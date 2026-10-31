"""
pages/2_📈_EDA_Insights.py
---------------------------
Stage 3: Exploratory data analysis and business insights, computed
directly from dataset/Telco-Customer-Churn.csv via the SAME
load_and_clean_data() function used by training — nothing invented.
"""

import sys
import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

matplotlib.use("Agg")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from preprocessing import load_and_clean_data  # noqa: E402

st.set_page_config(page_title="EDA & Business Insights", page_icon="📈", layout="wide")

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
    .surface-card { background: #FFFFFF; border: 1px solid #E3E8F0; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
    .insight-box {
        background: #F6F8FE; border-left: 3px solid #3358F4; border-radius: 8px;
        padding: 12px 14px; margin-top: 10px; font-size: 13px; color: #3D4A63; line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-header"><div class="page-header-inner">
        <h1>📈 EDA &amp; Business Insights</h1>
        <p>Real patterns behind customer churn, computed directly from the training dataset.</p>
    </div></div>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = os.path.join(PROJECT_ROOT, "dataset", "Telco-Customer-Churn.csv")
if not os.path.exists(DATA_PATH):
    st.error(f"Dataset not found at {DATA_PATH}")
    st.stop()


@st.cache_data
def get_data():
    return load_and_clean_data(DATA_PATH)


df = get_data()

sns.set_style("whitegrid")
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white"})
PALETTE = ["#16A34A", "#DC2626"]  # No Churn, Churn


def info_card(label, value):
    st.markdown(
        f'<div class="info-card"><div class="card-label">{label}</div>'
        f'<div class="card-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# Top-line stats
# ---------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
with c1:
    info_card("Total Customers", f"{len(df):,}")
with c2:
    info_card("Overall Churn Rate", f"{df['Churn'].mean()*100:.1f}%")
with c3:
    info_card("Avg. Tenure", f"{df['tenure'].mean():.1f} months")
with c4:
    info_card("Avg. Monthly Charges", f"${df['MonthlyCharges'].mean():.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 1. Churn by Contract
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Churn by Contract Type")
ct = pd.crosstab(df["Contract"], df["Churn"], normalize="index") * 100
ct.columns = ["No Churn %", "Churn %"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ct.plot(kind="bar", stacked=True, color=PALETTE, ax=ax)
ax.set_ylabel("Percentage")
ax.set_xlabel("")
plt.xticks(rotation=0)
st.pyplot(fig)
plt.close(fig)
month_to_month_rate = ct.loc["Month-to-month", "Churn %"]
two_year_rate = ct.loc["Two year", "Churn %"]
insight(
    f"Month-to-month customers churn at **{month_to_month_rate:.1f}%**, "
    f"vs just **{two_year_rate:.1f}%** for two-year contracts. Contract "
    f"length shows a strong association with churn — likely because "
    f"month-to-month customers face no switching cost or commitment. "
    f"(Association, not proven causation.)"
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 2. Churn by Tenure
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Churn by Tenure")
fig, ax = plt.subplots(figsize=(8, 3.5))
sns.histplot(data=df, x="tenure", hue="Churn", multiple="stack", palette=PALETTE, bins=30, ax=ax)
ax.set_xlabel("Tenure (months)")
st.pyplot(fig)
plt.close(fig)
early_churn = df[df["tenure"] <= 12]["Churn"].mean() * 100
late_churn = df[df["tenure"] > 48]["Churn"].mean() * 100
insight(
    f"Customers in their first year churn at **{early_churn:.1f}%**, compared to "
    f"**{late_churn:.1f}%** for customers with 4+ years of tenure. Churn risk is "
    f"heavily front-loaded — the first 12 months are the highest-risk window."
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 3. Churn by Internet Service
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Churn by Internet Service")
ct2 = pd.crosstab(df["InternetService"], df["Churn"], normalize="index") * 100
ct2.columns = ["No Churn %", "Churn %"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ct2.plot(kind="bar", stacked=True, color=PALETTE, ax=ax)
ax.set_ylabel("Percentage")
ax.set_xlabel("")
plt.xticks(rotation=0)
st.pyplot(fig)
plt.close(fig)
fiber_rate = ct2.loc["Fiber optic", "Churn %"]
dsl_rate = ct2.loc["DSL", "Churn %"]
insight(
    f"Fiber optic customers churn at **{fiber_rate:.1f}%**, notably higher than "
    f"DSL customers at **{dsl_rate:.1f}%**. This may reflect pricing or service "
    f"quality issues specific to fiber — worth investigating operationally, "
    f"not something this data alone can explain."
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 4. Churn by Payment Method
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Churn by Payment Method")
ct3 = pd.crosstab(df["PaymentMethod"], df["Churn"], normalize="index") * 100
ct3.columns = ["No Churn %", "Churn %"]
ct3 = ct3.sort_values("Churn %", ascending=False)
fig, ax = plt.subplots(figsize=(8, 3.5))
ct3.plot(kind="bar", stacked=True, color=PALETTE, ax=ax)
ax.set_ylabel("Percentage")
ax.set_xlabel("")
plt.xticks(rotation=15, ha="right")
st.pyplot(fig)
plt.close(fig)
top_payment = ct3.index[0]
top_payment_rate = ct3.iloc[0]["Churn %"]
insight(
    f"**{top_payment}** has the highest churn rate among payment methods, at "
    f"**{top_payment_rate:.1f}%** — automatic payment methods (bank transfer, "
    f"credit card) tend to show lower churn, possibly because they reduce "
    f"friction/lapses in billing."
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 5. Monthly Charges vs Churn
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Monthly Charges by Churn Status")
fig, ax = plt.subplots(figsize=(8, 3.5))
sns.boxplot(data=df, x="Churn", y="MonthlyCharges", hue="Churn", palette=PALETTE, legend=False, ax=ax)
ax.set_xticks([0, 1])
ax.set_xticklabels(["No Churn", "Churn"])
ax.set_xlabel("")
st.pyplot(fig)
plt.close(fig)
churn_avg_charge = df[df["Churn"] == 1]["MonthlyCharges"].mean()
no_churn_avg_charge = df[df["Churn"] == 0]["MonthlyCharges"].mean()
insight(
    f"Customers who churn pay **${churn_avg_charge:.2f}/month** on average, vs "
    f"**${no_churn_avg_charge:.2f}/month** for those who stay. Higher bills are "
    f"associated with higher churn — price sensitivity is a plausible factor."
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 6. Senior Citizen status
# ---------------------------------------------------------------------
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("#### Churn by Senior Citizen Status")
ct4 = pd.crosstab(df["SeniorCitizen"], df["Churn"], normalize="index") * 100
ct4.columns = ["No Churn %", "Churn %"]
ct4.index = ["Not Senior", "Senior Citizen"]
fig, ax = plt.subplots(figsize=(8, 3.5))
ct4.plot(kind="bar", stacked=True, color=PALETTE, ax=ax)
ax.set_ylabel("Percentage")
ax.set_xlabel("")
plt.xticks(rotation=0)
st.pyplot(fig)
plt.close(fig)
senior_rate = ct4.loc["Senior Citizen", "Churn %"]
non_senior_rate = ct4.loc["Not Senior", "Churn %"]
insight(
    f"Senior citizens churn at **{senior_rate:.1f}%**, noticeably higher than "
    f"**{non_senior_rate:.1f}%** for non-seniors — worth considering targeted "
    f"retention support for this segment."
)
st.markdown("</div>", unsafe_allow_html=True)

st.caption(
    "All figures above are calculated directly from the actual dataset "
    "(dataset/Telco-Customer-Churn.csv) — none are invented. Relationships "
    "shown are correlational, not proof of causation."
)
