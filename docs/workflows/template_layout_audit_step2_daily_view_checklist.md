# Template Layout Audit Checklist

## Step 2: Daily view layout audit

### Scope
- `src/templates/report/view/report_view_daily.html`
- `src/templates/report/view/sections/header_daily.html`
- `src/templates/report/view/sections/electricity.html`
- `src/templates/report/view/sections/utility.html`
- `src/templates/report/view/sections/kpi.html`
- `src/templates/report/view/sections/footer.html`

### Audit targets
- [x] Render daily view sample for anchor `2025-06-25`
- [x] Inspect section spacing and visual balance
- [x] Check for oversized charts, label collisions, and awkward empty states
- [x] Check whether tables/cards overflow or feel too compressed on desktop view
- [x] Record findings by section + probable source template/block
- [x] If clean, explicitly mark no-finding areas

## Findings
- Header/footer:
  - no layout issue worth changing in this slice
- Electricity slice P1 completed:
  - tightened daily electricity chart spacing
  - reduced daily electricity chart heights
  - tightened spacing before Top 10 and Daily Energy Summary blocks
- Remaining electricity issue:
  - `Area comparison` still feels too empty when near-zero values dominate
- Utility slice P2 completed:
  - tightened utility block spacing
  - reduced daily utility chart heights
  - tightened overview/detail spacing in the lower half
- Remaining utility issue:
  - the two `Utility comparison` charts still feel visually sparse when one dominant bar drives the scale
- KPI slice P3 completed:
  - reduced daily KPI chart height and tightened dashboard spacing
  - added explicit empty-state panels for zero/near-zero daily KPI charts in view mode
- Remaining KPI issue:
  - empty-state panels are clearer now, but still visually subtle when the whole KPI section is near-empty
