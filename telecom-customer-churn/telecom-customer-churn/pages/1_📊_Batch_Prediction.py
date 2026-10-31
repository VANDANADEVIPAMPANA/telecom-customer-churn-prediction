"""
pages/1_📊_Batch_Prediction.py
-------------------------------
Stage 5: Upload a CSV of many customers and get churn predictions for
all of them, using the SAME trained pipeline as the single-customer
Home page (via predict_batch() in src/predict.py — no separate
preprocessing logic).

Stage 6: Also shows aggregate estimated revenue-at-risk for the batch.
"""

import sys
import os
import streamlit as st
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from predict import load_model, predict_batch  # noqa: E402
from preprocessing import FEATURE_COLUMNS  # noqa: E402

st.set_page_config(page_title="Batch Prediction", page_icon="📊", layout="wide")

# Minimal shared look (kept intentionally simple/self-contained per page,
# matching the existing project's approach of one CSS block per file)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #F6F8FB; }
    .block-container { max-width: 1180px; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .page-header {
        background: linear-gradient(135deg, #0B1730 0%, #12213D 60%, #17285A 100%);
        margin: 0 -100vw; padding: 40px 100vw 44px 100vw; margin-bottom: 32px;
        border-bottom: 1px solid #1E2E52;
    }
    .page-header-inner { max-width: 1180px; margin: 0 auto; }
    .page-header h1 { color: #FFFFFF; font-size: 30px; font-weight: 800; margin: 0 0 8px 0; }
    .page-header p { color: #9AA8C7; font-size: 14.5px; margin: 0; }
    .info-card {
        background: #FFFFFF; border: 1px solid #E3E8F0; border-radius: 12px;
        padding: 16px 18px; min-height: 88px;
    }
    .info-card .card-label { color: #7A88A3; font-size: 12.5px; margin-bottom: 6px; font-weight: 500; }
    .info-card .card-value { color: #0B1730; font-size: 20px; font-weight: 700; font-family: 'Plus Jakarta Sans', sans-serif; }
    .surface-card { background: #FFFFFF; border: 1px solid #E3E8F0; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-header"><div class="page-header-inner">
        <h1>📊 Batch Churn Prediction</h1>
        <p>Upload a CSV of multiple customers to get predictions, risk levels, and revenue exposure for all of them at once.</p>
    </div></div>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_model():
    return load_model()


try:
    model = get_model()
except Exception as e:
    st.error(f"Could not load the trained model: {e}")
    st.stop()

st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("**Required columns**")
st.caption(
    "customerID is optional. Extra columns are fine and pass through unchanged."
)
st.code(", ".join(FEATURE_COLUMNS), language="text")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

sample_path = os.path.join(PROJECT_ROOT, "dataset", "Telco-Customer-Churn.csv")
if os.path.exists(sample_path):
    sample_df = pd.read_csv(sample_path).head(20)
    st.download_button(
        "⬇️ Download a sample CSV (20 real customers, for testing)",
        data=sample_df.to_csv(index=False),
        file_name="sample_customers.csv",
        mime="text/csv",
    )
st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file is not None:
    try:
        input_df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the uploaded file — please check it's a valid CSV. ({e})")
        st.stop()

    if input_df.empty:
        st.error("The uploaded file has no rows.")
        st.stop()

    # Same TotalCharges cleaning rule used during training (raw Telco data
    # stores it as text with blanks for brand-new customers) — reusing the
    # SAME rule, not a different one, so uploads of the raw dataset work.
    if "TotalCharges" in input_df.columns and input_df["TotalCharges"].dtype == object:
        input_df["TotalCharges"] = (
            input_df["TotalCharges"].astype(str).str.strip().replace("", "0")
        )
        input_df["TotalCharges"] = pd.to_numeric(input_df["TotalCharges"], errors="coerce").fillna(0)

    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    st.markdown("**Preview (first 10 rows)**")
    st.dataframe(input_df.head(10), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔮 Run Predictions on All Rows", type="primary", use_container_width=True):
        try:
            results = predict_batch(model, input_df)
        except ValueError as e:
            st.error(f"⚠️ {e}")
            st.stop()
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            st.stop()

        # Stage 6: aggregate estimated revenue at risk
        if "MonthlyCharges" in results.columns:
            results["Estimated_Revenue_At_Risk"] = (
                results["MonthlyCharges"] * results["Churn_Probability"]
            ).round(2)
            total_revenue_at_risk = results["Estimated_Revenue_At_Risk"].sum()
        else:
            total_revenue_at_risk = None

        total = len(results)
        churn_count = (results["Prediction"] == "Churn").sum()
        churn_rate = churn_count / total * 100 if total else 0
        high_risk_count = (results["Risk_Level"] == "High").sum()

        st.markdown("### 📈 Batch Summary")
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f'<div class="info-card"><div class="card-label">Total Customers</div><div class="card-value">{total}</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="info-card"><div class="card-label">Predicted Churn</div><div class="card-value">{churn_count} ({churn_rate:.1f}%)</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="info-card"><div class="card-label">High Risk Customers</div><div class="card-value">{high_risk_count}</div></div>', unsafe_allow_html=True)
        with s4:
            rev_display = f"${total_revenue_at_risk:,.2f}" if total_revenue_at_risk is not None else "N/A"
            st.markdown(f'<div class="info-card"><div class="card-label">Est. Monthly Revenue at Risk</div><div class="card-value">{rev_display}</div></div>', unsafe_allow_html=True)

        if total_revenue_at_risk is not None:
            st.caption(
                "⚠️ 'Estimated Revenue at Risk' = Σ (Monthly Charges × Churn Probability) across "
                "all customers. This is a **risk-weighted estimate**, not actual or guaranteed lost revenue."
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 Full Results")

        def highlight_risk(row):
            if row["Risk_Level"] == "High":
                return ["background-color: rgba(220, 38, 38, 0.08)"] * len(row)
            elif row["Risk_Level"] == "Medium":
                return ["background-color: rgba(217, 119, 6, 0.08)"] * len(row)
            return [""] * len(row)

        st.dataframe(results.style.apply(highlight_risk, axis=1), use_container_width=True)

        st.download_button(
            "⬇️ Download Predictions as CSV",
            data=results.to_csv(index=False),
            file_name="churn_predictions.csv",
            mime="text/csv",
            use_container_width=True,
        )
