"""Normalize platform exports, compute KPIs, flag anomalies, and write an Excel report.

Usage:
    python src/pipeline.py --config config/columns.yaml --input-dir data/raw --output reports/weekly.xlsx
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

CANONICAL = ["date", "campaign", "spend", "impressions", "clicks", "conversions"]


def load_mapping(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize(df: pd.DataFrame, mapping: dict, platform: str) -> pd.DataFrame:
    """Rename platform columns to canonical names and add a platform column.

    Raises a clear error if a required column is missing from the export.
    """
    cols = mapping[platform]
    missing = [cols[k] for k in CANONICAL if cols[k] not in df.columns]
    if missing:
        raise ValueError(f"{platform} export is missing columns: {missing}")
    out = df.rename(columns={cols[k]: k for k in CANONICAL})[CANONICAL].copy()
    out["platform"] = platform
    for col in ["spend", "impressions", "clicks", "conversions"]:
        out[col] = pd.to_numeric(out[col].astype(str).str.replace(",", "").str.replace("$", ""), errors="coerce").fillna(0)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    return out.dropna(subset=["date"])


def add_kpis(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    imp = out["impressions"].replace(0, np.nan)
    conv = out["conversions"].replace(0, np.nan)
    clk = out["clicks"].replace(0, np.nan)
    out["ctr"] = out["clicks"] / imp
    out["cpm"] = out["spend"] / imp * 1000
    out["cpc"] = out["spend"] / clk
    out["cpa"] = out["spend"] / conv
    return out


def flag_anomalies(df: pd.DataFrame, window: int = 14, threshold: float = 3.0) -> pd.DataFrame:
    """Flag days where spend-per-day deviates from the trailing baseline by more than `threshold` std devs."""
    out = []
    for (platform, campaign), g in df.sort_values("date").groupby(["platform", "campaign"]):
        g = g.copy()
        base = g["spend"].shift(1).rolling(window, min_periods=7)
        g["spend_z"] = (g["spend"] - base.mean()) / base.std()
        g["anomaly"] = g["spend_z"].abs() > threshold
        out.append(g)
    return pd.concat(out).reset_index(drop=True)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    s = df.groupby("platform").agg(
        spend=("spend", "sum"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("conversions", "sum"),
    )
    s["ctr"] = s["clicks"] / s["impressions"]
    s["cpm"] = s["spend"] / s["impressions"] * 1000
    s["cpa"] = s["spend"] / s["conversions"]
    return s.round(4).reset_index()


def run(config_path: Path, input_dir: Path, output: Path) -> pd.DataFrame:
    mapping = load_mapping(config_path)
    frames = []
    for platform in mapping:
        files = sorted(input_dir.glob(f"{platform}_*.csv"))
        for f in files:
            frames.append(normalize(pd.read_csv(f), mapping, platform))
    if not frames:
        raise FileNotFoundError(f"No platform CSVs found in {input_dir}")
    df = add_kpis(pd.concat(frames, ignore_index=True))
    df = flag_anomalies(df)

    output.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output, engine="openpyxl") as xl:
        summarize(df).to_excel(xl, sheet_name="Summary", index=False)
        df.to_excel(xl, sheet_name="Daily", index=False)
        df.loc[df["anomaly"], ["date", "platform", "campaign", "spend", "spend_z"]].to_excel(
            xl, sheet_name="Anomalies", index=False)
    return df


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--input-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    df = run(args.config, args.input_dir, args.output)
    print(f"Wrote {args.output} with {len(df)} rows")


if __name__ == "__main__":
    main()
