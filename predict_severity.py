# file to run the modelll

# predict_severity.py
import joblib
import pandas as pd
import numpy as np

# --- 1. LOAD THE SAVED MODEL ---
# Make sure this filename matches your saved baseline model
model_filename = 'xgboost_baseline_71bal_acc.pkl'
try:
    model = joblib.load(model_filename)
except FileNotFoundError:
    print(f"ERROR: Model file not found.")
    print(f"Please make sure '{model_filename}' is in the same folder as this script.")
    exit()

# --- This function must be identical to the one in the training script ---
def add_engineered_features(df):
    df = df.copy()
    sbp_safe = df["sbp"].replace(0, np.nan)
    df["shock_index"] = df["heartrate"] / sbp_safe
    df["pulse_pressure"] = df["sbp"] - df["dbp"]
    df["hypoxia_flag"] = (df["o2sat"] < 90).astype(int)
    df["fever_flag"] = (df["temperature"] >= 38).astype(int)
    return df

# --- 2. PREPARE THE NEW PATIENT'S DATA ---
# THIS IS THE SECTION YOU WILL MODIFY FOR EACH TEST
new_patient_data = {
    'temperature': 36.8, 'heartrate': 80, 'resprate': 18, 'o2sat': 98,
    'sbp': 120, 'dbp': 80, 'heartrate_median': 80, 'heartrate_min': 78,
    'heartrate_max': 82, 'resprate_median': 18, 'o2sat_median': 98,
    'o2sat_min': 97, 'temperature_median': 36.8, 'sbp_median': 120,
    'dbp_median': 80, 'pain_median': 2, 'shock_index': np.nan,
    'pulse_pressure': np.nan, 'hypoxia_flag': np.nan, 'fever_flag': np.nan
}

print("--- TESTING WITH SIMULATED VITALS ---")
print(new_patient_data)

input_df = pd.DataFrame([new_patient_data])
input_df_engineered = add_engineered_features(input_df)
original_features = [
    'temperature', 'heartrate', 'resprate', 'o2sat', 'sbp', 'dbp', 'heartrate_median',
    'heartrate_min', 'heartrate_max', 'resprate_median', 'o2sat_median', 'o2sat_min',
    'temperature_median', 'sbp_median', 'dbp_median', 'pain_median', 'shock_index',
    'pulse_pressure', 'hypoxia_flag', 'fever_flag'
]
input_df_final = input_df_engineered[original_features]

# --- 3. MAKE THE PREDICTION ---
prediction_index = model.predict(input_df_final)[0]
prediction_probabilities = model.predict_proba(input_df_final)[0]
severity_map = {0: 'Critical', 1: 'Moderate', 2: 'Low Urgency'}
predicted_severity = severity_map[prediction_index]

# --- 4. DISPLAY THE RESULT ---
print("\n--- PREDICTION RESULT ---")
print(f"Predicted Severity: {predicted_severity}")
print("Confidence Scores:")
print(f"  - Critical:     {prediction_probabilities[0]:.2%}")
print(f"  - Moderate:     {prediction_probabilities[1]:.2%}")
print(f"  - Low Urgency:  {prediction_probabilities[2]:.2%}")
print("-------------------------\n")