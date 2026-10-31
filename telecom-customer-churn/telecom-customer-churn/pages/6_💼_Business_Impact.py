import requests
import pandas as pd
import streamlit as st


# --------------------------------
# Page configuration
# --------------------------------

st.set_page_config(
    page_title="Business Impact",
    page_icon="💼",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"


# --------------------------------
# Custom styling
# --------------------------------

st.markdown(
    """
    <style>
    .kpi-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 10px;
    }

    .kpi-title {
        font-size: 14px;
        opacity: 0.75;
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 700;
    }

    .impact-box {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --------------------------------
# Page title
# --------------------------------

st.title("💼 Business Impact Dashboard")

st.write(
    "Analyze customer churn predictions from a business perspective "
    "using prediction history."
)

st.divider()


# --------------------------------
# Fetch prediction history
# --------------------------------

def get_history(limit=100):
    try:
        response = requests.get(
            f"{API_URL}/history",
            params={"limit": limit},
            timeout=10
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            "❌ Could not connect to the backend API. "
            "Please make sure FastAPI is running."
        )
        return []

    except requests.exceptions.RequestException as e:
        st.error(
            f"❌ Failed to load prediction history: {e}"
        )
        return []


records = get_history()


if not records:
    st.info(
        "No prediction history available yet. "
        "Make some customer predictions first."
    )
    st.stop()


# --------------------------------
# Convert history to DataFrame
# --------------------------------

df = pd.DataFrame(records)


# --------------------------------
# Basic calculations
# --------------------------------

total_predictions = len(df)

churn_count = (
    df["prediction"] == "Churn"
).sum()

no_churn_count = (
    df["prediction"] == "No Churn"
).sum()

high_risk_count = (
    df["risk_level"] == "High"
).sum()

medium_risk_count = (
    df["risk_level"] == "Medium"
).sum()

low_risk_count = (
    df["risk_level"] == "Low"
).sum()

average_probability = (
    df["churn_probability"].mean() * 100
)


# --------------------------------
# Churn percentage
# --------------------------------

churn_percentage = (
    churn_count / total_predictions
) * 100


# --------------------------------
# Revenue-at-risk calculation
# --------------------------------

revenue_at_risk = 0.0

for _, row in df.iterrows():

    input_data = row.get("input_json")

    if isinstance(input_data, dict):

        monthly_charges = input_data.get(
            "MonthlyCharges",
            0
        )

        probability = row.get(
            "churn_probability",
            0
        )

        try:
            revenue_at_risk += (
                float(monthly_charges)
                * float(probability)
            )

        except (ValueError, TypeError):
            pass


# --------------------------------
# KPI section
# --------------------------------

st.subheader("📊 Business Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Predictions</div>
            <div class="kpi-value">{total_predictions}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Churn Predictions</div>
            <div class="kpi-value">{int(churn_count)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">High Risk Customers</div>
            <div class="kpi-value">{int(high_risk_count)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">Average Churn Risk</div>
            <div class="kpi-value">{average_probability:.1f}%</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------
# Revenue exposure
# --------------------------------

st.divider()

st.subheader("💰 Revenue Exposure")

st.markdown(
    f"""
    <div class="impact-box">
        <div class="kpi-title">
            Estimated Monthly Revenue at Risk
        </div>

        <div class="kpi-value">
            ${revenue_at_risk:,.2f}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "Estimated using Monthly Charges × Churn Probability. "
    "This represents potential revenue exposure, not guaranteed revenue loss."
)


# --------------------------------
# Risk distribution
# --------------------------------

st.divider()

st.subheader("🚦 Customer Risk Distribution")

risk_data = pd.DataFrame(
    {
        "Risk Level": [
            "Low",
            "Medium",
            "High"
        ],
        "Customers": [
            int(low_risk_count),
            int(medium_risk_count),
            int(high_risk_count)
        ]
    }
)

st.bar_chart(
    risk_data.set_index("Risk Level")
)


# --------------------------------
# Prediction distribution
# --------------------------------

st.divider()

st.subheader("🔄 Churn Prediction Distribution")

prediction_data = pd.DataFrame(
    {
        "Prediction": [
            "Churn",
            "No Churn"
        ],
        "Customers": [
            int(churn_count),
            int(no_churn_count)
        ]
    }
)

st.bar_chart(
    prediction_data.set_index("Prediction")
)


# --------------------------------
# Business interpretation
# --------------------------------

st.divider()

st.subheader("💡 Business Insights")

if high_risk_count > 0:

    st.warning(
        f"🔴 {int(high_risk_count)} customer(s) are currently "
        "classified as High Risk. These customers should be "
        "prioritized for retention activities."
    )

else:

    st.success(
        "🟢 No customers are currently classified as High Risk."
    )


if medium_risk_count > 0:

    st.info(
        f"🟡 {int(medium_risk_count)} customer(s) are in the "
        "Medium Risk category and may require monitoring."
    )


st.write(
    f"**Churn prediction rate:** {churn_percentage:.2f}% "
    f"of all recorded predictions are classified as Churn."
)


if average_probability >= 60:

    st.warning(
        "The average predicted churn probability is relatively high. "
        "The business should consider prioritizing customer retention."
    )

elif average_probability >= 30:

    st.info(
        "The average predicted churn probability is in the "
        "medium-risk range. Continued monitoring is recommended."
    )

else:

    st.success(
        "The average predicted churn probability is currently low."
    )


# --------------------------------
# Refresh button
# --------------------------------

st.divider()

if st.button(
    "🔄 Refresh Dashboard",
    use_container_width=True
):
    st.rerun()