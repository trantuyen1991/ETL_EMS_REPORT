# Template Layout Fix - Daily View Sensor Final Polish (P13)

## Scope

Final daily-view-only polish pass for `Sensor Monitoring` before any PDF port.

## User-Approved Targets

- increase row spacing slightly
- reduce the visual weight of the secondary status/note treatment
- make the anomaly table below feel lighter and less heavy

## Guardrails

- daily HTML view only
- no PDF changes yet
- no periodic view changes yet
- no anomaly-rule or data-logic changes

## Checklist

- [x] Create this active checklist
- [x] Increase grouped-card row spacing and breathing room
- [x] Reduce secondary note emphasis without removing key meaning
- [x] Lighten anomaly table styling in daily view
- [x] Run focused regression tests
- [x] Render updated daily sample and capture review image
- [x] Summarize readiness before PDF port

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `17 passed`
- Initial implementation anchor: `2025-06-25`
- Better layout-review anchor selected after comparison: `2025-05-31`
- Review images:
  - `/home/nbt/.openclaw/workspace/audit/render_review_sensor_p13/daily_view_20250625_sensor_metric_table_p13_focus.png`
  - `/home/nbt/.openclaw/workspace/audit/render_review_sensor_anchor_compare/20250531_focus.png`

## Result Summary

- grouped sensor-card rows have slightly more breathing room
- secondary note treatment is lighter and no longer competes with the main metric label
- the anomaly table reads lighter and less block-heavy than P12
- `2025-05-31` is the better fairness anchor for visual review because it has `18/18 sensors active` and less misleading missing-data noise than `2025-06-25`
- daily view is now good enough to move on to PDF alignment, with only minor later polish if needed
