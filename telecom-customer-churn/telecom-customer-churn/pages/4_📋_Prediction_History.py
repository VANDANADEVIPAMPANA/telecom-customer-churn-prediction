import requests
import pandas as pd
import streamlit as st
import json


# --------------------------------
# Page configuration
# --------------------------------

st.set_page_config(
    page_title="Prediction History",
    page_icon="📋",
    layout="wide"
)


# --------------------------------
# Backend configuration
# --------------------------------

API_URL = "http://127.0.0.1:8000"


# --------------------------------
# Page title
# --------------------------------

st.title("📋 Prediction History")

st.write(
    "View previous customer churn predictions stored in the database."
)

st.divider()


# --------------------------------
# Fetch prediction history
# --------------------------------

def get_prediction_history(limit=100):
    try:
        response = requests.get(
            f"{API_URL}/history",
            params={"limit": limit},
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            return data

        # Handle APIs that return records inside a dictionary
        if isinstance(data, dict):
            if isinstance(data.get("records"), list):
                return data["records"]

            if isinstance(data.get("history"), list):
                return data["history"]

        st.error("Unexpected response format from the backend.")
        return []

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to the backend API. "
            "Please make sure FastAPI is running."
        )
        return []

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load prediction history: {e}")
        return []


# --------------------------------
# Fetch individual prediction details
# --------------------------------

def get_prediction_details(record_id):
    try:
        response = requests.get(
            f"{API_URL}/history/{record_id}",
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            return data

        st.error("Unexpected response format for prediction details.")
        return None

    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            st.error(
                f"No prediction record found with ID {record_id}."
            )
        else:
            st.error(
                f"Could not retrieve prediction details: {e}"
            )

        return None

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to the backend API. "
            "Please make sure FastAPI is running."
        )
        return None

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to retrieve prediction details: {e}")
        return None


# --------------------------------
# Refresh history
# --------------------------------

if st.button(
    "🔄 Refresh History",
    use_container_width=True
):
    st.rerun()


# --------------------------------
# Load records
# --------------------------------

records = get_prediction_history(100)

if not records:
    st.info("No prediction history found.")
    st.stop()


# --------------------------------
# Convert records to DataFrame
# --------------------------------

history_data = []

for record in records:
    history_data.append({
        "ID": record.get("id"),
        "Date & Time": record.get("timestamp"),
        "Prediction": record.get("prediction"),
        "Churn Probability": record.get("churn_probability"),
        "Risk Level": record.get("risk_level"),
        "Request Type": record.get("request_type"),
        "Batch ID": record.get("batch_id")
    })


df = pd.DataFrame(history_data)


# --------------------------------
# Search by Prediction ID
# --------------------------------

st.divider()

st.subheader("🔍 Search Prediction")

st.write(
    "Enter a Prediction ID to view the details stored for that prediction."
)

col1, col2 = st.columns([3, 1])

with col1:
    prediction_id = st.number_input(
        "Prediction ID",
        min_value=1,
        step=1,
        value=1,
        key="prediction_search_id"
    )

with col2:
    st.write("")
    st.write("")

    search_clicked = st.button(
        "🔎 View Details",
        use_container_width=True
    )


# --------------------------------
# Search action
# --------------------------------

if search_clicked:

    details = get_prediction_details(int(prediction_id))

    if details is not None:
        st.session_state["selected_prediction_details"] = details
        st.session_state["selected_prediction_id"] = int(prediction_id)


# --------------------------------
# Display selected prediction details
# --------------------------------

if "selected_prediction_details" in st.session_state:

    details = st.session_state["selected_prediction_details"]

    selected_id = st.session_state.get(
        "selected_prediction_id",
        details.get("id", "unknown")
    )

    st.divider()

    st.subheader("👤 Customer Prediction Details")

    st.caption(f"Prediction ID: {selected_id}")

    # Display the complete response returned by the backend
    st.json(details)

    # Download details as JSON
    json_data = json.dumps(
        details,
        indent=4,
        ensure_ascii=False,
        default=str
    )

    st.download_button(
        label="⬇️ Download Prediction Details (JSON)",
        data=json_data,
        file_name=f"prediction_{selected_id}.json",
        mime="application/json",
        key="download_prediction_details"
    )


# --------------------------------
# Filters
# --------------------------------

st.divider()

st.subheader("🔎 Filter Predictions")

col1, col2 = st.columns(2)

with col1:
    risk_values = df["Risk Level"].dropna().unique().tolist()

    risk_options = ["All"] + sorted(
        risk_values,
        key=str
    )

    selected_risk = st.selectbox(
        "Risk Level",
        risk_options
    )

with col2:
    type_values = df["Request Type"].dropna().unique().tolist()

    type_options = ["All"] + sorted(
        type_values,
        key=str
    )

    selected_type = st.selectbox(
        "Prediction Type",
        type_options
    )


# --------------------------------
# Apply filters
# --------------------------------

filtered_df = df.copy()

if selected_risk != "All":
    filtered_df = filtered_df[
        filtered_df["Risk Level"] == selected_risk
    ]

if selected_type != "All":
    filtered_df = filtered_df[
        filtered_df["Request Type"] == selected_type
    ]


# --------------------------------
# Summary metrics
# --------------------------------

st.divider()

st.subheader("📊 Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Predictions",
        len(filtered_df)
    )

with col2:
    churn_count = (
        filtered_df["Prediction"] == "Churn"
    ).sum()

    st.metric(
        "Churn Predictions",
        int(churn_count)
    )

with col3:
    no_churn_count = (
        filtered_df["Prediction"] == "No Churn"
    ).sum()

    st.metric(
        "No Churn Predictions",
        int(no_churn_count)
    )

with col4:
    high_risk_count = (
        filtered_df["Risk Level"] == "High"
    ).sum()

    st.metric(
        "High Risk Customers",
        int(high_risk_count)
    )


# --------------------------------
# Prediction table
# --------------------------------

st.divider()

st.subheader("📋 Prediction Records")

display_df = filtered_df.copy()

if not display_df.empty:

    probabilities = pd.to_numeric(
        display_df["Churn Probability"],
        errors="coerce"
    )

    display_df["Churn Probability"] = probabilities.apply(
        lambda value: (
            f"{value * 100:.2f}%"
            if pd.notna(value)
            else "N/A"
        )
    )

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)