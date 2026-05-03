# Template Layout Fix - Daily PDF Sensor Card Port (P14)

## Scope

Port the approved daily-view `Sensor Monitoring` grouped card layout into the **daily PDF** surface.

## Goals

- preserve the approved grouped-card visual language from daily HTML view
- keep the PDF layout A4-safe and page-break-aware
- avoid reintroducing heavy range-track cards for daily PDF
- keep the existing daily PDF sensor overview/health/anomaly content unless a narrow PDF-safe reduction is needed

## Guardrails

- daily PDF only
- no periodic PDF changes in this slice
- no business-logic or anomaly-rule changes
- prefer template/CSS changes over backend changes unless a layout hook is strictly required

## Checklist

- [x] Create this active checklist
- [x] Audit current daily PDF sensor block and pagination constraints
- [x] Port grouped sensor cards into the daily PDF template
- [x] Add PDF-safe styling for grouped sensor cards in `report_pdf.css`
- [x] Update regression coverage for daily PDF sensor template/CSS hooks
- [x] Render daily PDF and capture page review image
- [x] Summarize readiness / residual issues after the PDF port

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `18 passed`
- `./venv/bin/pytest -q` → `53 passed`
- Daily PDF render anchor: `2025-05-31`
- PDF pages extracted for review under:
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p14/page-06.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p14/page-07.png`
  - `/home/nbt/.openclaw/workspace/audit/daily_pdf_sensor_p14/page-08.png`

## Result Summary

- daily PDF now uses the grouped sensor-card layout instead of the old range-track cards
- `Domestic Water` and `Sakari Water` remain split as separate cards in PDF
- `Sakari Water` spans full width in the PDF grid as intended
- current PDF sample is readable and A4-safe for the chosen anchor
- main residual issue is density/text size in larger cards, not clipping or broken pagination
