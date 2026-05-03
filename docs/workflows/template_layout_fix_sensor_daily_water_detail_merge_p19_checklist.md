# Template Layout Fix - Daily Sensor Monitoring Water Detail Merge (P19)

## Scope

Final mini-pass to fully align the daily Sensor Monitoring detail cards with the merged overview logic.

## Requested Change

- merge `Domestic Water` and `Sakari Water` detail cards into one combined detail card
- preserve row-level distinction inside the merged card so labels stay readable

## Guardrails

- daily sensor monitoring only
- periodic behavior unchanged
- anomaly logic unchanged

## Checklist

- [x] Create this active checklist
- [x] Merge the two daily water detail groups in context
- [x] Keep row labels readable inside merged card (`Domestic Flow`, `Sakari Flow`)
- [x] Update regression checks
- [x] Render updated review pages

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `18 passed`
- review images:
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p19/page-05.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p19/page-06.png`

## Result

- daily detail cards now merge `Domestic Water` and `Sakari Water` into one card
- merged card rows stay readable as `Domestic Flow` and `Sakari Flow`
- overview and detail cards are now aligned on the same merged-water logic
- remaining mismatch: anomaly scan table still shows the original split group label (`Sakari Water`)
