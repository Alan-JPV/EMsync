# qc_report.py
import pandas as pd
import argparse

def main():
    parser = argparse.ArgumentParser(description="Quality check for the preprocessed dataset.")
    parser.add_argument("--input", required=True, help="Path to the dataset file to check.")
    parser.add_argument("--output", default="qc_report.txt", help="Name of the output report file.")
    args = parser.parse_args()

    print(f"--- Running Quality Check on: {args.input} ---")

    try:
        data = pd.read_csv(args.input)
    except FileNotFoundError:
        print(f"❌ ERROR: Input file not found at '{args.input}'. Please check the filename.")
        return

    # --- Generate the Report ---
    with open(args.output, "w") as f:
        f.write(f"Quality Check Report for: {args.input}\n")
        f.write("="*50 + "\n\n")

        # Shape
        f.write(f"Shape: {data.shape[0]} rows, {data.shape[1]} columns\n\n")

        # Data Types
        f.write("Column Data Types:\n")
        f.write(str(data.dtypes) + "\n\n")

        # Missing Values
        missing_values = data.isna().sum()
        missing_values = missing_values[missing_values > 0].sort_values(ascending=False)
        
        if not missing_values.empty:
            f.write("Missing Values per Column (Count):\n")
            f.write(str(missing_values) + "\n\n")
            
            missing_percent = (data.isna().sum() / len(data) * 100)
            missing_percent = missing_percent[missing_percent > 0].sort_values(ascending=False)
            f.write("Missing Values per Column (Percentage):\n")
            f.write(str(missing_percent.round(2)) + "%\n\n")
        else:
            f.write("No missing values found.\n\n")

    print(f"✅ Quality check complete. Report saved to '{args.output}'.")

if __name__ == "__main__":
    main()