# Template Layout Audit Checklist

## Step 1: Daily PDF layout audit

### Scope
- `src/templates/report/pdf/report_pdf_daily.html`
- `src/templates/report/pdf/sections/header_daily.html`
- `src/templates/report/pdf/sections/electricity.html`
- `src/templates/report/pdf/sections/utility.html`
- `src/templates/report/pdf/sections/kpi.html`
- `src/templates/report/pdf/sections/footer.html`

### Audit targets
- [x] Render daily-only PDF sample for anchor `2025-06-25`
- [x] Inspect every PDF page for whitespace / pagination balance
- [x] Check whether any chart is too tall and pushes a small table fragment to the next page
- [x] Check whether chart labels collide with y-axis or frame
- [x] Check whether any table content overflows page/card width
- [x] Record findings by page + section + probable source template/block
- [x] If clean, explicitly mark no-finding areas

## Findings

### Page 1, Electricity Consumption / Top 10 Meter Consumption
- Initial issue: bottom whitespace and weak page balance because page 1 ended with an empty Top 10 block shell.
- Root cause confirmed in rendered HTML: `sections.electricity.top10.grouped_rows` was empty for this sample, but the PDF template still rendered the Top 10 heading/table shell.
- Likely source: `src/templates/report/pdf/sections/electricity.html`
- Status: resolved by the follow-up fix slice tracked in `docs/workflows/template_layout_fix_electricity_daily_pdf_p2_checklist.md`.
- Minor label density issue still remains: some tiny `0.0` labels sit too close to the baseline in the area comparison chart.

### Page 2, Daily Energy Detail / DIODE Daily Energy Detail
- Initial state had very large whitespace in the lower half of the page.
- Status after page 1 fix: transition is cleaner because page 2 now starts directly with `Daily Energy Detail` instead of being preceded by an empty Top 10 shell on page 1.
- Remaining whitespace is acceptable for this sparse sample and no overflow was found.

### Page 3, ICO Daily Energy Detail / SAKARI Daily Energy Detail
- Bottom whitespace exists but is still acceptable.
- No immediate overflow or collision found.

### Page 4-5, Utility Overview / Utility Detail Summary
- Strongest issue found in the initial daily PDF audit.
- Initial state: page 4 charts were too tall relative to the remaining table height.
- Initial result: only the last row of `Utility Detail Summary` spilled to page 5, leaving severe whitespace.
- Likely source: `src/templates/report/pdf/sections/utility.html`
- Status: resolved by the follow-up fix slice tracked in `docs/workflows/template_layout_fix_utility_daily_pdf_p1_checklist.md`.

### Page 6-8, Sensor Monitoring
- Pages 6-8 are underfilled overall, especially page 7 and page 8.
- No obvious overflow.
- Likely source: sensor-monitoring blocks/macros referenced from the PDF report flow.
- Proposed fix direction:
  - audit card min-heights, grid spacing, and page-break behavior for sensor blocks after electricity/utility balancing.

### Page 8, Sensor anomaly scan
- Large whitespace below the anomaly table.
- Reason column is tight but still within page width.

### Page 9, Energy KPI / KPI Summary Matrix
- Overall page use is acceptable.
- `Deviation vs yesterday` chart has too much internal empty space when values are near zero.
- Small `0.0` labels cluster near the baseline in KPI charts.
- Waterfall x-axis label wrapping is awkward (`Yesterday\nKPI`, `Today\nKPI`) and hurts polish.
- Likely source: `src/templates/report/pdf/sections/kpi.html` and related KPI chart config in `report_builder_service.py`

### No overflow findings in step 1
- No table/text block was observed spilling outside the card/page width in the audited daily PDF sample.
