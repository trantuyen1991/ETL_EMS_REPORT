# Release Runbook

Use this runbook for quick manual release smoke checks.

Notes:
- Run from `/home/nbt/workspace/02_MySQL`
- Each command temporarily rewrites `REPORT_ANCHOR_DATE` in `config/.env`, runs production, lists matching artifacts in `output/reports/`, then restores the original `.env`
- Production entry point is `./venv/bin/python -m src.main`

## 1. Daily-only smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-25' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && ls -1 output/reports/*20250625*
```

Expected:
- `daily` artifacts are generated
- no `weekly` or `monthly` artifact should be created for this anchor

## 2. Sunday smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-06-29' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && ls -1 output/reports/*20250629*
```

Expected:
- `daily` and `weekly` artifacts are generated
- no `monthly` artifact should be created for this anchor

## 3. Month-end smoke

```bash
cd /home/nbt/workspace/02_MySQL && tmp=$(mktemp) && cp config/.env "$tmp" && trap 'mv "$tmp" config/.env' EXIT && ./venv/bin/python - <<'PY'
from pathlib import Path
p = Path('config/.env')
lines = p.read_text(encoding='utf-8').splitlines()
p.write_text('\n'.join('REPORT_ANCHOR_DATE=2025-05-31' if line.startswith('REPORT_ANCHOR_DATE=') else line for line in lines) + '\n', encoding='utf-8')
PY
./venv/bin/python -m src.main && ls -1 output/reports/*20250531*
```

Expected:
- `daily` and `monthly` artifacts are generated
- no `weekly` artifact should be created for this anchor
