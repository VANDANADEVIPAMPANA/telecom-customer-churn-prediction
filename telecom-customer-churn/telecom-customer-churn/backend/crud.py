"""
backend/crud.py
----------------
Insert/query functions for the prediction_history table, plus the
shared risk-level helper.

Risk thresholds below (<0.30 Low, <0.60 Medium, >=0.60 High) intentionally
mirror the exact same thresholds already used in src/predict.py's
predict_batch() and in app.py. They are re-declared here (rather than
imported) specifically so that Stage 1 does NOT modify predict.py at all,
per the requirement to leave predict_churn()/load_model() untouched.
If predict.py is ever refactored to export this helper, this can be
pointed at that instead.
"""

import json
import os
import sys
import sqlite3
from datetime import datetime, timezone

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from database import get_connection


def get_risk_level(probability: float) -> str:
    """Same thresholds as predict_batch() in src/predict.py and app.py."""
    if probability < 0.30:
        return "Low"
    elif probability < 0.60:
        return "Medium"
    return "High"


def insert_prediction(
    request_type: str,
    input_data: dict,
    prediction: str,
    churn_probability: float,
    risk_level: str,
    batch_id: str = None,
) -> int:
    """
    Inserts one prediction record and returns its new row id.
    request_type is "single" or "batch".
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO prediction_history
                (timestamp, request_type, input_json, prediction,
                 churn_probability, risk_level, batch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                request_type,
                json.dumps(input_data),
                prediction,
                churn_probability,
                risk_level,
                batch_id,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_prediction_by_id(record_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM prediction_history WHERE id = ?", (record_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_recent_predictions(limit: int = 50):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM prediction_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_predictions() -> int:
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as c FROM prediction_history").fetchone()
        return row["c"]
    finally:
        conn.close()
