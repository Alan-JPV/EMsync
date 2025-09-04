#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Quality check script for preprocessed ICU dataset.
- Summarizes rows, columns, dtypes
- Counts NaNs per column
- Reports columns with >50% missing values
- Saves a report file (qc_report.txt by default)
"""

import argparse
import os
import pandas as pd

def log(msg: str):
    print(f"[QC] {msg}", flush=True)

def main():
    ap = argparse.ArgumentParser(description="Quality check for preprocessed ICU dataset")
    ap.add_argument("--input", required=True, help="Path to preprocessed dataset (.csv or .parquet)")
    ap.add_argument("--out_report", default="qc_report.txt", help="Path to save QC report (txt)")
    args = ap.parse_args()

    # Load dataset
    log(f"Loading dataset: {args.input}")
    if args.input.endswith(".csv"):
        df = pd.read_csv(args.input, low_memory=False)
    else:
        df = pd.read_parquet(args.input)

    # Start report
    report_lines = []
    report_lines.append(f"Dataset: {args.input}")
    report_lines.append(f"Rows: {len(df)}")
    report_lines.append(f"Columns: {len(df.columns)}\n")

    # Column dtypes
    report_lines.append("Column types:")
    report_lines.append(str(df.dtypes))
    report_lines.append("")

    # Missing values
    na_counts = df.isna().sum()
    report_lines.append("Missing values per column:")
    report_lines.append(str(na_counts[na_counts > 0]))
    report_lines.append("")

    # High missingness columns
    high_na = (na_counts / len(df)) * 100
    high_na = high_na[high_na > 50]
    if not high_na.empty:
        report_lines.append("⚠️ Columns with >50% missing values:")
        report_lines.append(str(high_na))
    else:
        report_lines.append("No columns with >50% missing values.")

    # Save report
    with open(args.out_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    log(f"QC report saved to {args.out_report}")

if __name__ == "__main__":
    main()
