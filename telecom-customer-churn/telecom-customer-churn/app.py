import sys
import os
import math
import requests
import streamlit as st

# =========================================================
# Allow imports from src/
# =========================================================

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# =========================================================
# Page Configuration
# =========================================================

st.set_page_config(
    page_title="Telecom Churn Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# Custom CSS - Professional, Razorpay-inspired fintech UI
# Design tokens:
#   Navy   #0B1730 / #12213D   (hero + footer)
#   Page   #F6F8FB             (light neutral background)
#   Surface#FFFFFF             (cards)
#   Border #E3E8F0
#   Accent #3358F4  /  #6C8CFF (indigo, primary brand color)
#   Text   #0B1730 (primary)  /  #5B6B85 (secondary)
#   Risk   Low #16A34A  Medium #D97706  High #DC2626
# =========================================================

st.markdown(
    """
    <style>

    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }

    h1, h2, h3, .jakarta {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Page background */
    .stApp {
        background: #F6F8FB;
    }

    .block-container {
        padding-top: 0rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }

    /* =========================================================
       HERO
       ========================================================= */
    .hero-band {
        background: linear-gradient(135deg, #0B1730 0%, #12213D 60%, #17285A 100%);
        margin: 0 -100vw;
        padding: 56px 100vw 64px 100vw;
        margin-bottom: 40px;
        border-bottom: 1px solid #1E2E52;
    }

    .hero-inner {
        max-width: 1180px;
        margin: 0 auto;
    }

    .eyebrow-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(108, 140, 255, 0.12);
        border: 1px solid rgba(108, 140, 255, 0.35);
        color: #A9BBFF;
        font-size: 13px;
        font-weight: 600;
        padding: 6px 14px;
        border-radius: 999px;
        margin-bottom: 20px;
    }

    .hero-title {
        color: #FFFFFF;
        font-size: 42px;
        font-weight: 800;
        line-height: 1.15;
        margin: 0 0 14px 0;
        letter-spacing: -0.02em;
    }

    .hero-subtitle {
        color: #9AA8C7;
        font-size: 16px;
        line-height: 1.6;
        max-width: 560px;
        margin-bottom: 28px;
    }

    .stat-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }

    .stat-pill {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 12px;
        padding: 12px 18px;
        min-width: 150px;
    }

    .stat-pill .stat-value {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stat-pill .stat-label {
        color: #7E8CB0;
        font-size: 12px;
        margin-top: 2px;
    }

    /* =========================================================
       SECTIONS / CARDS
       ========================================================= */
    .section-eyebrow {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }

    .section-eyebrow .icon-box {
        width: 34px;
        height: 34px;
        border-radius: 9px;
        background: #EAEEFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
    }

    .section-eyebrow .title {
        color: #0B1730;
        font-size: 19px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .section-desc {
        color: #7A88A3;
        font-size: 13.5px;
        margin: 6px 0 18px 44px;
    }

    .surface-card {
        background: #FFFFFF;
        border: 1px solid #E3E8F0;
        border-radius: 16px;
        padding: 28px 28px 8px 28px;
        margin-bottom: 28px;
        box-shadow: 0 1px 2px rgba(11, 23, 48, 0.04);
    }

    .info-card {
        background: #F8FAFD;
        border: 1px solid #E3E8F0;
        border-radius: 12px;
        padding: 16px 18px;
        min-height: 88px;
    }

    .info-card .card-label {
        color: #7A88A3;
        font-size: 12.5px;
        margin-bottom: 6px;
        font-weight: 500;
    }

    .info-card .card-value {
        color: #0B1730;
        font-size: 20px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* =========================================================
       STREAMLIT WIDGET OVERRIDES (light theme)
       ========================================================= */
    [data-testid="stWidgetLabel"] p {
        color: #3D4A63 !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
    }

    div[data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border: 1.5px solid #E3E8F0 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] > div:hover {
        border-color: #3358F4 !important;
    }

    .stNumberInput input {
        background: #FFFFFF !important;
        border: 1.5px solid #E3E8F0 !important;
        border-radius: 10px !important;
        color: #0B1730 !important;
    }

    .stNumberInput input:focus {
        border-color: #3358F4 !important;
        box-shadow: 0 0 0 3px rgba(51, 88, 244, 0.12) !important;
    }

    /* Predict button */
    div.stButton > button {
        width: 100%;
        height: 54px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: linear-gradient(135deg, #3358F4 0%, #4A6CFF 100%);
        border: none;
        color: #FFFFFF;
        box-shadow: 0 4px 14px rgba(51, 88, 244, 0.30);
        transition: all 0.15s ease;
    }

    div.stButton > button:hover {
        box-shadow: 0 6px 20px rgba(51, 88, 244, 0.40);
        transform: translateY(-1px);
    }

    /* =========================================================
       RESULT PANEL + GAUGE
       ========================================================= */
    .result-panel {
        background: #FFFFFF;
        border: 1px solid #E3E8F0;
        border-radius: 20px;
        padding: 32px;
        margin-top: 28px;
        box-shadow: 0 4px 24px rgba(11, 23, 48, 0.06);
    }

    .result-title {
        color: #0B1730;
        font-size: 21px;
        font-weight: 700;
        font-family: 'Plus Jakarta Sans', sans-serif;
        margin-bottom: 22px;
    }

    .risk-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 16px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }

    .risk-pill.low { background: #E8F8EE; color: #16A34A; }
    .risk-pill.medium { background: #FEF3E2; color: #D97706; }
    .risk-pill.high { background: #FDEAEA; color: #DC2626; }

    .risk-desc {
        color: #5B6B85;
        font-size: 14.5px;
        line-height: 1.6;
        margin-top: 14px;
    }

    .recommendation-box {
        background: #F6F8FE;
        border-left: 3px solid #3358F4;
        border-radius: 10px;
        padding: 16px 18px;
        margin-top: 18px;
    }

    .recommendation-box .rec-title {
        color: #0B1730;
        font-weight: 700;
        font-size: 14.5px;
        margin-bottom: 5px;
    }

    .recommendation-box .rec-text {
        color: #5B6B85;
        font-size: 13.5px;
        line-height: 1.5;
    }

    .factors-label {
        color: #7A88A3;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-top: 16px;
        margin-bottom: 8px;
    }

    .factor-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .factor-chip {
        background: #FDEAEA;
        color: #B91C1C;
        font-size: 12.5px;
        font-weight: 500;
        padding: 5px 12px;
        border-radius: 999px;
        border: 1px solid #F5C6C6;
    }

    .revenue-box {
        background: #F0FBF4;
        border-left: 3px solid #16A34A;
        border-radius: 10px;
        padding: 16px 18px;
        margin-top: 14px;
    }

    .revenue-value {
        color: #0B1730;
        font-size: 22px;
        font-weight: 800;
        font-family: 'Plus Jakarta Sans', sans-serif;
        margin: 4px 0;
    }

    .revenue-note {
        color: #5B6B85;
        font-size: 12px;
        line-height: 1.5;
    }

    /* Footer */
    .app-footer {
        text-align: center;
        color: #9AA5BD;
        font-size: 12.5px;
        padding: 30px 0 10px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Helper: SVG risk gauge (signature visual element)
# =========================================================

def render_gauge(probability, risk_color_hex):
    """
    Renders a circular ring gauge with the churn probability centered
    inside — the app's signature visual (replaces a plain progress bar).
    Pure SVG + inline CSS, no extra dependency.
    """
    radius = 70
    stroke = 14
    circumference = 2 * math.pi * radius
    offset = circumference * (1 - probability)

    svg = f"""
    <div style="display:flex; justify-content:center; align-items:center; padding: 10px 0 18px 0;">
        <svg width="180" height="180" viewBox="0 0 180 180">
            <circle cx="90" cy="90" r="{radius}" fill="none"
                    stroke="#EEF1F8" stroke-width="{stroke}" />
            <circle cx="90" cy="90" r="{radius}" fill="none"
                    stroke="{risk_color_hex}" stroke-width="{stroke}"
                    stroke-linecap="round"
                    stroke-dasharray="{circumference:.2f}"
                    stroke-dashoffset="{offset:.2f}"
                    transform="rotate(-90 90 90)" />
            <text x="90" y="82" text-anchor="middle"
                  font-family="Plus Jakarta Sans, sans-serif" font-weight="800"
                  font-size="30" fill="#0B1730">{probability*100:.1f}%</text>
            <text x="90" y="104" text-anchor="middle"
                  font-family="Inter, sans-serif" font-size="11.5" fill="#7A88A3">
                  churn probability</text>
        </svg>
    </div>
    """
    st.markdown(svg, unsafe_allow_html=True)


def info_card(label, value):
    st.markdown(
        f"""
        <div class="info-card">
            <div class="card-label">{label}</div>
            <div class="card-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def section_header(icon, title, description):
    st.markdown(
        f"""
        <div class="section-eyebrow">
            <div class="icon-box">{icon}</div>
            <div class="title">{title}</div>
        </div>
        <div class="section-desc">{description}</div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# Stage 2: Rule-based risk factors + retention recommendation
# =========================================================
# IMPORTANT: this is a RULE-BASED heuristic layer, not a model explanation.
# It flags input values that are well-known churn correlates in this
# dataset (confirmed via the model's own coefficients in train_model.py's
# feature-importance output). It does NOT claim these specific values
# caused THIS prediction — that distinction is handled separately by the
# genuine model-based explanation on the Explainability page (Stage 4).

def get_risk_factors(data: dict) -> list:
    """Flags common churn-correlated attributes present in this customer's
    input. Purely rule-based — used only to make the recommendation text
    more specific, not as a claim of causal model attribution."""
    factors = []
    if data["Contract"] == "Month-to-month":
        factors.append("Month-to-month contract (no long-term commitment)")
    if data["tenure"] <= 12:
        factors.append(f"Short tenure ({data['tenure']} months)")
    if data["MonthlyCharges"] >= 80:
        factors.append(f"High monthly charges (${data['MonthlyCharges']:.2f})")
    if data["InternetService"] == "Fiber optic":
        factors.append("Fiber optic internet service")
    if data["PaymentMethod"] == "Electronic check":
        factors.append("Electronic check payment method")
    if data["OnlineSecurity"] == "No" and data["InternetService"] != "No":
        factors.append("No online security add-on")
    if data["TechSupport"] == "No" and data["InternetService"] != "No":
        factors.append("No tech support add-on")
    return factors


def build_recommendation(risk_level: str, factors: list) -> str:
    """Builds a recommendation string that references the top 1-2 detected
    factors when available, falling back to a generic template otherwise.
    Thresholds/labels passed in are the SAME existing Low/Medium/High
    buckets already used elsewhere in this file — not redefined here."""
    factor_snippet = ""
    if factors:
        top = factors[:2]
        factor_snippet = " Notably: " + " and ".join(top) + "."

    if risk_level == "LOW RISK":
        return (
            "Continue providing a good customer experience. Regular "
            "engagement and service quality monitoring can help maintain "
            "customer loyalty." + factor_snippet
        )
    elif risk_level == "MEDIUM RISK":
        return (
            "Consider proactive customer engagement, service reviews, and "
            "suitable offers to improve customer satisfaction." + factor_snippet
        )
    else:
        return (
            "Consider proactive retention strategies such as personalized "
            "offers, contract upgrade incentives, or customer support "
            "follow-up." + factor_snippet
        )


# =========================================================
# Backend API Connection
# =========================================================
# Single-customer prediction now goes through the FastAPI backend's
# POST /predict endpoint instead of calling load_model()/predict_churn()
# directly in-process. The backend itself still calls the exact same,
# unmodified predict_churn() — this only changes WHERE that call happens.

API_BASE_URL = os.getenv("CHURN_API_URL", "http://127.0.0.1:8000")


def call_predict_api(input_data: dict):
    """
    Calls POST /predict on the FastAPI backend with this customer's data
    and returns (label, probability) — the same tuple shape predict_churn()
    used to return, so nothing downstream (risk bucketing, risk factors,
    recommendation, revenue-at-risk, the gauge) needs to change.
    """
    try:
        response = requests.post(f"{API_BASE_URL}/predict", json=input_data, timeout=10)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not connect to the backend API at {API_BASE_URL}. "
            f"Make sure it's running: uvicorn backend.main:app --reload"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The backend API took too long to respond.")

    if response.status_code != 200:
        raise RuntimeError(f"API returned an error ({response.status_code}): {response.text}")

    data = response.json()
    return data["prediction"], data["churn_probability"]


# Fail fast if the backend isn't reachable, same as the old load_model()
# guard did for the local model — before rendering any of the form below.
try:
    health = requests.get(f"{API_BASE_URL}/health", timeout=5)
    health_data = health.json()
    if health.status_code != 200 or not health_data.get("model_loaded", False):
        st.error(f"Backend API is reachable but not healthy: {health_data}")
        st.stop()
except requests.exceptions.ConnectionError:
    st.error(
        f"Could not connect to the backend API at {API_BASE_URL}. "
        f"Start it with: uvicorn backend.main:app --reload"
    )
    st.stop()
except requests.exceptions.Timeout:
    st.error("Backend API health check timed out.")
    st.stop()

# Real, verified stats for the hero trust badges (not invented numbers)
MODEL_ROC_AUC = "84.0%"
TRAINING_SIZE = "7,021"


# =========================================================
# Hero
# =========================================================

st.markdown(
    f"""
    <div class="hero-band">
        <div class="hero-inner">
            <div class="eyebrow-pill">🤖 &nbsp; AI-Powered Risk Engine</div>
            <div class="hero-title">Predict customer churn<br>before it happens.</div>
            <div class="hero-subtitle">
                Enter a customer's profile and service details to get an instant,
                data-driven churn risk score — trained on real telecom subscriber data.
            </div>
            <div class="stat-row">
                <div class="stat-pill">
                    <div class="stat-value">{MODEL_ROC_AUC}</div>
                    <div class="stat-label">Model ROC-AUC</div>
                </div>
                <div class="stat-pill">
                    <div class="stat-value">{TRAINING_SIZE}</div>
                    <div class="stat-label">Customers analyzed</div>
                </div>
                <div class="stat-pill">
                    <div class="stat-value">Real-time</div>
                    <div class="stat-label">Instant prediction</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# Customer Information
# =========================================================

with st.container():
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    section_header("👤", "Customer Information", "Basic profile and account details.")

    col1, col2 = st.columns(2)

    with col1:
        gender = st.selectbox("Gender", ["Female", "Male"])
        senior_citizen = st.selectbox(
            "Senior Citizen",
            [0, 1],
            format_func=lambda x: "Yes" if x == 1 else "No"
        )
        partner = st.selectbox("Partner", ["Yes", "No"])
        dependents = st.selectbox("Dependents", ["Yes", "No"])
        tenure = st.number_input("Tenure (months)", min_value=0, max_value=100, value=12)
        phone_service = st.selectbox("Phone Service", ["Yes", "No"])
        multiple_lines = st.selectbox("Multiple Lines", ["Yes", "No", "No phone service"])

    with col2:
        internet_service = st.selectbox("Internet Service", ["DSL", "Fiber optic", "No"])
        online_security = st.selectbox("Online Security", ["Yes", "No", "No internet service"])
        online_backup = st.selectbox("Online Backup", ["Yes", "No", "No internet service"])
        device_protection = st.selectbox("Device Protection", ["Yes", "No", "No internet service"])
        tech_support = st.selectbox("Tech Support", ["Yes", "No", "No internet service"])
        streaming_tv = st.selectbox("Streaming TV", ["Yes", "No", "No internet service"])
        streaming_movies = st.selectbox("Streaming Movies", ["Yes", "No", "No internet service"])

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# Contract & Billing
# =========================================================

with st.container():
    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    section_header("💳", "Contract & Billing", "Payment method and contract terms.")

    col3, col4 = st.columns(2)

    with col3:
        contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
        paperless_billing = st.selectbox("Paperless Billing", ["Yes", "No"])
        payment_method = st.selectbox(
            "Payment Method",
            [
                "Electronic check",
                "Mailed check",
                "Bank transfer (automatic)",
                "Credit card (automatic)"
            ]
        )

    with col4:
        monthly_charges = st.number_input(
            "Monthly Charges",
            min_value=0.0,
            value=70.0,
            step=1.0
        )
        total_charges = tenure * monthly_charges
        st.markdown("<br>", unsafe_allow_html=True)
        info_card("Estimated Total Charges", f"${total_charges:,.2f}")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# Customer Summary
# =========================================================

st.markdown('<div style="margin-bottom: 14px;">', unsafe_allow_html=True)
section_header("📊", "Customer Summary", "Quick overview of the entered profile.")
st.markdown('</div>', unsafe_allow_html=True)

summary1, summary2, summary3, summary4 = st.columns(4)
with summary1:
    info_card("Tenure", f"{tenure} months")
with summary2:
    info_card("Monthly Charges", f"${monthly_charges:,.2f}")
with summary3:
    info_card("Contract", contract)
with summary4:
    info_card("Total Charges", f"${total_charges:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# Predict Button
# =========================================================

predict_button = st.button(
    "🔍  Predict Customer Churn",
    type="primary",
    use_container_width=True
)


# =========================================================
# Prediction
# =========================================================

if predict_button:

    input_data = {
        "gender": gender,
        "SeniorCitizen": senior_citizen,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": tenure,
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless_billing,
        "PaymentMethod": payment_method,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges
    }

    try:

        label, probability = call_predict_api(input_data)

        probability_percent = probability * 100

        # =================================================
        # Risk Classification (unchanged thresholds/logic)
        # =================================================

        if probability < 0.30:
            risk_level = "LOW RISK"
            risk_class = "low"
            risk_color = "#16A34A"
            description = (
                "This customer has a relatively low probability "
                "of leaving the telecom service."
            )

        elif probability < 0.60:
            risk_level = "MEDIUM RISK"
            risk_class = "medium"
            risk_color = "#D97706"
            description = (
                "This customer shows a moderate probability "
                "of leaving the telecom service."
            )

        else:
            risk_level = "HIGH RISK"
            risk_class = "high"
            risk_color = "#DC2626"
            description = (
                "This customer has a relatively high probability "
                "of leaving the telecom service."
            )

        # Stage 2: rule-based risk factors + factor-aware recommendation
        risk_factors = get_risk_factors(input_data)
        recommendation = build_recommendation(risk_level, risk_factors)

        # Stage 6: estimated revenue at risk (clearly labeled as an estimate)
        revenue_at_risk = monthly_charges * probability

        # =================================================
        # Prediction Result
        # =================================================

        st.markdown('<div class="result-panel">', unsafe_allow_html=True)
        st.markdown('<div class="result-title">🎯 Prediction Result</div>', unsafe_allow_html=True)

        result_col1, result_col2 = st.columns([1, 1.3])

        with result_col1:
            render_gauge(probability, risk_color)
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <span class="risk-pill {risk_class}">{risk_level}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with result_col2:
            factors_html = ""
            if risk_factors:
                chips = "".join(
                    f'<div class="factor-chip">{f}</div>' for f in risk_factors
                )
                factors_html = f"""
                <div class="factors-label">Possible risk factors (rule-based, see note below)</div>
                <div class="factor-chip-row">{chips}</div>
                """

            st.markdown(
                f"""
                <div class="risk-desc">{description}</div>
                {factors_html}
                <div class="recommendation-box">
                    <div class="rec-title">💡 Recommended Action</div>
                    <div class="rec-text">{recommendation}</div>
                </div>
                <div class="revenue-box">
                    <div class="rec-title">💰 Estimated Revenue at Risk (monthly)</div>
                    <div class="revenue-value">${revenue_at_risk:,.2f}</div>
                    <div class="revenue-note">
                        Estimate only = Monthly Charges × Churn Probability.
                        Not a guaranteed or actual lost-revenue figure.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        st.caption(
            "⚠️ Risk factors above are rule-based heuristics on common churn "
            "correlates in this dataset — not a claim that these specific "
            "values caused this prediction. For a genuine model-based "
            "explanation of this prediction, see the **Explainability** page."
        )

    except Exception as e:

        st.error(
            f"Prediction failed: {e}"
        )


# =========================================================
# Footer
# =========================================================

st.markdown(
    """
    <div class="app-footer">
        Telecom Customer Churn Prediction • Machine Learning Application
    </div>
    """,
    unsafe_allow_html=True
)
