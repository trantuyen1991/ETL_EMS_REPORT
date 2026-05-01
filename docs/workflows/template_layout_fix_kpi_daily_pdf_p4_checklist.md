# Template Layout Fix Checklist

## Slice: KPI daily PDF page 8 polish P4

### Goal
Improve the final KPI page density and polish in the daily PDF after sensor-page compaction moved KPI onto page 8.

- [x] Recall KPI page finding from audit context
- [x] Inspect KPI PDF layout blocks and chart config that drive page height / label polish
- [x] Apply the smallest safe KPI page density and label adjustments
- [x] Re-render daily PDF sample (`2025-06-25`) and capture the fixed page image

## Current direction
- First KPI pass tightened card/chart/table spacing and shortened waterfall x-axis labels.
- Second KPI pass adds compact empty-state rendering for zero-only daily KPI charts, so empty frames do not dominate the last page.
- [x] Update checklist/findings, commit, and mine the slice

## Result
- Page 8 improved materially for the zero-data daily KPI scenario.
- Empty KPI charts are now replaced by compact explanatory empty-state panels in the PDF.
- Waterfall labels are shorter (`Yesterday`, `Energy`, `Prod.`, `Today`) and zero-only variance labels are suppressed.
- Remaining whitespace still exists below the summary matrix, but the page now reads as intentional and user-ready rather than broken.
