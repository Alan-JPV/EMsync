# app_new_resources.py (Corrected)
import streamlit as st
import joblib
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="New Resource Predictor", page_icon="🧪", layout="wide")

# --- Load the 3 New Models ---
try:
    dialysis_model = joblib.load('dialysis_model.pkl')
    sedatives_model = joblib.load('sedatives_model.pkl')
    opioids_model = joblib.load('opioids_model.pkl')
    training_features = dialysis_model.get_booster().feature_names
except FileNotFoundError as e:
    st.error(f"A model file was not found. Please ensure all 3 new .pkl files are present. Details: {e}")
    st.stop()

# --- Streamlit App Interface ---
st.title('🧪 EMsync: New Resource Prediction')
st.write("This tool predicts the likelihood of a patient requiring Dialysis, Sedatives, or Opioids.")

# --- Input Data via Sidebar ---
st.sidebar.header('Patient Data Input')
st.sidebar.subheader("Average Vitals")
mean_hr = st.sidebar.slider('Heart Rate (bpm)', 50, 150, 90)
mean_mbp = st.sidebar.slider('Mean Blood Pressure (mmHg)', 50, 120, 80)
mean_spo2 = st.sidebar.slider('Oxygen Saturation (%)', 80, 100, 95)
mean_temp_c = st.sidebar.slider('Temperature (°C)', 35.0, 41.0, 37.0, 0.1)

if st.sidebar.button('**Predict Resource Needs**', use_container_width=True):
    input_data = {feature: 0.0 for feature in training_features}
    
    input_data['mean_hr'] = float(mean_hr); input_data['min_hr'] = float(mean_hr-10); input_data['max_hr'] = float(mean_hr+10)
    input_data['mean_sbp'] = float(mean_mbp+10); input_data['min_sbp'] = float(mean_mbp); input_data['max_sbp'] = float(mean_mbp+20)
    input_data['mean_dbp'] = float(mean_mbp-10); input_data['min_dbp'] = float(mean_mbp-20); input_data['max_dbp'] = float(mean_mbp)
    input_data['mean_spo2'] = float(mean_spo2); input_data['min_spo2'] = float(mean_spo2-3); input_data['max_spo2'] = 100.0
    input_data['mean_temp_c'] = float(mean_temp_c); input_data['min_temp_c'] = float(mean_temp_c-0.5); input_data['max_temp_c'] = float(mean_temp_c+0.5)
    
    input_df = pd.DataFrame([input_data])[training_features]

    dialysis_pred = dialysis_model.predict(input_df)[0]
    dialysis_prob = dialysis_model.predict_proba(input_df)[0][1]
    sedatives_pred = sedatives_model.predict(input_df)[0]
    sedatives_prob = sedatives_model.predict_proba(input_df)[0][1]
    opioids_pred = opioids_model.predict(input_df)[0]
    opioids_prob = opioids_model.predict_proba(input_df)[0][1]

    st.subheader('Prediction Results')
    col1, col2, col3 = st.columns(3)

    # --- THIS IS THE CORRECTED SECTION ---
    with col1:
        st.markdown("####   Dialysis Need")
        if dialysis_pred == 0:
            st.success(f"**Prediction: NO**")
        else:
            st.error(f"**Prediction: YES**")
        st.metric(label="Confidence", value=f"{dialysis_prob:.2%}")
        st.progress(int(dialysis_prob * 100))

    with col2:
        st.markdown("#### 💊 Sedatives Need")
        if sedatives_pred == 0:
            st.success(f"**Prediction: NO**")
        else:
            st.error(f"**Prediction: YES**")
        st.metric(label="Confidence", value=f"{sedatives_prob:.2%}")
        st.progress(int(sedatives_prob * 100))
        
    with col3:
        st.markdown("#### 💊 Opioids Need")
        if opioids_pred == 0:
            st.success(f"**Prediction: NO**")
        else:
            st.error(f"**Prediction: YES**")
        st.metric(label="Confidence", value=f"{opioids_prob:.2%}")
        st.progress(int(opioids_prob * 100))