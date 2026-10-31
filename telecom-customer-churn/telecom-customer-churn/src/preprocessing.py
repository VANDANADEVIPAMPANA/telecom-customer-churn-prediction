"""
preprocessing.py
-----------------
All data loading, cleaning, and preprocessing-pipeline logic for the
Telecom Customer Churn Prediction project.

This file is imported by BOTH train_model.py (during training) and
app.py (during live prediction) so that the exact same preprocessing
is applied every time. This avoids train/serve mismatch.
"""

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# ---------------------------------------------------------------------
# 1. Column definitions (based on actual inspection of the dataset)
# ---------------------------------------------------------------------
# Target column
TARGET_COLUMN = "Churn"

# Column that is just an ID -> not useful for prediction, must be dropped
ID_COLUMN = "customerID"

# Numerical features (true continuous / count numbers)
NUMERICAL_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]

# Categorical features (everything else that is not numeric, id, or target)
CATEGORICAL_FEATURES = [
    "gender",
    "SeniorCitizen",      # stored as 0/1 in the raw data, but it is really
                           # a category (Yes/No), so we treat it as categorical
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

# Final list of feature columns the model actually uses (order matters for
# app.py, so we keep one single source of truth here)
FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


# ---------------------------------------------------------------------
# 2. Load + clean the raw CSV
# ---------------------------------------------------------------------
def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """
    Loads the raw Telco Customer Churn CSV and applies the cleaning steps
    found necessary during inspection of the real data:

      - TotalCharges is stored as text and has 11 blank rows (all customers
        with tenure == 0, i.e. brand new customers who have not been billed
        yet). We convert it to numeric and fill those blanks with 0.
      - customerID is dropped (pure identifier, not predictive).
      - Churn (target) is mapped from Yes/No to 1/0.

    Returns a cleaned DataFrame ready to be split into X and y.
    """
    df = pd.read_csv(csv_path)

    # --- Fix TotalCharges: text -> numeric, blanks -> 0 ---
    df["TotalCharges"] = df["TotalCharges"].astype(str).str.strip()
    df["TotalCharges"] = df["TotalCharges"].replace("", "0")
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df["TotalCharges"] = df["TotalCharges"].fillna(0)

    # --- Drop the ID column (not predictive, would just add noise) ---
    if ID_COLUMN in df.columns:
        df = df.drop(columns=[ID_COLUMN])

    # --- Encode target: Yes -> 1 (Churn), No -> 0 (No Churn) ---
    df[TARGET_COLUMN] = df[TARGET_COLUMN].map({"Yes": 1, "No": 0})

    # Drop exact duplicate rows if any slipped in (inspection showed 0,
    # but we keep this as a safety net for future data refreshes)
    df = df.drop_duplicates()

    return df


def split_features_target(df: pd.DataFrame):
    """Splits a cleaned DataFrame into X (features) and y (target)."""
    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()
    return X, y


# ---------------------------------------------------------------------
# 3. Build the preprocessing pipeline (ColumnTransformer)
# ---------------------------------------------------------------------
def build_preprocessor() -> ColumnTransformer:
    """
    Builds a ColumnTransformer that:
      - Scales numerical features with StandardScaler
        (helps Logistic Regression converge properly; harmless for
        tree-based models).
      - One-hot encodes categorical features.
        handle_unknown="ignore" so that if the Streamlit app ever sends
        a category value not seen during training, it won't crash.

    This SAME object is fitted inside the model pipeline during training,
    and the exact fitted version is saved to disk and reused in app.py.
    So training and prediction preprocessing are guaranteed identical.
    """
    numerical_transformer = StandardScaler()
    categorical_transformer = OneHotEncoder(handle_unknown="ignore")

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numerical_transformer, NUMERICAL_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )
    return preprocessor
