"""Create sample platform exports in the three different column formats.

All values are random and for demonstration only.
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "raw"


def make(platform: str, columns: dict, seed: int):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-03-01", periods=60, freq="D")
    rows = []
    for campaign in [f"{platform.upper()}_PROSPECT_A", f"{platform.upper()}_PROSPECT_B"]:
        for d in dates:
            spend = float(max(rng.normal(250, 30), 20))
            imp = int(spend * 1000 / rng.uniform(6, 12))
            clk = int(imp * rng.uniform(0.008, 0.02))
            conv = int(clk * rng.uniform(0.03, 0.07))
            rows.append({
                columns["date"]: d.strftime("%Y-%m-%d"),
                columns["campaign"]: campaign,
                columns["spend"]: f"{spend:.2f}",
                columns["impressions"]: f"{imp:,}",
                columns["clicks"]: clk,
                columns["conversions"]: conv,
            })
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / f"{platform}_2026-03.csv", index=False)


if __name__ == "__main__":
    import yaml

    with open(Path(__file__).resolve().parent.parent / "config" / "columns.yaml", encoding="utf-8") as f:
        mapping = yaml.safe_load(f)
    for i, platform in enumerate(mapping):
        make(platform, mapping[platform], seed=i + 1)
    print("Sample exports written to", OUT)
