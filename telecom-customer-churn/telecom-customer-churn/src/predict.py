"""
predict.py
----------
Small helper module to load the saved churn model pipeline and make
predictions on new customer data. Used by app.py (Streamlit) so the
app file stays clean and focused on UI.
"""

import os
import joblib
import pandas as pd

from preprocessing import FEATURE_COLUMNS

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "churn_model.pkl")


def load_model(model_path: str = MODEL_PATH):
    """
    Loads the saved scikit-learn Pipeline (preprocessing + trained
    classifier bundled together, saved by train_model.py).
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No trained model found at '{model_path}'. "
            f"Run 'python src/train_model.py' from the project root first."
        )
    return joblib.load(model_path)


def predict_churn(model, input_dict: dict):
    """
    Takes a dictionary of raw customer feature values (same names/format
    as the original dataset columns, e.g. {'tenure': 5, 'gender': 'Female',
    'Contract': 'Month-to-month', ...}) and returns:

        (label:str, probability_of_churn:float)

    label is either "Churn" or "No Churn".
    probability_of_churn is a float between 0 and 1.

    The model pipeline internally applies the EXACT same preprocessing
    (scaling + one-hot encoding) that was used during training, so no
    manual encoding is needed here.
    """
    # Build a single-row DataFrame in the exact column order the model
    # was trained on.
    input_df = pd.DataFrame([input_dict], columns=FEATURE_COLUMNS)

    prediction = model.predict(input_df)[0]
    probability = model.predict_proba(input_df)[0][1]  # P(Churn = 1)

    label = "Churn" if prediction == 1 else "No Churn"
    return label, float(probability)


def predict_batch(model, df: pd.DataFrame) -> pd.DataFrame:
    """
    Runs predictions for MANY customers at once, using the exact same
    trained pipeline (preprocessing + model bundled together) as
    predict_churn() above — no separate/duplicate preprocessing logic.

    Takes a DataFrame that must contain all FEATURE_COLUMNS (extra
    columns like customerID are fine and pass through unchanged).

    Returns a new DataFrame = original data + 3 new columns:
        - 'Prediction'         ("Churn" / "No Churn")
        - 'Churn_Probability'  (0.0 - 1.0)
        - 'Risk_Level'         ("Low" / "Medium" / "High") using the SAME
          thresholds as the single-customer app (<0.30 / <0.60 / >=0.60)
    """
    missing_cols = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Uploaded file is missing required column(s): {missing_cols}. "
            f"Expected columns: {FEATURE_COLUMNS}"
        )

    X = df[FEATURE_COLUMNS].copy()

    predictions = model.predict(X)
    probabilities = model.predict_proba(X)[:, 1]

    def _risk_level(p):
        if p < 0.30:
            return "Low"
        elif p < 0.60:
            return "Medium"
        return "High"

    result_df = df.copy()
    result_df["Prediction"] = ["Churn" if p == 1 else "No Churn" for p in predictions]
    result_df["Churn_Probability"] = probabilities.round(4)
    result_df["Risk_Level"] = [_risk_level(p) for p in probabilities]

    return result_df
