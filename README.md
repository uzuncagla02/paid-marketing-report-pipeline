# Paid Marketing Report Pipeline

A config-driven Python pipeline that takes exports from Meta, TikTok and Google Ads (each with different column names), normalizes them into one schema, calculates KPIs, flags unusual spend days, and writes an Excel report.

> **Data note:** The sample CSVs are generated randomly. They are not real campaign data.

## Why it exists
Each ad platform names the same metric differently: "Amount spent", "Cost", and so on. A weekly report often means manual copying and fixing. This pipeline moves the differences into one config file (`config/columns.yaml`), so adding a platform means adding a few lines, not changing code.

## What it does
1. **Normalize:** Renames platform-specific columns to a shared schema. Cleans numbers with commas and currency symbols. Raises a clear error when a column is missing from an export.
2. **KPIs:** CTR, CPM, CPC and CPA. Division by zero produces empty values, not crashes.
3. **Anomalies:** Flags days where a campaign's spend deviates from its 14-day trailing baseline by more than 3 standard deviations.
4. **Report:** An Excel workbook with three sheets: `Summary`, `Daily` and `Anomalies`.

## Structure
```
config/columns.yaml          # column mapping per platform
src/pipeline.py              # normalize, KPIs, anomalies, Excel output (CLI)
src/make_sample_data.py      # creates sample exports in three different formats
tests/test_pipeline.py       # unit tests and an end-to-end run
```

## Run
```bash
pip install pandas numpy openpyxl pyyaml pytest
python src/make_sample_data.py
python src/pipeline.py --config config/columns.yaml --input-dir data/raw --output reports/weekly.xlsx
pytest tests/
```

## Extending
To add a platform, add its column names under a new key in `config/columns.yaml` and name its export file `platform_*.csv`.
