# Template Layout Fix - Daily View Sensor Metric Table (P10)

## Scope

Convert the **daily view** `Sensor Monitoring` group cards from the current range-card presentation into a compact metric-table card layout that matches the approved reference direction.

## Guardrails

- daily HTML view only for this slice
- no PDF changes yet
- no business-rule or anomaly-scoring changes
- no group ordering changes
- keep existing min / avg / max / alert data bindings

## Audit Findings

- Current sensor group cards are rendered in `src/templates/report/view/sections/utility.html` under `.utility-sensor-group-grid`.
- Each sensor row currently uses a range-track layout:
  - name + submeta
  - alert flag pill
  - range line + avg dot
  - `Min / Avg / Max` stacked values
  - optional tolerance note
  - optional anomaly reason
- Existing backend context in `src/services/utility_service.py` already provides the needed fields for a table-like layout:
  - `display_name`
  - `measurement_type_label`
  - `min_display`
  - `avg_display`
  - `max_display`
  - `flag_summary`
  - `flag_detail_summary`
  - `severity_class`
  - `severity_label`
- This slice is presentation-only unless a missing display field is discovered during implementation.

## Checklist

- [x] Audit current sensor monitoring markup, CSS, and available data fields
- [x] Create this active checklist
- [x] Refactor daily view sensor group markup into compact metric-table cards
- [x] Replace range-track styling with table-like card styling in `report.css`
- [x] Add/adjust regression coverage for the new daily-view structure
- [x] Render daily view sample and capture review image
- [x] Summarize findings for user review before any PDF port

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py` → `12 passed`
- `./venv/bin/pytest -q` → `52 passed`
- Daily render anchor: `2025-06-25`
- Review image:
  - `/home/nbt/.openclaw/workspace/audit/render_review_sensor_p10/slice_3.png`

## Review Notes

- Daily `Sensor Monitoring` now renders group cards as compact metric-table cards.
- New visual structure is present only in the daily HTML view for this slice.
- Periodic view and PDF remain unchanged for now.
- Initial render looks structurally correct; remaining judgment is mainly about density/readability tuning from the user side.
