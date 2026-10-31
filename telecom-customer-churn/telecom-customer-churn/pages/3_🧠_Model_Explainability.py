"""
pages/3_🧠_Model_Explainability.py
------------------------------------
Stage 4: Model explainability using the ACTUAL saved Logistic Regression
model — no retraining, no invented explanations.

Section 1 (Global): classifier.coef_ directly from the saved pipeline.

Section 2 (Per-customer): since the deployed model is linear
(Logistic Regression), each feature's exact contribution to THIS
customer's prediction is coefficient × transformed_feature_value.
Summing all contributions + the intercept exactly reproduces the
model's real logit/probability — this is verified below at runtime
(not approximated), so it is a genuine model explanation, clearly
distinct from the rule-based risk factors on the Home page.

SHAP is intentionally NOT used here — it's an unnecessary dependency
for a linear model, where exact contributions are already available
for free from the coefficients themselves.
"""

import sys
import os
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from predict import load_model  # noqa: E402
from preprocessing import FEATURE_COLUMNS  # noqa: E402

st.set_page_config(page_title="Model Explainability", page_icon="🧠", layout="wide")

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
    .surface-card { background: #FFFFFF; border: 1px solid #E3E8F0; border-radius: 16px; padding: 22px; margin-bottom: 22px; }
    .verify-badge {
        display: inline-block; background: #E8F8EE; color: #16A34A; font-size: 12.5px;
        font-weight: 700; padding: 5px 12px; border-radius: 999px; margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="page-header"><div class="page-header-inner">
        <h1>🧠 Model Explainability</h1>
        <p>What actually drives churn predictions, straight from the deployed model's own coefficients.</p>
    </div></div>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_model():
    return load_model()


try:
    model = get_model()
    preprocessor = model.named_steps["preprocessor"]
    classifier = model.named_steps["classifier"]
except Exception as e:
    st.error(f"Could not load the trained model: {e}")
    st.stop()

is_linear = hasattr(classifier, "coef_")

# =======================================================================
# SECTION 1 — Global Feature Importance (from the actual saved model)
# =======================================================================
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("### 🌍 Global Feature Importance")
st.caption(
    "Pulled directly from the deployed model's own coefficients "
    f"(`{type(classifier).__name__}.coef_`) — not recomputed or estimated."
)

if is_linear:
    feature_names = preprocessor.get_feature_names_out()
    coefs = classifier.coef_[0]
    imp_df = pd.DataFrame({"feature": feature_names, "coefficient": coefs})

    top_n = st.slider("Number of top features to show", 5, 30, 15)
    plot_df = imp_df.reindex(imp_df["coefficient"].abs().sort_values(ascending=False).index).head(top_n)
    plot_df = plot_df.sort_values(by="coefficient")

    fig, ax = plt.subplots(figsize=(9, max(4, top_n * 0.32)))
    colors = ["#DC2626" if v > 0 else "#16A34A" for v in plot_df["coefficient"]]
    ax.barh(plot_df["feature"], plot_df["coefficient"], color=colors)
    ax.set_xlabel("Coefficient (positive = increases churn odds, negative = decreases it)")
    ax.axvline(0, color="#697386", linewidth=0.8)
    st.pyplot(fig)
    plt.close(fig)

    st.caption("🔴 Increases churn odds. 🟢 Decreases churn odds. Bar length = strength of effect (log-odds scale).")
elif hasattr(classifier, "feature_importances_"):
    feature_names = preprocessor.get_feature_names_out()
    importances = classifier.feature_importances_
    imp_df = pd.DataFrame({"feature": feature_names, "importance": importances})
    imp_df = imp_df.sort_values(by="importance", ascending=False).head(15)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(imp_df["feature"][::-1], imp_df["importance"][::-1], color="#3358F4")
    ax.set_xlabel("Feature importance")
    st.pyplot(fig)
    plt.close(fig)
else:
    st.warning("The deployed model doesn't expose coefficients or feature importances.")

st.markdown("</div>", unsafe_allow_html=True)

# =======================================================================
# SECTION 2 — Per-customer explanation (exact, for linear models)
# =======================================================================
st.markdown('<div class="surface-card">', unsafe_allow_html=True)
st.markdown("### 🔬 Why This Customer? (Exact Model Explanation)")

if "last_input" not in st.session_state:
    st.info("Make a prediction on the **Home** page first, then come back here to see why.")
elif not is_linear:
    st.warning(
        "The deployed model isn't linear, so exact per-feature contributions "
        "(coefficient × value) don't apply the same way. Global importance above is still valid."
    )
else:
    input_data = st.session_state["last_input"]
    label, probability = st.session_state.get("last_prediction", ("?", 0.0))
    st.markdown(f"**Last prediction:** `{label}` ({probability*100:.1f}% churn probability)")

    feature_names = preprocessor.get_feature_names_out()
    coefs = classifier.coef_[0]
    intercept = classifier.intercept_[0]

    input_df = pd.DataFrame([input_data], columns=FEATURE_COLUMNS)
    X_transformed = preprocessor.transform(input_df)
    if hasattr(X_transformed, "toarray"):
        X_transformed = X_transformed.toarray()
    X_transformed = X_transformed[0]

    contributions = coefs * X_transformed
    logit = intercept + contributions.sum()
    reconstructed_prob = 1 / (1 + np.exp(-logit))

    # Verify the math actually reproduces the real prediction before
    # showing it as an "explanation" — if it doesn't match, say so
    # instead of silently showing something wrong.
    match = abs(reconstructed_prob - probability) < 1e-6

    if match:
        st.markdown(
            '<span class="verify-badge">✓ Verified: contributions sum exactly to the model\'s real prediction</span>',
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            f"Reconstructed probability ({reconstructed_prob*100:.2f}%) doesn't exactly "
            f"match the displayed prediction ({probability*100:.2f}%) — showing it anyway "
            f"for reference, but treat with caution."
        )

    contrib_df = pd.DataFrame({"feature": feature_names, "contribution": contributions})
    contrib_df = contrib_df.reindex(
        contrib_df["contribution"].abs().sort_values(ascending=False).index
    ).head(15)
    contrib_df = contrib_df.sort_values(by="contribution")

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["#DC2626" if v > 0 else "#16A34A" for v in contrib_df["contribution"]]
    ax.barh(contrib_df["feature"], contrib_df["contribution"], color=colors)
    ax.set_xlabel("Contribution to this customer's prediction (log-odds)")
    ax.axvline(0, color="#697386", linewidth=0.8)
    st.pyplot(fig)
    plt.close(fig)

    st.caption(
        "🔴 Pushed this customer toward Churn. 🟢 Pushed toward No Churn. "
        "This is an exact decomposition of the model's own math for this customer "
        "— different from the rule-based 'risk factors' shown on the Home page."
    )

st.markdown("</div>", unsafe_allow_html=True)

# =======================================================================
# Optional: SHAP (only if installed; app must work perfectly without it)
# =======================================================================
with st.expander("🔧 Advanced: SHAP-based explanation (optional, requires `shap`)"):
    st.caption(
        "Not required — the exact coefficient-based explanation above already "
        "gives a mathematically verified answer for this linear model. This is "
        "only here for users who specifically want SHAP-formatted output."
    )
    try:
        import shap  # noqa: F401
        st.success("`shap` is installed in this environment. (Full SHAP visualization not wired up in this build to avoid adding an untested dependency path — the verified coefficient explanation above is the primary, supported method.)")
    except ImportError:
        st.info("`shap` is not installed. This is expected and fine — it's optional and nothing above depends on it.")
