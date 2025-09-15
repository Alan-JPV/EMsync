# app_final_experimental.py
import streamlit as st
import joblib
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Experimental Predictor", page_icon="🔬", layout="wide")

# --- Load the 3 Experimental Models ---
@st.cache_resource
def load_models():
    models = {}
    model_files = ['dialysis_model.pkl', 'sedatives_model.pkl', 'opioids_model.pkl']
    for f in model_files:
        try:
            model_name = f.replace('_model.pkl', '')
            models[model_name] = joblib.load(f)
        except FileNotFoundError:
            st.error(f"CRITICAL ERROR: Model file '{f}' not found. Please ensure all 3 .pkl files are in the folder.")
            st.stop()
    return models

models = load_models()
training_features = models['dialysis'].get_booster().feature_names

# --- Streamlit App Interface ---
st.title('🔬 EMsync: Experimental Resource Prediction')
st.write("This tool uses models to predict the need for Dialysis, Sedatives, and Opioids, with adjustable decision thresholds.")

# --- Input Data via Sidebar ---
st.sidebar.header('Patient Data Input')
mean_hr = st.sidebar.slider('Heart Rate (bpm)', 50, 150, 90)
mean_mbp = st.sidebar.slider('Mean Blood Pressure (mmHg)', 50, 120, 80)
mean_spo2 = st.sidebar.slider('Oxygen Saturation (%)', 80, 100, 95)
mean_temp_c = st.sidebar.slider('Temperature (°C)', 35.0, 41.0, 37.0, 0.1)

# --- Prepare the feature set once ---
input_data = {feature: 0.0 for feature in training_features}
input_data['mean_hr'] = float(mean_hr); input_data['min_hr'] = float(mean_hr-10); input_data['max_hr'] = float(mean_hr+10)
input_data['mean_sbp'] = float(mean_mbp+10); input_data['min_sbp'] = float(mean_mbp); input_data['max_sbp'] = float(mean_mbp+20)
input_data['mean_dbp'] = float(mean_mbp-10); input_data['min_dbp'] = float(mean_mbp-20); input_data['max_dbp'] = float(mean_mbp)
input_data['mean_spo2'] = float(mean_spo2); input_data['min_spo2'] = float(mean_spo2-3); input_data['max_spo2'] = 100.0
input_data['mean_temp_c'] = float(mean_temp_c); input_data['min_temp_c'] = float(mean_temp_c-0.5); input_data['max_temp_c'] = float(mean_temp_c+0.5)
input_df = pd.DataFrame([input_data])[training_features]

# --- Display Predictions and Threshold Sliders ---
st.subheader('Prediction Results')
cols = st.columns(len(models))
model_names = ['dialysis', 'sedatives', 'opioids']
icons = ["", "💊", "💊"]

for col, name, icon in zip(cols, model_names, icons):
    with col:
        model = models[name]
        probability = model.predict_proba(input_df)[0][1]
        
        st.markdown(f"#### {icon} {name.capitalize()} Need")
        
        # --- Interactive Threshold Slider ---
        default_threshold = 0.5
        if name == 'dialysis': default_threshold = 0.25
        if name in ['sedatives', 'opioids']: default_threshold = 0.75
            
        threshold = st.slider(f"Threshold for {name.capitalize()}", 0.0, 1.0, default_threshold, 0.05)
        
        # Prediction is now based on the adjustable threshold
        prediction = 1 if probability >= threshold else 0
        
        if prediction == 1:
            st.error(f"**Prediction: YES**")
        else:
            st.success(f"**Prediction: NO**")
        
        st.metric(label="Model Confidence", value=f"{probability:.2%}")
        st.progress(int(probability * 100))