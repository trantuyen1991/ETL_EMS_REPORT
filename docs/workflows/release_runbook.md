# Release Runbook

Use this runbook for quick manual release smoke checks.

Companion deployment guide:
- `docs/workflows/deployment_runbook.md`
- ready-made sample units: `deploy/systemd/energy-report-etl.service` and `deploy/systemd/energy-report-etl.timer`
- one-command installer helper: `deploy/systemd/install_systemd_units.sh`

Notes:
- Run from `/home/nbt/workspace/02_MySQL`
- Each command temporarily rewrites `REPORT_ANCHOR_DATE` in `config/.env`, runs production, lists matching artifacts under the configured `OUTPUT_DIR`, then restores the original `.env`
- Production entry point is `./venv/bin/python -m src.main`
- Canonical artifacts now write directly into `OUTPUT_DIR/YYYY_MM/` grouped by artifact type
- When `PRINT_STAGING_DIR` is blank, runtime stages temporary print files under `OUTPUT_DIR/_staging/`
- After a successful run, runtime removes current-batch staging files and prunes an empty `_staging/` folder
- Period sort prefixes are:
  - `01_monthly`
  - `02_weekly`
  - `03_daily`

## 1. Daily-only smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-25' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && output_dir=$(awk -F= '/^OUTPUT_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && output_dir=${output_dir:-output/reports} && staging_dir=$(awk -F= '/^PRINT_STAGING_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && staging_dir=${staging_dir:-${output_dir%/}/_staging} && find "$output_dir" -path "$staging_dir" -prune -o -type f -print | sort | grep 20250625
```

Expected:
- `daily` artifacts are generated
- no `weekly` or `monthly` artifact should be created for this anchor
- expected files:
  - `<OUTPUT_DIR>/2025_06/view_html/03_daily_energy_automatic_report_20250625.html`
  - `<OUTPUT_DIR>/2025_06/pdf_source_html/03_daily_energy_automatic_report_20250625.html`
  - `<OUTPUT_DIR>/2025_06/pdf/03_daily_energy_automatic_report_20250625.pdf`
  - `<OUTPUT_DIR>/2025_06/excel/03_daily_energy_automatic_report_20250625.xlsx`

## 2. Sunday smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-29' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && output_dir=$(awk -F= '/^OUTPUT_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && output_dir=${output_dir:-output/reports} && staging_dir=$(awk -F= '/^PRINT_STAGING_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && staging_dir=${staging_dir:-${output_dir%/}/_staging} && find "$output_dir" -path "$staging_dir" -prune -o -type f -print | sort | grep 20250629
```

Expected:
- `daily` and `weekly` artifacts are generated
- no `monthly` artifact should be created for this anchor
- expected files:
  - `<OUTPUT_DIR>/2025_06/view_html/02_weekly_energy_automatic_report_20250629.html`
  - `<OUTPUT_DIR>/2025_06/pdf_source_html/02_weekly_energy_automatic_report_20250629.html`
  - `<OUTPUT_DIR>/2025_06/pdf/02_weekly_energy_automatic_report_20250629.pdf`
  - `<OUTPUT_DIR>/2025_06/view_html/03_daily_energy_automatic_report_20250629.html`
  - `<OUTPUT_DIR>/2025_06/pdf_source_html/03_daily_energy_automatic_report_20250629.html`
  - `<OUTPUT_DIR>/2025_06/pdf/03_daily_energy_automatic_report_20250629.pdf`
  - `<OUTPUT_DIR>/2025_06/excel/03_daily_energy_automatic_report_20250629.xlsx`

## 3. Month-end smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-05-31' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && output_dir=$(awk -F= '/^OUTPUT_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && output_dir=${output_dir:-output/reports} && staging_dir=$(awk -F= '/^PRINT_STAGING_DIR=/{print substr($0,index($0,"=")+1)}' config/.env) && staging_dir=${staging_dir:-${output_dir%/}/_staging} && find "$output_dir" -path "$staging_dir" -prune -o -type f -print | sort | grep 20250531
```

Expected:
- `daily` and `monthly` artifacts are generated
- no `weekly` artifact should be created for this anchor
- expected files:
  - `<OUTPUT_DIR>/2025_05/view_html/01_monthly_energy_automatic_report_20250531.html`
  - `<OUTPUT_DIR>/2025_05/pdf_source_html/01_monthly_energy_automatic_report_20250531.html`
  - `<OUTPUT_DIR>/2025_05/pdf/01_monthly_energy_automatic_report_20250531.pdf`
  - `<OUTPUT_DIR>/2025_05/view_html/03_daily_energy_automatic_report_20250531.html`
  - `<OUTPUT_DIR>/2025_05/pdf_source_html/03_daily_energy_automatic_report_20250531.html`
  - `<OUTPUT_DIR>/2025_05/pdf/03_daily_energy_automatic_report_20250531.pdf`
  - `<OUTPUT_DIR>/2025_05/excel/03_daily_energy_automatic_report_20250531.xlsx`
