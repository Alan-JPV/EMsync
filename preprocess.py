# preprocess.py
import pandas as pd
import hashlib

# -----------------------
# Config
# -----------------------
EDSTAYS_FILE = "edstays.csv.gz"
TRIAGE_FILE = "triage.csv.gz"
VITALS_FILE = "vitalsign.csv.gz"

OUTPUT_CSV = "features_mimic_ed.csv"
OUTPUT_PARQUET = "features_mimic_ed.parquet"

# -----------------------
# Helper: Hash IDs for privacy
# -----------------------
def hash_id(val):
    return hashlib.sha256(str(val).encode()).hexdigest()

# -----------------------
# Load raw tables
# -----------------------
print("Loading raw tables...")
edstays = pd.read_csv(EDSTAYS_FILE)
triage = pd.read_csv(TRIAGE_FILE)
vitals = pd.read_csv(VITALS_FILE)

print("Raw tables loaded:")
print("edstays:", edstays.shape, "triage:", triage.shape, "vitals:", vitals.shape)

# -----------------------
# Hash IDs
# -----------------------
print("Hashing IDs for privacy...")
for df in [edstays, triage, vitals]:
    df["stay_id_hash"] = df["stay_id"].apply(hash_id)

# -----------------------
# Clean vitals
# -----------------------
print("Cleaning vitals...")
numeric_cols = ["temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp", "pain"]
for col in numeric_cols:
    vitals[col] = pd.to_numeric(vitals[col], errors="coerce")

# -----------------------
# Aggregate vitals
# -----------------------
print("Aggregating vital signs...")
vital_agg = vitals.groupby("stay_id_hash").agg({
    "heartrate": ["median", "min", "max"],
    "resprate": ["median"],
    "o2sat": ["median", "min"],
    "temperature": ["median"],
    "sbp": ["median"],
    "dbp": ["median"],
    "pain": ["median"]
})

# Flatten column names (e.g., heartrate_median)
vital_agg.columns = ["_".join(col).strip() for col in vital_agg.columns.values]
vital_agg = vital_agg.reset_index()
print("Aggregated vitals shape:", vital_agg.shape)

# -----------------------
# Merge features
# -----------------------
print("Merging features...")
features = edstays[["stay_id", "stay_id_hash", "subject_id", "intime", "outtime"]].merge(
    triage[["stay_id_hash", "acuity", "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp"]],
    on="stay_id_hash",
    how="left"
).merge(
    vital_agg,
    on="stay_id_hash",
    how="left"
)

print("Final features shape:", features.shape)

# -----------------------
# Save outputs
# -----------------------
features.to_csv(OUTPUT_CSV, index=False)
features.to_parquet(OUTPUT_PARQUET, index=False)

print(f"✅ Saved {OUTPUT_CSV} and {OUTPUT_PARQUET}")

# Optional: Preview a few rows
print("\nPreview of features:")
print(features.head())
