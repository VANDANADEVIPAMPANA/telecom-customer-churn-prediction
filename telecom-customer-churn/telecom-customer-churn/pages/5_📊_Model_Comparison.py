import os
import pandas as pd
import streamlit as st


# --------------------------------
# Page configuration
# --------------------------------

st.set_page_config(
    page_title="Model Comparison",
    page_icon="📊",
    layout="wide"
)


# --------------------------------
# Page title
# --------------------------------

st.title("📊 Model Comparison")
st.write(
    "Compare the performance of the machine learning models "
    "used for telecom customer churn prediction."
)

st.divider()


# --------------------------------
# Locate results file
# --------------------------------

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

RESULTS_FILE = os.path.join(
    PROJECT_ROOT,
    "models",
    "model_comparison_results.csv"
)


# --------------------------------
# Load model comparison results
# --------------------------------

if not os.path.exists(RESULTS_FILE):
    st.error(
        "Model comparison results file was not found."
    )
    st.stop()

try:
    results = pd.read_csv(RESULTS_FILE)
except Exception as e:
    st.error(
        f"Could not load model comparison results: {e}"
    )
    st.stop()


# --------------------------------
# Display raw data information
# --------------------------------

st.subheader("🤖 Models Evaluated")

st.write(
    "The project evaluates three machine learning models:"
)

models = results.iloc[:, 0].tolist()

for model_name in models:
    st.write(f"• {model_name}")


# --------------------------------
# Identify metric columns
# --------------------------------

metric_columns = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1-Score",
    "ROC-AUC"
]

available_metrics = [
    column for column in metric_columns
    if column in results.columns
]


# --------------------------------
# Performance table
# --------------------------------

st.divider()

st.subheader("📋 Performance Comparison")

display_results = results.copy()

for column in available_metrics:
    display_results[column] = (
        display_results[column] * 100
    ).round(2).astype(str) + "%"

st.dataframe(
    display_results,
    use_container_width=True,
    hide_index=True
)


# --------------------------------
# Best model based on F1-score
# --------------------------------

if "F1-Score" in results.columns:

    best_index = results["F1-Score"].idxmax()

    best_model = results.loc[
        best_index,
        results.columns[0]
    ]

    best_f1 = results.loc[
        best_index,
        "F1-Score"
    ]

    st.divider()

    st.subheader("🏆 Best Model")

    st.success(
        f"**{best_model}** has the highest F1-score "
        f"of **{best_f1:.4f}**."
    )


# --------------------------------
# Model metrics
# --------------------------------

st.divider()

st.subheader("📈 Model Performance")

selected_metric = st.selectbox(
    "Select a metric to compare",
    available_metrics
)

chart_data = results[
    [results.columns[0], selected_metric]
].copy()

chart_data = chart_data.set_index(
    results.columns[0]
)

st.bar_chart(chart_data)


# --------------------------------
# Model selection explanation
# --------------------------------

st.divider()

st.subheader("💡 Why Logistic Regression?")

st.write(
    """
    Logistic Regression is used as the production model because
    it provides a good balance between predictive performance
    and interpretability.

    The model is also suitable for customer churn analysis because
    its coefficients can be used to understand how different
    customer features influence the prediction.

    This interpretability is especially useful for the
    Model Explainability page, where individual customer
    predictions can be explained using the model coefficients.
    """
)


# --------------------------------
# Metric explanations
# --------------------------------

st.divider()

st.subheader("📚 Evaluation Metrics")

st.markdown(
    """
    **Accuracy:** Percentage of total predictions that are correct.

    **Precision:** Among customers predicted as churn, how many
    actually churned.

    **Recall:** Among actual churn customers, how many were
    correctly identified.

    **F1-Score:** Harmonic mean of Precision and Recall.

    **ROC-AUC:** Measures how well the model separates churn
    and non-churn customers across different thresholds.
    """
)