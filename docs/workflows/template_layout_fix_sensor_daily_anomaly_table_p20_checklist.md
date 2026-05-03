# Template Layout Fix - Daily Sensor Monitoring Anomaly Table (P20)

## Scope

Final daily PDF anomaly-scan cleanup based on direct review feedback.

## Requested Changes

- move `Group` column before `Sensor`
- shorten sensor names in anomaly scan
- narrow numeric columns to widen the final `Reason` column
- try to keep the anomaly table on the same page as the cards without ugly row wrapping

## Guardrails

- daily PDF only
- keep periodic anomaly table behavior unchanged unless the shared markup absolutely requires a harmless column-order update
- no anomaly-rule logic changes

## Checklist

- [x] Create this active checklist
- [x] Update daily anomaly context labels
- [x] Update anomaly table column order and cell hooks
- [x] Compact PDF anomaly table widths and spacing
- [x] Render updated daily PDF review pages

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `18 passed`
- review images:
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p20/page-05.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p20/page-06.png`

## Result

- `Group` now appears before `Sensor`
- anomaly sensor names are shortened to match card context better (`Sakari Flow`, `Cooling Capacity`, `Supply Flow`, ...)
- numeric columns are tighter and the final `Reason` column is wider
- anomaly table now moves up onto the same page as the sensor cards
- remaining visible issue: the first merged-water row still feels crowded between `Group` and `Sensor`
