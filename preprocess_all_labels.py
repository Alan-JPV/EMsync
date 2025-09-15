# preprocess_all_labels.py (Final, Robust Version)
import pandas as pd
import argparse
import os

# --- Helper functions to find files and log messages ---
def log(msg: str): print(f"[EMSync] {msg}", flush=True)

def find_csv(data_dir: str, filename: str):
    # This function checks for both .csv and .csv.gz
    path_csv = os.path.join(data_dir, f"{filename}.csv")
    path_gz = os.path.join(data_dir, f"{filename}.csv.gz")
    if os.path.exists(path_csv):
        return path_csv
    if os.path.exists(path_gz):
        return path_gz
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--out_path", default="icu_interventions_all.csv")
    args = parser.parse_args()

    print("--- Creating Dataset with All Labels ---")
    
    # --- 1. Load All Necessary Source Files using the robust finder ---
    try:
        icustays_path = find_csv(args.data_dir, "icustays")
        d_items_path = find_csv(args.data_dir, "d_items")
        chartevents_path = find_csv(args.data_dir, "chartevents")
        procedures_path = find_csv(args.data_dir, "procedureevents")
        prescriptions_path = find_csv(args.data_dir, "prescriptions")

        if not all([icustays_path, d_items_path, chartevents_path, procedures_path, prescriptions_path]):
            raise FileNotFoundError("One or more required MIMIC files were not found in the data directory.")

        icustays = pd.read_csv(icustays_path)
        d_items = pd.read_csv(d_items_path)
        chartevents = pd.read_csv(chartevents_path, usecols=['stay_id', 'itemid', 'valuenum'])
        procedures = pd.read_csv(procedures_path, usecols=['stay_id', 'itemid'])
        prescriptions = pd.read_csv(prescriptions_path, usecols=['hadm_id', 'drug'])
        print("✅ All source files loaded successfully.")
    except Exception as e:
        print(f"❌ ERROR loading files: {e}")
        return

    # --- 2. Create Vitals Features ---
    print("Extracting vital signs...")
    vital_patterns = {"hr": r"heart rate", "spo2": r"o2 saturation|spo2", "temp_c": r"temperature celsius", "sbp": r"systolic", "dbp": r"diastolic"}
    item_map = {name: set(d_items[d_items['label'].str.contains(pat, case=False, na=False)]['itemid']) for name, pat in vital_patterns.items()}
    all_vital_ids = set.union(*item_map.values())
    
    vitals_df = chartevents[chartevents['itemid'].isin(all_vital_ids)]
    def id_to_var(iid):
        for name, ids in item_map.items():
            if iid in ids: return name
    vitals_df['var'] = vitals_df['itemid'].map(id_to_var)
    
    vitals_agg = vitals_df.groupby(['stay_id', 'var'])['valuenum'].agg(['mean', 'min', 'max']).unstack()
    vitals_agg.columns = [f'{stat}_{var}' for stat, var in vitals_agg.columns]

    # --- 3. Create All Labels ---
    print("Creating all outcome labels...")
    labels = icustays[['stay_id', 'hadm_id']].copy()
    
    vent_ids = {225792, 224385}; labels['ventilation_needed'] = labels['stay_id'].isin(procedures[procedures['itemid'].isin(vent_ids)]['stay_id']).astype(int)
    vaso_drugs = 'norepinephrine|vasopressin|epinephrine|dopamine|phenylephrine'; labels['vasopressors_needed'] = labels['hadm_id'].isin(prescriptions[prescriptions['drug'].str.contains(vaso_drugs, case=False, na=False)]['hadm_id']).astype(int)
    dialysis_ids = {225802, 225803, 225805, 225807, 225809, 224149, 224150, 224151, 224152, 225442, 225951, 225952, 225953, 225954}; labels['dialysis_needed'] = labels['stay_id'].isin(procedures[procedures['itemid'].isin(dialysis_ids)]['stay_id']).astype(int)
    sed_drugs = 'propofol|midazolam|lorazepam|dexmedetomidine'; labels['sedatives_needed'] = labels['hadm_id'].isin(prescriptions[prescriptions['drug'].str.contains(sed_drugs, case=False, na=False)]['hadm_id']).astype(int)
    opioid_drugs = 'fentanyl|morphine|hydromorphone|oxycodone'; labels['opioids_needed'] = labels['hadm_id'].isin(prescriptions[prescriptions['drug'].str.contains(opioid_drugs, case=False, na=False)]['hadm_id']).astype(int)

    # --- 4. Join and Save ---
    final_df = icustays.merge(vitals_agg, on='stay_id', how='left').merge(labels, on=['stay_id', 'hadm_id'], how='left')
    final_df.to_csv(args.out_path, index=False)
    print(f"✅ Saved final dataset to {args.out_path}. Shape: {final_df.shape}")

if __name__ == "__main__":
    main()