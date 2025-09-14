# app.py
import streamlit as st
import joblib
import pandas as pd
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="EMsync Severity Predictor",
    page_icon="🚑",
    layout="wide"
)

# --- Load Model and Functions ---
# This function must be identical to the one in the training script
def add_engineered_features(df):
    df = df.copy()
    sbp_safe = df["sbp"].replace(0, np.nan)
    df["shock_index"] = df["heartrate"] / sbp_safe
    df["pulse_pressure"] = df["sbp"] - df["dbp"]
    df["hypoxia_flag"] = (df["o2sat"] < 90).astype(int)
    df["fever_flag"] = (df["temperature"] >= 38).astype(int)
    return df

# Load the saved model
model_filename = 'xgboost_baseline_71bal_acc.pkl'
try:
    model = joblib.load(model_filename)
except FileNotFoundError:
    st.error(f"Model file '{model_filename}' not found. Please make sure it's in the same folder.")
    st.stop() # Stop the app from running if the model is not found

# --- Streamlit App Interface ---
st.title('EMsync: Real-Time Severity Prediction')
st.write("This tool uses a trained XGBoost model to predict patient severity based on their initial vital signs. Adjust the sliders in the sidebar to match the patient's vitals and click 'Predict'.")

# --- Input Vitals via Sidebar ---
st.sidebar.header('Patient Vitals Input')

# Create sliders for the 7 key vitals that would be collected
temperature = st.sidebar.slider('Temperature (°C)', 35.0, 42.0, 36.8, 0.1)
heartrate = st.sidebar.slider('Heart Rate (bpm)', 40, 200, 80)
resprate = st.sidebar.slider('Respiration Rate (breaths/min)', 10, 40, 18)
o2sat = st.sidebar.slider('Oxygen Saturation (%)', 80, 100, 98)
sbp = st.sidebar.slider('Systolic Blood Pressure (mmHg)', 70, 180, 120)
dbp = st.sidebar.slider('Diastolic Blood Pressure (mmHg)', 40, 120, 80)
pain_median = st.sidebar.slider('Pain Score (0-10)', 0, 10, 2)

# "Predict" button
if st.sidebar.button('**Predict Severity**', use_container_width=True):
    # --- Prepare data for the model ---
    # The model was trained on 20 features. We must create them all.
    # We'll use the slider values and create reasonable approximations for the rest.
    new_patient_data = {
        'temperature': temperature, 'heartrate': heartrate, 'resprate': resprate,
        'o2sat': o2sat, 'sbp': sbp, 'dbp': dbp, 'pain_median': pain_median,
        # Approximations for aggregated features
        'heartrate_median': heartrate, 'heartrate_min': heartrate - 5,
        'heartrate_max': heartrate + 5, 'resprate_median': resprate,
        'o2sat_median': o2sat, 'o2sat_min': o2sat - 1,
        'temperature_median': temperature, 'sbp_median': sbp, 'dbp_median': dbp,
        # Features to be engineered
        'shock_index': np.nan, 'pulse_pressure': np.nan,
        'hypoxia_flag': np.nan, 'fever_flag': np.nan
    }

    input_df = pd.DataFrame([new_patient_data])
    input_df_engineered = add_engineered_features(input_df)
    original_features = [
        'temperature', 'heartrate', 'resprate', 'o2sat', 'sbp', 'dbp', 'heartrate_median',
        'heartrate_min', 'heartrate_max', 'resprate_median', 'o2sat_median', 'o2sat_min',
        'temperature_median', 'sbp_median', 'dbp_median', 'pain_median', 'shock_index',
        'pulse_pressure', 'hypoxia_flag', 'fever_flag'
    ]
    input_df_final = input_df_engineered[original_features]

    # --- Make and display prediction ---
    prediction_index = model.predict(input_df_final)[0]
    prediction_probabilities = model.predict_proba(input_df_final)[0]
    severity_map = {0: 'Critical', 1: 'Moderate', 2: 'Low Urgency'}
    predicted_severity = severity_map[prediction_index]

    st.subheader('Prediction Result')
    
    # Display the result with a colored box
    if predicted_severity == 'Critical':
        st.error(f'### Predicted Severity: **{predicted_severity}**')
    elif predicted_severity == 'Moderate':
        st.warning(f'### Predicted Severity: **{predicted_severity}**')
    else:
        st.success(f'### Predicted Severity: **{predicted_severity}**')

    # Display confidence scores as a bar chart
    st.write('**Confidence Scores:**')
    prob_df = pd.DataFrame({
        'Severity': ['Critical', 'Moderate', 'Low Urgency'],
        'Confidence': prediction_probabilities
    })
    st.bar_chart(prob_df.set_index('Severity'))