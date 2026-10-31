"""
backend/schemas.py
-------------------
Pydantic request/response models for the API.

CustomerInput's fields are deliberately a 1:1 match with
src/preprocessing.py's FEATURE_COLUMNS (NUMERICAL_FEATURES +
CATEGORICAL_FEATURES) — same names, same set, nothing added or removed.
This is checked at runtime in main.py's startup (see startup_event) so
that if preprocessing.py ever changes, the mismatch is caught immediately
with a clear error instead of silently producing wrong predictions.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomerInput(BaseModel):
    # Numerical features
    tenure: int = Field(..., ge=0, le=100, description="Months with the company")
    MonthlyCharges: float = Field(..., ge=0, description="Current monthly bill amount")
    TotalCharges: float = Field(..., ge=0, description="Total amount billed so far")

    # Categorical features (same 16 as preprocessing.CATEGORICAL_FEATURES)
    gender: str
    SeniorCitizen: int = Field(..., ge=0, le=1, description="0 = No, 1 = Yes")
    Partner: str
    Dependents: str
    PhoneService: str
    MultipleLines: str
    InternetService: str
    OnlineSecurity: str
    OnlineBackup: str
    DeviceProtection: str
    TechSupport: str
    StreamingTV: str
    StreamingMovies: str
    Contract: str
    PaperlessBilling: str
    PaymentMethod: str

    class Config:
        json_schema_extra = {
            "example": {
                "tenure": 2,
                "MonthlyCharges": 85.0,
                "TotalCharges": 170.0,
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "No",
                "Dependents": "No",
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No",
                "OnlineBackup": "No",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "Yes",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
            }
        }


class PredictionResponse(BaseModel):
    id: int
    prediction: str
    churn_probability: float
    risk_level: str
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    database_connected: bool
    timestamp: str


# =======================================================================
# Stage 2: Batch prediction + history schemas
# =======================================================================

class BatchPredictionResponse(BaseModel):
    """
    Response for POST /predict/batch. `results` deliberately uses
    Dict[str, Any] rather than a strict per-column model — uploaded CSVs
    may contain extra columns (e.g. customerID) beyond FEATURE_COLUMNS,
    and predict_batch() already handles/validates the required ones.
    Each dict = one input row's original columns + Prediction,
    Churn_Probability, Risk_Level (exactly what predict_batch() returns).
    """
    batch_id: str
    total_records: int
    churn_count: int
    no_churn_count: int
    results: List[Dict[str, Any]]


class HistoryRecord(BaseModel):
    """One row from the prediction_history table. `input` is the parsed
    form of the stored input_json column (parsed in main.py, not crud.py,
    so crud.py's existing return shape is untouched)."""
    id: int
    timestamp: str
    request_type: str
    input: Dict[str, Any]
    prediction: str
    churn_probability: float
    risk_level: str
    batch_id: Optional[str] = None
