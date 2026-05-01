# Template Layout Audit Master Checklist

## Goal
Audit every primary report template/surface for layout quality and PDF pagination behavior.

## Audit rules
For each audited surface/section, check:
- [ ] Layout is visually balanced
- [ ] No page has excessive unused whitespace without reason
- [ ] No oversized chart pushes a small remainder of a table onto the next page
- [ ] No chart label/value text collides with y-axis or chart frame
- [ ] If chart labels are too wide, prefer:
  - increase left/right padding
  - shorten value labels using `k` for thousands when appropriate
- [ ] No table content overflows outside the page/card
- [ ] If a table is too wide, compress lower-priority columns first
- [ ] Record exact file/block and proposed fix before editing

## Audit scenarios
- [x] Daily-only anchor: `2025-06-25`
- [ ] Sunday anchor (daily + weekly): `2025-06-29`
- [ ] Month-end anchor (daily + monthly): `2025-05-31`

## Surface order
### Step 1. Daily PDF layout audit
- [x] `src/templates/report/pdf/report_pdf_daily.html`
- [x] `src/templates/report/pdf/sections/header_daily.html`
- [x] `src/templates/report/pdf/sections/electricity.html`
- [x] `src/templates/report/pdf/sections/utility.html`
- [x] `src/templates/report/pdf/sections/kpi.html`
- [x] `src/templates/report/pdf/sections/footer.html`

### Step 2. Daily view layout audit
- [ ] `src/templates/report/view/report_view_daily.html`
- [ ] `src/templates/report/view/sections/header_daily.html`
- [ ] `src/templates/report/view/sections/electricity.html`
- [ ] `src/templates/report/view/sections/utility.html`
- [ ] `src/templates/report/view/sections/kpi.html`
- [ ] `src/templates/report/view/sections/footer.html`

### Step 3. Weekly PDF layout audit
- [ ] `src/templates/report/pdf/report_pdf_periodic.html`
- [ ] `src/templates/report/pdf/sections/header_periodic.html`
- [ ] `src/templates/report/pdf/sections/electricity.html`
- [ ] `src/templates/report/pdf/sections/utility.html`
- [ ] `src/templates/report/pdf/sections/kpi.html`
- [ ] `src/templates/report/pdf/sections/footer.html`

### Step 4. Weekly view layout audit
- [ ] `src/templates/report/view/report_view_periodic.html`
- [ ] `src/templates/report/view/sections/header_periodic.html`
- [ ] `src/templates/report/view/sections/electricity.html`
- [ ] `src/templates/report/view/sections/utility.html`
- [ ] `src/templates/report/view/sections/kpi.html`
- [ ] `src/templates/report/view/sections/footer.html`

### Step 5. Monthly PDF layout audit
- [ ] Re-check periodic PDF with month-end output pages
- [ ] Focus on sections with longer tables/charts under monthly density

### Step 6. Monthly view layout audit
- [ ] Re-check periodic view with month-end output
- [ ] Focus on overflow, label crowding, and card balance

## Deliverables per step
- [ ] Checklist updated with findings
- [ ] Findings doc/checkpoint committed
- [ ] Findings mined to MemPalace
- [ ] Approved fixes executed in narrow slices
