"""
backend/main.py
----------------
FastAPI application exposing the existing churn model as a REST API.

Run from the project root with:
    uvicorn backend.main:app --reload

Or from inside the backend/ folder:
    uvicorn main:app --reload

Both work — see the sys.path handling below.

IMPORTANT: this file only IMPORTS load_model() and predict_churn() from
src/predict.py. It does not redefine, wrap, or alter their logic in any
way — the exact same function that powers the Streamlit app powers this
API, so results are guaranteed identical.
"""

import os
import sys
import io
import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------
# Path setup — works regardless of the current working directory or
# which of the two uvicorn invocations above is used.
# ---------------------------------------------------------------------
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

for path in (BACKEND_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from predict import load_model, predict_churn, predict_batch  # existing, UNCHANGED
from preprocessing import FEATURE_COLUMNS       # existing, UNCHANGED
from schemas import (
    CustomerInput,
    PredictionResponse,
    HealthResponse,
    BatchPredictionResponse,
    HistoryRecord,
)
from database import init_db
import crud
import json


app = FastAPI(
    title="Telecom Customer Churn Prediction API",
    description=(
        "REST API wrapping the existing trained churn model "
        "(same model and prediction logic used by the Streamlit app)."
    ),
    version="1.0.0",
)

# Permissive CORS for local development (e.g. calling from a future
# frontend on a different port). Not a production security posture —
# fine to tighten later, called out explicitly rather than left silent.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model is loaded ONCE at startup and reused across requests — loading
# a pickle on every request would be slow and pointless.
model_state = {"model": None, "load_error": None}


@app.on_event("startup")
def startup_event():
    # Fail loudly and early if the API schema ever drifts from the real
    # model's expected features, rather than silently mispredicting.
    schema_fields = set(CustomerInput.model_fields.keys())
    expected_fields = set(FEATURE_COLUMNS)
    if schema_fields != expected_fields:
        missing = expected_fields - schema_fields
        extra = schema_fields - expected_fields
        raise RuntimeError(
            f"CustomerInput schema does not match FEATURE_COLUMNS. "
            f"Missing: {missing}, Extra: {extra}"
        )

    try:
        model_state["model"] = load_model()
    except Exception as e:
        # Don't crash the whole app — /health should be able to report
        # "model not loaded" instead of the server failing to start.
        model_state["load_error"] = str(e)

    init_db()


def get_model_or_503():
    if model_state["model"] is None:
        raise HTTPException(
            status_code=503,
            detail=f"Model is not loaded: {model_state['load_error']}",
        )
    return model_state["model"]


# =======================================================================
# GET /health
# =======================================================================
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    db_ok = True
    try:
        crud.count_predictions()
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if model_state["model"] is not None and db_ok else "degraded",
        model_loaded=model_state["model"] is not None,
        database_connected=db_ok,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# =======================================================================
# POST /predict
# =======================================================================
@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
def predict(customer: CustomerInput):
    model = get_model_or_503()

    input_dict = customer.model_dump()

    # This is the EXACT same function call app.py makes — same code path,
    # same result, guaranteed no drift between the API and the UI.
    try:
        label, probability = predict_churn(model, input_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    risk_level = crud.get_risk_level(probability)

    record_id = crud.insert_prediction(
        request_type="single",
        input_data=input_dict,
        prediction=label,
        churn_probability=probability,
        risk_level=risk_level,
    )

    record = crud.get_prediction_by_id(record_id)

    return PredictionResponse(
        id=record_id,
        prediction=label,
        churn_probability=probability,
        risk_level=risk_level,
        timestamp=record["timestamp"],
    )


# =======================================================================
# POST /predict/batch  (Stage 2)
# =======================================================================
@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"])
def predict_batch_endpoint(file: UploadFile = File(...)):
    model = get_model_or_503()

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    try:
        contents = file.file.read()
        input_df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read CSV file: {e}")

    if input_df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV has no rows.")

    # Same TotalCharges cleaning rule already used by pages/1_Batch_Prediction.py
    # (raw Telco data stores it as text with blanks for brand-new customers).
    # Reusing the SAME rule here, not a different/second preprocessing pipeline.
    if "TotalCharges" in input_df.columns and input_df["TotalCharges"].dtype == object:
        input_df["TotalCharges"] = (
            input_df["TotalCharges"].astype(str).str.strip().replace("", "0")
        )
        input_df["TotalCharges"] = pd.to_numeric(input_df["TotalCharges"], errors="coerce").fillna(0)

    # This is the EXACT same function the Streamlit batch page calls —
    # same code path, same validation, same result.
    try:
        results_df = predict_batch(model, input_df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

    batch_id = str(uuid.uuid4())
    records = results_df.to_dict(orient="records")

    for record in records:
        input_data = {col: record[col] for col in FEATURE_COLUMNS if col in record}
        crud.insert_prediction(
            request_type="batch",
            input_data=input_data,
            prediction=record["Prediction"],
            churn_probability=float(record["Churn_Probability"]),
            risk_level=record["Risk_Level"],
            batch_id=batch_id,
        )

    churn_count = sum(1 for r in records if r["Prediction"] == "Churn")

    return BatchPredictionResponse(
        batch_id=batch_id,
        total_records=len(records),
        churn_count=churn_count,
        no_churn_count=len(records) - churn_count,
        results=records,
    )


# =======================================================================
# GET /history  (Stage 2)
# =======================================================================
@app.get("/history", response_model=list[HistoryRecord], tags=["History"])
def get_history(limit: int = 50):
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500.")

    rows = crud.get_recent_predictions(limit=limit)
    return [
        HistoryRecord(
            id=row["id"],
            timestamp=row["timestamp"],
            request_type=row["request_type"],
            input=json.loads(row["input_json"]),
            prediction=row["prediction"],
            churn_probability=row["churn_probability"],
            risk_level=row["risk_level"],
            batch_id=row["batch_id"],
        )
        for row in rows
    ]


# =======================================================================
# GET /history/{id}  (Stage 2)
# =======================================================================
@app.get("/history/{record_id}", response_model=HistoryRecord, tags=["History"])
def get_history_by_id(record_id: int):
    row = crud.get_prediction_by_id(record_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"No prediction found with id={record_id}")

    return HistoryRecord(
        id=row["id"],
        timestamp=row["timestamp"],
        request_type=row["request_type"],
        input=json.loads(row["input_json"]),
        prediction=row["prediction"],
        churn_probability=row["churn_probability"],
        risk_level=row["risk_level"],
        batch_id=row["batch_id"],
    )
