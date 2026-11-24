import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from pipeline import add_kpis, load_mapping, normalize, run  # noqa: E402


@pytest.fixture
def mapping():
    return load_mapping(ROOT / "config" / "columns.yaml")


def test_normalize_renames_meta_columns(mapping):
    raw = pd.DataFrame({
        "Reporting starts": ["2026-03-01"],
        "Campaign name": ["X"],
        "Amount spent (USD)": ["1,250.50"],
        "Impressions": ["10,000"],
        "Link clicks": [120],
        "Results": [5],
    })
    out = normalize(raw, mapping, "meta")
    assert out.loc[0, "spend"] == pytest.approx(1250.50)
    assert out.loc[0, "impressions"] == 10000
    assert out.loc[0, "platform"] == "meta"


def test_normalize_raises_on_missing_column(mapping):
    raw = pd.DataFrame({"Date": ["2026-03-01"]})
    with pytest.raises(ValueError, match="missing columns"):
        normalize(raw, mapping, "tiktok")


def test_kpis_handle_zero_conversions():
    df = pd.DataFrame({"spend": [100.0], "impressions": [5000], "clicks": [50], "conversions": [0]})
    out = add_kpis(df)
    assert pd.isna(out.loc[0, "cpa"])
    assert out.loc[0, "ctr"] == pytest.approx(0.01)


def test_end_to_end_writes_excel(tmp_path):
    import subprocess

    subprocess.run([sys.executable, str(ROOT / "src" / "make_sample_data.py")], check=True)
    out = tmp_path / "report.xlsx"
    df = run(ROOT / "config" / "columns.yaml", ROOT / "data" / "raw", out)
    assert out.exists()
    assert set(df["platform"]) == {"meta", "tiktok", "google"}
    sheets = pd.ExcelFile(out).sheet_names
    assert sheets == ["Summary", "Daily", "Anomalies"]
