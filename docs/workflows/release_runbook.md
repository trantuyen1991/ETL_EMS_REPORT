# Release Runbook

Use this runbook for quick manual release smoke checks.

Notes:
- Run from `/home/nbt/workspace/02_MySQL`
- Each command temporarily rewrites `REPORT_ANCHOR_DATE` in `config/.env`, runs production, lists matching artifacts under `output/reports/`, then restores the original `.env`
- Production entry point is `./venv/bin/python -m src.main`
- After each export run, the app also copies the current batch into `output/reports/YYYY_MM_DD/` where `YYYY_MM_DD` is the export run date in `APP_TIMEZONE`

## 1. Daily-only smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-25' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && find output/reports -maxdepth 2 -type f | sort | grep 20250625
```

Expected:
- `daily` artifacts are generated
- no `weekly` or `monthly` artifact should be created for this anchor
- expected flat files:
  - `output/reports/daily_automatic_report_daily_20250625_view.html`
  - `output/reports/daily_automatic_report_daily_20250625_pdf_source.html`
  - `output/reports/daily_automatic_report_daily_20250625.pdf`
- expected dated-copy patterns:
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250625_view.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250625_pdf_source.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250625.pdf`

## 2. Sunday smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-29' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && find output/reports -maxdepth 2 -type f | sort | grep 20250629
```

Expected:
- `daily` and `weekly` artifacts are generated
- no `monthly` artifact should be created for this anchor
- expected flat files:
  - `output/reports/daily_automatic_report_daily_20250629_view.html`
  - `output/reports/daily_automatic_report_daily_20250629_pdf_source.html`
  - `output/reports/daily_automatic_report_daily_20250629.pdf`
  - `output/reports/daily_automatic_report_weekly_20250629_view.html`
  - `output/reports/daily_automatic_report_weekly_20250629_pdf_source.html`
  - `output/reports/daily_automatic_report_weekly_20250629.pdf`
- expected dated-copy patterns:
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250629_view.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250629_pdf_source.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250629.pdf`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_weekly_20250629_view.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_weekly_20250629_pdf_source.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_weekly_20250629.pdf`

## 3. Month-end smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-05-31' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && find output/reports -maxdepth 2 -type f | sort | grep 20250531
```

Expected:
- `daily` and `monthly` artifacts are generated
- no `weekly` artifact should be created for this anchor
- expected flat files:
  - `output/reports/daily_automatic_report_daily_20250531_view.html`
  - `output/reports/daily_automatic_report_daily_20250531_pdf_source.html`
  - `output/reports/daily_automatic_report_daily_20250531.pdf`
  - `output/reports/daily_automatic_report_monthly_20250531_view.html`
  - `output/reports/daily_automatic_report_monthly_20250531_pdf_source.html`
  - `output/reports/daily_automatic_report_monthly_20250531.pdf`
- expected dated-copy patterns:
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250531_view.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250531_pdf_source.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_daily_20250531.pdf`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_monthly_20250531_view.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_monthly_20250531_pdf_source.html`
  - `output/reports/YYYY_MM_DD/daily_automatic_report_monthly_20250531.pdf`
