# EMsync_Ultimate_Dashboard.py
import streamlit as st
import joblib
import pandas as pd
import numpy as np
import time

# --- Page Configuration ---
st.set_page_config(page_title="EMsync Final Dashboard", page_icon="🚨", layout="wide")

# --- Model Loading ---
@st.cache_resource
def load_all_models():
    models = {}
    try:
        models['severity'] = joblib.load('xgboost_baseline_71bal_acc.pkl')
        models['ventilator'] = joblib.load('ventilator_model.pkl')
        models['vasopressors'] = joblib.load('vasopressors_model.pkl')
        models['dialysis'] = joblib.load('dialysis_model.pkl')
        models['sedatives'] = joblib.load('sedatives_model.pkl')
        models['opioids'] = joblib.load('opioids_model.pkl')
        models['icu_unit'] = joblib.load('icu_unit_model.pkl')
        models['icu_label_encoder'] = joblib.load('icu_unit_label_encoder.pkl')
    except FileNotFoundError as e:
        st.error(f"A model file was not found. Ensure all 8 .pkl files are in the folder. Details: {e}")
        st.stop()
    return models

models = load_all_models()

# --- Helper Function ---
def add_engineered_features_severity(df):
    df = df.copy()
    sbp_safe = df["sbp"].replace(0, np.nan); df["shock_index"] = df["heartrate"] / sbp_safe
    df["pulse_pressure"] = df["sbp"] - df["dbp"]; df["hypoxia_flag"] = (df["o2sat"] < 90).astype(int)
    df["fever_flag"] = (df["temperature"] >= 38).astype(int)
    return df

# --- UI & State Initialization ---
st.title('🚨 EMsync: Unified Simulation Dashboard')
if 'run_simulation' not in st.session_state:
    st.session_state.run_simulation = False
if 'vitals_history' not in st.session_state:
    st.session_state.vitals_history = pd.DataFrame()

# --- Sidebar Controls ---
st.sidebar.title("Simulation Controls")
sim_mode = st.sidebar.radio("Select Simulation Mode", ["Pre-defined Scenario", "Manual Control"])
SCENARIOS = {
    "Stable Patient": {'hr': 80, 'sbp': 120, 'dbp': 80, 'rr': 18, 'spo2': 98, 'temp': 37.0, 'pain': 2, 'sofa': 2},
    "Septic Shock": {'hr': 130, 'sbp': 85, 'dbp': 55, 'rr': 28, 'spo2': 92, 'temp': 39.0, 'pain': 5, 'sofa': 12},
    "Severe Hypoxia": {'hr': 120, 'sbp': 110, 'dbp': 70, 'rr': 32, 'spo2': 86, 'temp': 37.5, 'pain': 3, 'sofa': 8},
}
initial_vitals = {}
scenario_name = "Manual Control"
if sim_mode == "Pre-defined Scenario":
    scenario_name = st.sidebar.selectbox("Select Patient Scenario", list(SCENARIOS.keys()))
    initial_vitals = SCENARIOS[scenario_name]
else:
    st.sidebar.subheader("Set Vitals")
    # Using session_state keys for manual control sliders
    for key, (min_val, max_val, default_val, step) in {
        'hr': (40, 200, 80, 1), 'sbp': (70, 200, 120, 1), 'dbp': (40, 120, 80, 1), 'rr': (10, 40, 18, 1),
        'spo2': (80, 100, 98, 1), 'temp': (35.0, 42.0, 37.0, 0.1), 'pain': (0, 10, 2, 1), 'sofa': (0, 24, 2, 1)
    }.items():
        st.session_state[key] = st.sidebar.slider(key.capitalize(), min_val, max_val, default_val, step)

if st.sidebar.button('**Start / Reset Simulation**', use_container_width=True):
    st.session_state.vitals_history = pd.DataFrame(); st.session_state.run_simulation = True; st.session_state.step = 0
    if sim_mode == "Pre-defined Scenario":
        # Store scenario vitals in session state to be used by the loop
        for key, value in initial_vitals.items():
            st.session_state[key] = value
    st.rerun()

# --- Main Display Area ---
if not st.session_state.run_simulation and st.session_state.vitals_history.empty:
    st.info("Select a simulation mode from the sidebar and click 'Start / Reset Simulation'.")
elif st.session_state.run_simulation:
    step = st.session_state.step
    current_vitals = {k: st.session_state[k] for k in SCENARIOS["Stable Patient"].keys()}

    if sim_mode == "Pre-defined Scenario":
        if scenario_name == 'Septic Shock': current_vitals['hr'] += step*2; current_vitals['sbp'] -= step*3
        elif scenario_name == 'Severe Hypoxia': current_vitals['spo2'] -= step*1; current_vitals['rr'] += step*1
    
    current_vitals['hr'] += np.random.randint(-2, 2); current_vitals['sbp'] += np.random.randint(-3, 3); current_vitals['spo2'] = max(75, min(100, current_vitals['spo2'] + np.random.uniform(-0.5, 0.5)))
    st.session_state.vitals_history = pd.concat([st.session_state.vitals_history, pd.DataFrame([current_vitals])], ignore_index=True)
    st.subheader(f"Simulation in Progress... (Time: {st.session_state.step+1} / 120s)")
    st.line_chart(st.session_state.vitals_history)
    
    st.session_state.step += 1
    if st.session_state.step >= 120: st.session_state.run_simulation = False
    time.sleep(1); st.rerun()
else:
    st.subheader("Simulation Complete: Final Report"); history = st.session_state.vitals_history; final_vitals = history.iloc[-1]
    
    sev_model = models['severity']; sev_features = sev_model.get_booster().feature_names
    sev_data = {'temperature': final_vitals['temp'], 'heartrate': final_vitals['hr'], 'resprate': final_vitals['rr'], 'o2sat': final_vitals['spo2'], 'sbp': final_vitals['sbp'], 'dbp': final_vitals['dbp'], 'pain_median': float(final_vitals['pain'])}
    sev_df_engineered = add_engineered_features_severity(pd.DataFrame([sev_data]))
    for col in sev_features:
        if col not in sev_df_engineered.columns: sev_df_engineered[col] = 0
    sev_input = sev_df_engineered[sev_features]
    
    res_model = models['ventilator']; res_features = res_model.get_booster().feature_names
    res_data = {'mean_hr': history['hr'].mean(), 'min_hr': history['hr'].min(), 'max_hr': history['hr'].max(), 'mean_sbp': history['sbp'].mean(), 'min_sbp': history['sbp'].min(), 'max_sbp': history['sbp'].max(), 'mean_dbp': history['dbp'].mean(), 'min_dbp': history['dbp'].min(), 'max_dbp': history['dbp'].max(), 'mean_spo2': history['spo2'].mean(), 'min_spo2': history['spo2'].min(), 'max_spo2': history['spo2'].max(), 'mean_temp_c': history['temp'].mean(), 'min_temp_c': history['temp'].min(), 'max_temp_c': history['temp'].max(), 'sofa_score': float(final_vitals['sofa'])}
    for col in res_features:
        if col not in res_data: res_data[col] = 0
    res_input = pd.DataFrame([res_data])[res_features]
    
    sev_pred_idx = sev_model.predict(sev_input)[0]; sev_pred_probs = sev_model.predict_proba(sev_input)[0]; sev_map = {0: 'Critical', 1: 'Moderate', 2: 'Low Urgency'}
    icu_pred_idx = models['icu_unit'].predict(res_input)[0]; icu_label_encoder = models['icu_label_encoder']; icu_pred_name = icu_label_encoder.inverse_transform([icu_pred_idx])[0]; icu_pred_probs = models['icu_unit'].predict_proba(res_input)[0]
    
    st.subheader(f"Final Analysis for: *{scenario_name}*")
    col1, col2 = st.columns(2);
    with col1:
        st.markdown("##### Predicted Patient Severity"); sev_pred_text = sev_map[sev_pred_idx]
        if sev_pred_text == 'Critical': st.error(f"### {sev_pred_text}")
        elif sev_pred_text == 'Moderate': st.warning(f"### {sev_pred_text}")
        else: st.success(f"### {sev_pred_text}")
        prob_df_sev = pd.DataFrame({'Severity': list(sev_map.values()), 'Confidence': sev_pred_probs}); st.bar_chart(prob_df_sev.set_index('Severity'))
    with col2:
        st.markdown("##### Suggested ICU Destination"); st.info(f"### {icu_pred_name}")
        prob_df_icu = pd.DataFrame({'ICU Unit': icu_label_encoder.classes_, 'Probability': icu_pred_probs}).sort_values(by='Probability', ascending=False); st.bar_chart(prob_df_icu.set_index('ICU Unit'))
    
    st.markdown("---"); st.subheader("Predicted Resource Needs")
    
    resource_probs = {name: models[name].predict_proba(res_input)[0][1] for name in ['ventilator', 'vasopressors', 'dialysis', 'sedatives', 'opioids']}
    cols = st.columns(5); icons = ["💨 Ventilator", "❤️ Vasopressors", "కిडनी Dialysis", "💊 Sedatives", "💊 Opioids"]
    for col, icon, (name, prob) in zip(cols, icons, resource_probs.items()):
        with col:
            st.markdown(f"<h6>{icon}</h6>", unsafe_allow_html=True)
            pred = 1 if prob > 0.5 else 0
            if pred == 1: st.error("**YES**")
            else: st.success("**NO**")
            st.metric(label="Model Confidence", value=f"{prob:.2%}"); st.progress(int(prob * 100))