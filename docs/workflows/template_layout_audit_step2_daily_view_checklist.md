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
- [ ] Inspect section spacing and visual balance
- [ ] Check for oversized charts, label collisions, and awkward empty states
- [ ] Check whether tables/cards overflow or feel too compressed on desktop view
- [ ] Record findings by section + probable source template/block
- [ ] If clean, explicitly mark no-finding areas

## Findings
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
- KPI daily view audit remains pending as the next slice.
