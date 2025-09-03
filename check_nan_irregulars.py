import pandas as pd

# --- Load dataset ---
df = pd.read_csv("features_mimic_ed.csv")
print("🔍 Checking dataset quality...\n")
print(f"Initial shape: {df.shape}\n")

# --- Fix temperature units if values look like Fahrenheit ---
if "temperature_median" in df.columns:
    median_temp = df["temperature_median"].median()
    if median_temp > 45:  # likely Fahrenheit
        print("⚠️ Detected Fahrenheit temperatures, converting to Celsius...")
        df["temperature_median"] = (df["temperature_median"] - 32) * 5.0 / 9.0

# --- 1. NaN Report ---
nan_report = df.isna().sum()
print("NaN values per column:")
print(nan_report[nan_report > 0], "\n")

# --- 2. Define realistic ranges for vitals (clinical reference ranges) ---
valid_ranges = {
    "heartrate_median": (30, 220),     # bpm
    "resprate_median": (5, 50),        # breaths/min
    "o2sat_median": (50, 100),         # %
    "temperature_median": (30, 43),    # °C
    "sbp_median": (50, 250),           # mmHg
    "dbp_median": (30, 150),           # mmHg
    "pain_median": (0, 10),            # 0–10 scale
}

# --- 3. Report irregular values ---
for col, (low, high) in valid_ranges.items():
    if col in df.columns:
        below = (df[col] < low).sum()
        above = (df[col] > high).sum()
        print(f"{col}:")
        print(f"   Below {low}: {below}")
        print(f"   Above {high}: {above}\n")

# --- 4. Cleaning ---
# Drop rows where ALL vitals are NaN (instead of any NaN)
df_cleaned = df.dropna(how="all", subset=list(valid_ranges.keys())).copy()

# Fill remaining NaNs with column median
for col in valid_ranges.keys():
    if col in df_cleaned.columns:
        df_cleaned.loc[:, col] = df_cleaned[col].fillna(df_cleaned[col].median())

# Clip values outside valid ranges
for col, (low, high) in valid_ranges.items():
    if col in df_cleaned.columns:
        df_cleaned.loc[:, col] = df_cleaned[col].clip(lower=low, upper=high)

# --- 5. Save cleaned dataset ---
df_cleaned.to_csv("cleaned_dataset.csv", index=False)
print("✅ Cleaning complete. Saved as 'cleaned_dataset.csv'")
print(f"Final shape: {df_cleaned.shape}")

# --- 6. Save cleaning log ---
with open("cleaning_report.txt", "w", encoding="utf-8") as f:
    f.write("Cleaning Report for features_mimic_ed.csv\n")
    f.write("=" * 50 + "\n\n")
    f.write("NaN values before cleaning:\n")
    f.write(str(nan_report[nan_report > 0]) + "\n\n")
    f.write("Irregular values before cleaning:\n")
    for col, (low, high) in valid_ranges.items():
        if col in df.columns:
            below = (df[col] < low).sum()
            above = (df[col] > high).sum()
            f.write(f"{col}: Below {low}: {below}, Above {high}: {above}\n")
    f.write("\n")
    f.write(f"Final dataset shape: {df_cleaned.shape}\n")

print("📝 Cleaning report saved as 'cleaning_report.txt'")
