#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Preprocess MIMIC-IV ICU data for Intervention/Resource Prediction.
Creates per-stay features (first N hours) and multi-label targets:
- ventilation_needed
- vasopressors_needed
- dialysis_needed
- transfusion_needed
"""

import argparse
import os
import sys
import re
import pandas as pd
import numpy as np
from typing import Optional, Set

# ----------------------------- Utils ---------------------------------

def log(msg: str):
    print(f"[EMSync] {msg}", flush=True)

def find_csv(data_dir: str, filename: str) -> Optional[str]:
    candidates = []
    base = os.path.join(data_dir, filename)
    candidates.append(base)
    if not filename.endswith(".gz"):
        candidates.append(base + ".gz")
    if filename.endswith(".csv"):
        candidates.append(os.path.join(data_dir, filename[:-4]))
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def read_csv_fast(path, usecols=None, parse_dates=None, chunksize=None):
    kwargs = dict(low_memory=False, compression="infer")
    try:
        kwargs["dtype_backend"] = "pyarrow"
    except TypeError:
        pass
    return pd.read_csv(path, usecols=usecols, parse_dates=parse_dates,
                       chunksize=chunksize, **kwargs)

def normalize_str(s: pd.Series) -> pd.Series:
    return s.astype("string").str.lower().str.replace(r"\s+", " ", regex=True)

# ----------------------- Keyword Dictionaries ------------------------

PRESSOR_KEYWORDS = [
    "norepinephrine","noradrenaline","epinephrine","adrenaline",
    "phenylephrine","vasopressin","dopamine","dobutamine","milrinone"
]

TRANSFUSION_KEYWORDS = [
    "packed red blood","prbc","rbc","red cell","platelet","plts",
    "fresh frozen plasma","ffp","plasma","cryoprecipitate","cryo"
]

DIALYSIS_KEYWORDS = [
    "dialysis","hemodialysis","crrt","cvvh","cvvhd","cvvhdf",
    "renal replacement","ultrafiltration"
]

VENT_PROC_KEYWORDS = [
    "intubation","endotracheal","tracheostomy","mechanical ventilation"
]

VITAL_PATTERNS = {
    "hr": r"(^| )heart rate($| )",
    "resp_rate": r"(^| )resp(irat| )?e( rate)?($| )",
    "spo2": r"(oximetry|o2 saturation|spo2)",
    "temp_c": r"(temperature( \(celsius\))?|temperature c)",
    "sbp": r"(non ?invasive|arterial).*systolic.*blood pressure|sbp",
    "dbp": r"(non ?invasive|arterial).*diastolic.*blood pressure|dbp",
    "mbp": r"(non ?invasive|arterial).*mean.*blood pressure|map|mbp",
}

VENT_ITEM_PATTERNS = {
    "fio2": r"\bfio2\b|fraction of inspired oxygen",
    "peep": r"\bpeep\b",
    "vent_mode": r"vent(ilator)? mode|vent mode",
    "tv": r"tidal volume",
    "set_rate": r"(set )?rate( control)?",
    "minute_vent": r"minute ventilation",
    "o2_device": r"o(xygen)? (delivery )?device|ventilator",
}

# ----------------------------- Loaders ----------------------------------

def get_args():
    ap = argparse.ArgumentParser(description="MIMIC-IV ICU preprocessing for interventions/resources.")
    ap.add_argument("--data_dir", required=True, help="Folder containing ICU CSV files.")
    ap.add_argument("--out_path", default="icu_interventions.csv", help="Output file (.csv or .parquet).")
    ap.add_argument("--window_hours", type=float, default=6.0, help="Feature window from ICU intime (hours).")
    ap.add_argument("--chunksize", type=int, default=1_000_000, help="Chunk size for chartevents.")
    return ap.parse_args()

def load_icustays(data_dir):
    path = find_csv(data_dir, "icustays.csv")
    if path is None:
        log("ERROR: icustays.csv(.gz) not found.")
        sys.exit(1)
    usecols = ["subject_id","hadm_id","stay_id","first_careunit","intime","outtime"]
    df = read_csv_fast(path, usecols=usecols, parse_dates=["intime","outtime"])
    df = df.dropna(subset=["stay_id","intime"])
    return df

def try_load(file, data_dir, parse_dates=None):
    path = find_csv(data_dir, file)
    if path is not None:
        log(f"Loading {os.path.basename(path)} ...")
        return read_csv_fast(path, parse_dates=parse_dates)
    log(f"WARNING: {file} not found -> skipping features/labels that depend on it.")
    return None

def try_load_d_items(data_dir):
    path = find_csv(data_dir, "d_items.csv")
    if path is not None:
        d = read_csv_fast(path)
        if "label" in d.columns:
            d["clean_label"] = normalize_str(d["label"])
        else:
            d["clean_label"] = pd.Series(dtype="string")
        return d
    return None

def map_itemids(d_items, linksto: str, pattern: str) -> Set[int]:
    if d_items is None: return set()
    m = d_items
    if "linksto" in m.columns:
        m = m[m["linksto"]==linksto]
    return set(m.loc[m["clean_label"].str.contains(pattern, na=False, regex=True), "itemid"].astype(int))

def collect_itemid_map(d_items):
    item_map = {}
    for k,pat in VITAL_PATTERNS.items():
        item_map[k] = map_itemids(d_items, "chartevents", pat)
    vent_union = set()
    for k,pat in VENT_ITEM_PATTERNS.items():
        s = map_itemids(d_items, "chartevents", pat)
        item_map[f"vent_{k}"] = s
        vent_union |= s
    item_map["vent_any"] = vent_union
    return item_map

# ----------------------------- Features ----------------------------------

def make_vitals_features_chartevents(icustays, data_dir, item_map, window_hours, chunksize):
    path = find_csv(data_dir, "chartevents.csv")
    if path is None or len(item_map)==0:
        log("Skipping chartevents vitals.")
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")

    need_itemids = set().union(*[v for k,v in item_map.items() if not k.startswith("vent_") and k!="vent_any"])
    if not need_itemids:
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")

    keep_cols = ["stay_id","itemid","charttime","valuenum"]
    agg_list = []

    for i, chunk in enumerate(read_csv_fast(path, usecols=keep_cols, parse_dates=["charttime"], chunksize=chunksize), start=1):
        chunk = chunk[chunk["itemid"].isin(need_itemids)]
        if chunk.empty: continue
        c = chunk.merge(icustays[["stay_id","intime"]], on="stay_id", how="inner")
        mask = (c["charttime"] >= c["intime"]) & (c["charttime"] <= (c["intime"] + pd.to_timedelta(window_hours, unit="h")))
        c = c[mask]
        if c.empty: continue
        def id_to_var(iid: int):
            for name, ids in item_map.items():
                if name.startswith("vent_") or name=="vent_any":
                    continue
                if iid in ids:
                    return name
            return None
        c["var"] = c["itemid"].map(id_to_var)
        c = c.dropna(subset=["var","valuenum"])
        g = c.groupby(["stay_id","var"])["valuenum"].agg(["mean","min","max"]).reset_index()
        agg_list.append(g)
        if i % 5 == 0:
            log(f"  processed {i} chunks...")

    if not agg_list:
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")

    vit = pd.concat(agg_list, ignore_index=True)
    vit = vit.groupby(["stay_id","var"]).agg({"mean":"mean","min":"min","max":"max"}).reset_index()
    vit = vit.pivot(index="stay_id", columns="var", values=["mean","min","max"])
    vit.columns = [f"{stat}_{var}" for stat,var in vit.columns]
    vit = vit.groupby(level=0).first()
    return vit

def make_early_features_from_prescriptions(icustays, prescriptions, window_hours):
    if prescriptions is None:
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")
    df = prescriptions.copy()
    for col in ["drug"]:
        if col in df.columns:
            df[col] = normalize_str(df[col])
    merged = df.merge(icustays[["stay_id","hadm_id","intime","outtime"]], on="hadm_id", how="inner")
    s = pd.to_datetime(merged.get("starttime", merged["intime"]), errors="coerce")
    e = pd.to_datetime(merged.get("stoptime", merged["outtime"]), errors="coerce")
    early_end = merged["intime"] + pd.to_timedelta(window_hours, unit="h")
    mask = (s < early_end) & (e >= merged["intime"])
    early = merged[mask].copy()

    def has_kw(series: pd.Series, kws):
        return series.fillna("").str.contains("|".join([re.escape(k) for k in kws]), case=False, regex=True)

    feats = (
        early.assign(
            antibiotics=lambda x: has_kw(x["drug"], ["penicillin","cef","meropenem","vancomycin"]),
            sedatives=lambda x: has_kw(x["drug"], ["propofol","midazolam","lorazepam","dexmedetomidine"]),
            opioids=lambda x: has_kw(x["drug"], ["fentanyl","morphine","hydromorphone","oxycodone"])
        )
        .groupby("stay_id")[["antibiotics","sedatives","opioids"]]
        .any()
        .astype(int)
    )
    return feats

def make_early_features_from_inputevents(icustays, inputevents, window_hours):
    if inputevents is None:
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")
    df = inputevents.copy()
    if "starttime" in df.columns:
        t = pd.to_datetime(df["starttime"], errors="coerce")
    elif "storetime" in df.columns:
        t = pd.to_datetime(df["storetime"], errors="coerce")
    else:
        return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")
    df = df.merge(icustays[["stay_id","intime"]], on="stay_id", how="inner")
    mask = (t >= df["intime"]) & (t <= df["intime"] + pd.to_timedelta(window_hours, unit="h"))
    df = df[mask]
    if "amount" in df.columns:
        fluids = df.groupby("stay_id")["amount"].sum(min_count=1).rename("fluids_total")
        return fluids.to_frame()
    return pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")

# ----------------------------- Labels ----------------------------------

def build_labels(icustays, prescriptions, procedureevents, d_items, item_map):
    y = pd.DataFrame({"stay_id": icustays["stay_id"].values}).set_index("stay_id")

    # Vasopressors
    if prescriptions is not None and "drug" in prescriptions.columns:
        pr = prescriptions.merge(icu[["stay_id","hadm_id"]], on="hadm_id", how="inner")
        pr["drug"] = normalize_str(pr["drug"])
        press = pr["drug"].str.contains("|".join(PRESSOR_KEYWORDS), case=False, na=False)
        y["vasopressors_needed"] = pr[press].groupby("stay_id").size().reindex(y.index, fill_value=0).gt(0).astype(int)
    else:
        y["vasopressors_needed"] = 0

    # Transfusion
    if prescriptions is not None and "drug" in prescriptions.columns:
        pr = prescriptions.merge(icu[["stay_id","hadm_id"]], on="hadm_id", how="inner")
        pr["drug"] = normalize_str(pr["drug"])
        transf = pr["drug"].str.contains("|".join(TRANSFUSION_KEYWORDS), case=False, na=False)
        y["transfusion_needed"] = pr[transf].groupby("stay_id").size().reindex(y.index, fill_value=0).gt(0).astype(int)
    else:
        y["transfusion_needed"] = 0

    # Dialysis
    if procedureevents is not None:
        pe = procedureevents.merge(icu[["stay_id"]], on="stay_id", how="inner")
        text_cols = ["ordercategoryname","ordercategorydescription","value"]
        text = pd.Series("", index=pe.index, dtype="string")
        for c in text_cols:
            if c in pe.columns:
                text += " " + normalize_str(pe[c])
        dial = text.str.contains("|".join(DIALYSIS_KEYWORDS), na=False)
        y["dialysis_needed"] = pe[dial].groupby("stay_id").size().reindex(y.index, fill_value=0).gt(0).astype(int)
    else:
        y["dialysis_needed"] = 0

    # Ventilation (from procedures)
    if procedureevents is not None:
        pe = procedureevents.merge(icu[["stay_id"]], on="stay_id", how="inner")
        text_cols = ["ordercategoryname","ordercategorydescription","value"]
        text = pd.Series("", index=pe.index, dtype="string")
        for c in text_cols:
            if c in pe.columns:
                text += " " + normalize_str(pe[c])
        vent = text.str.contains("|".join(VENT_PROC_KEYWORDS), na=False)
        y["ventilation_needed"] = pe[vent].groupby("stay_id").size().reindex(y.index, fill_value=0).gt(0).astype(int)
    else:
        y["ventilation_needed"] = 0

    return y

# ----------------------------- Main ----------------------------------

def main():
    args = get_args()
    data_dir = args.data_dir
    out_path = args.out_path
    window_h = args.window_hours
    chunksize = args.chunksize

    pd.options.mode.copy_on_write = True

    global icu
    icu = load_icustays(data_dir)

    d_items = try_load_d_items(data_dir)
    prescriptions   = try_load("prescriptions.csv",   data_dir, parse_dates=["starttime","stoptime"])
    procedureevents = try_load("procedureevents.csv", data_dir, parse_dates=["starttime","endtime"])
    inputevents     = try_load("inputevents.csv",     data_dir, parse_dates=["starttime","endtime","storetime"])

    item_map = collect_itemid_map(d_items) if d_items is not None else {}

    # Features
    feats = []
    feats.append(make_vitals_features_chartevents(icu, data_dir, item_map, window_h, chunksize))
    feats.append(make_early_features_from_prescriptions(icu, prescriptions, window_h))
    feats.append(make_early_features_from_inputevents(icu, inputevents, window_h))
    care = pd.get_dummies(icu["first_careunit"], prefix="unit", dummy_na=True)
    care.index = icu["stay_id"]
    feats.append(care)
    X = pd.DataFrame(index=icu["stay_id"])
    for f in feats:
        if f is not None and not f.empty:
            X = X.join(f, how="left")

    # Labels
    Y = build_labels(icu, prescriptions, procedureevents, d_items, item_map)

    df = X.join(Y, how="left").reset_index()

    # Save
    if out_path.lower().endswith(".csv"):
        df.to_csv(out_path, index=False)
    else:
        df.to_parquet(out_path, index=False)

    log(f"Saved dataset: {out_path}")
    log(f"Rows: {len(df)}, Columns: {len(df.columns)}")

if __name__ == "__main__":
    main()
