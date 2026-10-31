"""
backend/database.py
--------------------
SQLite connection management and table creation for prediction history.

Design note: input_json stores the full customer input as one JSON blob
rather than 19 separate columns. This keeps the schema stable even if
FEATURE_COLUMNS in preprocessing.py ever changes, without needing a
database migration.
"""

import os
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "predictions.db")


def get_connection() -> sqlite3.Connection:
    """
    Opens a new SQLite connection. check_same_thread=False is required
    because FastAPI can serve requests from a thread pool, and each
    request here opens its own short-lived connection (safe pattern for
    SQLite — connections are not shared/held across requests).
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Creates the prediction_history table if it doesn't already exist.
    Safe to call every time the app starts — CREATE TABLE IF NOT EXISTS
    is a no-op if the table is already there, so existing data is never
    wiped on restart.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request_type TEXT NOT NULL,
                input_json TEXT NOT NULL,
                prediction TEXT NOT NULL,
                churn_probability REAL NOT NULL,
                risk_level TEXT NOT NULL,
                batch_id TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
