# Template Layout Fix - Daily PDF Sensor Inner Row Rework (P16)

## Scope

A focused PDF-only refinement pass that follows the approved target more closely by reworking the **inside of each sensor card**.

## Targeted Problems

- inner rows still feel like stacked report text instead of compact sensor modules
- `Min / Avg / Max` values do not scan as one tight value cluster yet
- icon + color treatment inside rows is still weaker than the target

## Slice Goal

Make each PDF sensor entry read closer to the target card style:
- metric title with unit integrated
- one stronger compact value cluster for `Min / Avg / Max`
- simpler two-line left column
- clearer icon / color hierarchy

## Guardrails

- daily PDF only
- no page-strategy rewrite in this slice unless required by the row rework
- no business logic changes

## Checklist

- [x] Create this active checklist
- [x] Rework PDF sensor row structure toward a tighter module pattern
- [x] Tighten `Min / Avg / Max` cluster scanability
- [x] Tune icon and status color treatment toward target
- [x] Run focused regression tests
- [x] Render updated PDF pages 6-7 for review

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `18 passed`
- Review pages:
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p16/page-06.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p16/page-07.png`

## Current Assessment

- inner card content is materially tighter and more module-like than P15
- biggest improvement: metric rows now read as repeatable units instead of loose stacked text
- biggest remaining mismatch: internal vertical spacing is still a bit too open compared with the target
