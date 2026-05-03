# Template Layout Fix - Daily Sensor Monitoring Overview Rework (P17)

## Scope

Daily Sensor Monitoring layout refinement based on direct user feedback.

## Requested Changes

- combine `Domestic Water` and `Sakari Water` into one overview card
- remove `Sensor health snapshot`
- remove `Top issues today`
- pull daily min/avg/max sensor cards up onto the same PDF page as the overview cards

## Guardrails

- keep detailed daily sensor cards intact unless pagination/layout requires a small PDF-only adjustment
- do not change periodic behavior
- do not change anomaly logic

## Checklist

- [x] Create this active checklist
- [x] Combine Domestic Water + Sakari Water in daily overview cards
- [x] Remove daily PDF insight blocks
- [x] Rebalance daily PDF sensor pagination so overview and metric cards share the same page
- [x] Update regression checks
- [x] Render updated daily PDF review pages

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `18 passed`
- review images:
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_overview_p17/page-05.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_overview_p17/page-06.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_overview_p17/page-07.png`

## Result

- overview now merges `Domestic Water + Sakari Water`
- `Sensor health snapshot` and `Top issues today` are removed from daily PDF
- overview cards and all daily metric cards now fit before the anomaly scan page break
- contextual short sensor labels are applied in daily metric cards (`Flow`, `Pressure`, `Cooling Capacity`, `Supply Flow`, ...)
- faint row dividers and group-color metric icons are now visible in the daily detail cards
- remaining visible inconsistency: overview merges the two water groups, but detailed metric cards still remain separate
