# preprocess_icu_interventions.py (Corrected)
import argparse
import os
import pandas as pd
from typing import Optional, Set

def log(msg: str):
    print(f"[EMSync] {msg}", flush=True)

def find_csv(data_dir: str, filename: str) -> Optional[str]:
    path = os.path.join(data_dir, filename)
    if os.path.exists(path): return path
    path_gz = path + ".gz"
    if os.path.exists(path_gz): return path_gz
    return None

def read_csv_fast(path, usecols=None, parse_dates=None):
    return pd.read_csv(path, usecols=usecols, parse_dates=parse_dates, low_memory=False, compression="infer")

# --- THIS IS THE CORRECTED SECTION ---
# Simpler, more robust patterns to find the correct item IDs for blood pressure.
VITAL_PATTERNS = {
    "hr": r"heart rate",
    "spo2": r"o2 saturation|spo2|oximetry",
    "temp_c": r"temperature celsius",
    "sbp": r"systolic",
    "dbp": r"diastolic",
}

def get_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True, help="Folder with raw MIMIC CSVs")
    ap.add_argument("--out_path", default="icu_interventions.csv", help="Output filename")
    return ap.parse_args()

def map_itemids(d_items, pattern: str) -> Set[int]:
    # Finds all itemids whose labels match a given text pattern
    return set(d_items.loc[d_items["label"].str.contains(pattern, case=False, na=False, regex=True), "itemid"].astype(int))

def main():
    args = get_args()
    
    # --- 1. Load All Necessary Source Files ---
    paths = {
        "icustays": find_csv(args.data_dir, "icustays.csv"),
        "d_items": find_csv(args.data_dir, "d_items.csv"),
        "chartevents": find_csv(args.data_dir, "chartevents.csv"),
        "procedureevents": find_csv(args.data_dir, "procedureevents.csv"),
        "prescriptions": find_csv(args.data_dir, "prescriptions.csv"),
    }
    if any(p is None for p in paths.values()):
        log("ERROR: One or more required data files not found. Please check your --data_dir.")
        return

    log("Loading core data files...")
    icustays = read_csv_fast(paths["icustays"], usecols=["stay_id", "hadm_id"])
    d_items = read_csv_fast(paths["d_items"], usecols=["itemid", "label"])
    
    # --- 2. Extract Vital Signs ---
    log("Mapping vital sign itemids...")
    item_map = {name: map_itemids(d_items, pat) for name, pat in VITAL_PATTERNS.items()}

    log("Processing chartevents to extract vitals (this may take a while)...")
    all_vital_ids = set.union(*item_map.values())
    vitals_chunks = []
    # Read the large chartevents file in chunks to save memory
    for chunk in pd.read_csv(paths["chartevents"], usecols=["stay_id", "itemid", "valuenum"], chunksize=5_000_000):
        vitals_chunks.append(chunk[chunk["itemid"].isin(all_vital_ids)])
    
    vitals_df = pd.concat(vitals_chunks).dropna()
    
    def id_to_var(iid):
        for name, ids in item_map.items():
            if iid in ids: return name
        return None
    vitals_df['var'] = vitals_df['itemid'].map(id_to_var)
    
    vitals_agg = vitals_df.groupby(['stay_id', 'var'])['valuenum'].agg(['mean', 'min', 'max']).unstack()
    vitals_agg.columns = [f'{stat}_{var}' for stat, var in vitals_agg.columns]
    
    # --- 3. Build the Outcome Labels ---
    log("Building outcome labels...")
    procs = read_csv_fast(paths["procedureevents"], usecols=["stay_id", "itemid"])
    prescs = read_csv_fast(paths["prescriptions"], usecols=["hadm_id", "drug"])
    labels = icustays[['stay_id', 'hadm_id']].copy()
    
    # Ventilation Label
    vent_ids = {225792, 224385}
    labels['ventilation_needed'] = labels['stay_id'].isin(procs[procs['itemid'].isin(vent_ids)]['stay_id']).astype(int)
    
    # Vasopressor Label
    vaso_drugs = 'norepinephrine|vasopressin|epinephrine|dopamine|phenylephrine'
    labels['vasopressors_needed'] = labels['hadm_id'].isin(prescs[prescs['drug'].str.contains(vaso_drugs, case=False, na=False)]['hadm_id']).astype(int)
    
    # Transfusion and Dialysis labels can be added here following the same pattern
    labels['transfusion_needed'] = 0 # Placeholder
    labels['dialysis_needed'] = 0 # Placeholder

    # --- 4. Join Features and Labels & Save ---
    log("Joining features and labels into the final dataset...")
    final_df = icustays.merge(vitals_agg, on='stay_id', how='left').merge(labels, on=['stay_id', 'hadm_id'], how='left')
    
    final_df.to_csv(args.out_path, index=False)
    log(f"✅ Saved final dataset to {args.out_path}. Shape: {final_df.shape}")

if __name__ == "__main__":
    main()