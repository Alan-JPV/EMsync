# app_icu_unit.py
import streamlit as st
import joblib
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="ICU Unit Predictor", page_icon="🗺️", layout="wide")

# --- Load the Model and the Label Encoder ---
try:
    model = joblib.load('icu_unit_model.pkl')
    label_encoder = joblib.load('icu_unit_label_encoder.pkl')
    # Get the list of features the model was trained on
    training_features = model.get_booster().feature_names
    print("✅ Model and label encoder loaded successfully.")
except FileNotFoundError as e:
    st.error(f"A required file was not found. Ensure 'icu_unit_model.pkl' and 'icu_unit_label_encoder.pkl' are present. Details: {e}")
    st.stop()

# --- Streamlit App Interface ---
st.title('🗺️ EMsync: ICU Unit Predictor')
st.write("This tool predicts the most likely ICU destination for a patient based on their initial vital signs and overall acuity (SOFA score).")

# --- Input Data via Sidebar ---
st.sidebar.header('Patient Data Input')

# Sliders for the basic, common vitals
st.sidebar.subheader("Fundamental Vitals")
mean_hr = st.sidebar.slider('Heart Rate (bpm)', 50, 150, 90)
mean_mbp = st.sidebar.slider('Mean Blood Pressure (mmHg)', 50, 120, 80)
mean_spo2 = st.sidebar.slider('Oxygen Saturation (%)', 80, 100, 95)
mean_temp_c = st.sidebar.slider('Temperature (°C)', 35.0, 41.0, 37.0, 0.1)

# Slider for the powerful SOFA score feature
st.sidebar.subheader("Clinical Score")
sofa_score = st.sidebar.slider('SOFA Score', 0, 24, 6)


if st.sidebar.button('**Predict ICU Unit**', use_container_width=True):
    # --- Prepare the full feature set for the model ---
    input_data = {feature: 0.0 for feature in training_features}
    
    # Populate vitals from UI, approximating min/max from the mean value
    input_data['mean_hr'] = float(mean_hr); input_data['min_hr'] = float(mean_hr - 10); input_data['max_hr'] = float(mean_hr + 10)
    input_data['mean_sbp'] = float(mean_mbp + 10); input_data['min_sbp'] = float(mean_mbp); input_data['max_sbp'] = float(mean_mbp + 20)
    input_data['mean_dbp'] = float(mean_mbp - 10); input_data['min_dbp'] = float(mean_mbp - 20); input_data['max_dbp'] = float(mean_mbp)
    input_data['mean_spo2'] = float(mean_spo2); input_data['min_spo2'] = float(mean_spo2 - 3); input_data['max_spo2'] = 100.0
    input_data['mean_temp_c'] = float(mean_temp_c); input_data['min_temp_c'] = float(mean_temp_c - 0.5); input_data['max_temp_c'] = float(mean_temp_c + 0.5)
    
    # Include the SOFA score
    if 'sofa_score' in input_data:
        input_data['sofa_score'] = float(sofa_score)

    input_df = pd.DataFrame([input_data])[training_features]

    # --- Make and display prediction ---
    prediction_numeric = model.predict(input_df)[0]
    prediction_text = label_encoder.inverse_transform([prediction_numeric])[0]
    prediction_probabilities = model.predict_proba(input_df)[0]

    st.subheader('Prediction Result')
    st.success(f"### Suggested ICU Unit: **{prediction_text}**")
    
    st.write('**Probability Distribution:**')
    
    # Create a DataFrame for the bar chart
    prob_df = pd.DataFrame({
        'ICU Unit': label_encoder.classes_,
        'Probability': prediction_probabilities
    }).sort_values(by='Probability', ascending=False)
    
    st.bar_chart(prob_df.set_index('ICU Unit'))