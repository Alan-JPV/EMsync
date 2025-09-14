# app_resources.py
import streamlit as st
import joblib
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Resource Predictor", page_icon="🏥", layout="wide")

# --- Load Models and Feature Lists ---
try:
    # These filenames must exactly match the files in your folder
    ventilator_model = joblib.load('ventilator_model.pkl')
    vasopressors_model = joblib.load('vasopressors_model.pkl')
    
    # We can get the feature list from either model
    training_features = ventilator_model.get_booster().feature_names
    print("✅ Models loaded successfully.")
except FileNotFoundError as e:
    st.error(f"A model file was not found. Please ensure ventilator_model.pkl and vasopressors_model.pkl are present. Details: {e}")
    st.stop()

# --- Streamlit App Interface ---
st.title('🏥 EMsync: Resource Requirement Prediction')
st.write("This tool uses trained models to predict the likelihood of a patient requiring critical resources based on their initial ICU data.")

# --- Input Data via Sidebar ---
st.sidebar.header('Patient Data Input')
st.sidebar.subheader("Average Vitals")
mean_hr = st.sidebar.slider('Heart Rate (bpm)', 50, 150, 90)
mean_mbp = st.sidebar.slider('Mean Blood Pressure (mmHg)', 50, 120, 80)
mean_spo2 = st.sidebar.slider('Oxygen Saturation (%)', 80, 100, 95)
mean_temp_c = st.sidebar.slider('Temperature (°C)', 35.0, 41.0, 37.0, 0.1)

if st.sidebar.button('**Predict Resource Needs**', use_container_width=True):
    # --- Prepare a single feature set for both models ---
    input_data = {feature: 0.0 for feature in training_features} # Use 0.0 for floats
    
    # Populate vitals from UI, approximating min/max/mean from a single value
    input_data['mean_hr'] = float(mean_hr); input_data['min_hr'] = float(mean_hr - 10); input_data['max_hr'] = float(mean_hr + 10)
    # Use sbp and dbp as they are in the training data, approximating mbp
    input_data['mean_sbp'] = float(mean_mbp + 10); input_data['min_sbp'] = float(mean_mbp); input_data['max_sbp'] = float(mean_mbp + 20)
    input_data['mean_dbp'] = float(mean_mbp - 10); input_data['min_dbp'] = float(mean_mbp - 20); input_data['max_dbp'] = float(mean_mbp)
    input_data['mean_spo2'] = float(mean_spo2); input_data['min_spo2'] = float(mean_spo2 - 3); input_data['max_spo2'] = 100.0
    input_data['mean_temp_c'] = float(mean_temp_c); input_data['min_temp_c'] = float(mean_temp_c - 0.5); input_data['max_temp_c'] = float(mean_temp_c + 0.5)
    
    input_df = pd.DataFrame([input_data])[training_features]

    # --- Make Predictions with BOTH models ---
    vent_pred = ventilator_model.predict(input_df)[0]
    vent_prob = ventilator_model.predict_proba(input_df)[0][1]

    vaso_pred = vasopressors_model.predict(input_df)[0]
    vaso_prob = vasopressors_model.predict_proba(input_df)[0][1]

    # --- Display Results Side-by-Side ---
    st.subheader('Prediction Results')
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💨 Ventilator Need")
        if vent_pred == 1:
            st.error(f"**Prediction: YES**")
        else:
            st.success(f"**Prediction: NO**")
        st.metric(label="Confidence", value=f"{vent_prob:.2%}")
        st.progress(int(vent_prob * 100))

    with col2:
        st.markdown("#### ❤️ Vasopressor Need")
        if vaso_pred == 1:
            st.error(f"**Prediction: YES**")
        else:
            st.success(f"**Prediction: NO**")
        st.metric(label="Confidence", value=f"{vaso_prob:.2%}")
        st.progress(int(vaso_prob * 100))