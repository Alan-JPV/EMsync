# quality_check.py
import pandas as pd
import matplotlib.pyplot as plt

# Load preprocessed dataset
print("Loading dataset...")
df = pd.read_csv("cleaned_dataset.csv")
print("Shape:", df.shape)

# === Sanity check ranges ===
valid_ranges = {
    "heartrate_median": (20, 250),
    "resprate_median": (5, 60),
    "o2sat_median": (50, 100),
    "temperature_median": (25, 45),
    "sbp_median": (50, 250),
    "dbp_median": (30, 150),
    "pain_median": (0, 10),
}

report_lines = []
report_lines.append(f"Dataset shape BEFORE cleaning: {df.shape}\n")

# Outlier removal
for col, (low, high) in valid_ranges.items():
    if col in df.columns:
        before = df.shape[0]
        df = df[(df[col].isna()) | ((df[col] >= low) & (df[col] <= high))]
        after = df.shape[0]
        removed = before - after
        report_lines.append(f"{col}: kept values in [{low}, {high}], removed {removed} rows")

report_lines.append(f"\nDataset shape AFTER cleaning: {df.shape}")
report_lines.append("\n✅ Cleaned dataset saved as features_mimic_ed_clean.csv")

# Save cleaned dataset
df.to_csv("features_mimic_ed_clean.csv", index=False)

# Save report (UTF-8 encoding so ✅ works)
with open("quality_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

# === Plot distributions for all key vitals ===
for col in valid_ranges.keys():
    if col in df.columns:
        plt.figure()
        plt.hist(df[col].dropna(), bins=50)
        plt.title(f"Distribution of {col} (CLEANED)")
        plt.xlabel(col)
        plt.ylabel("Count")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.show()

print("✔ Quality check, cleaning, and plots complete. Report saved to quality_report.txt")
