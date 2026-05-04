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
- [x] Sunday anchor (daily + weekly): `2025-06-29`
- [ ] Month-end anchor (daily + monthly): `2025-05-31`

## Surface order
### Step 1. Daily PDF layout audit
- [x] `src/templates/report/pdf/report_pdf_daily.html`
- [x] `src/templates/report/pdf/sections/header_daily.html`
- [x] `src/templates/report/pdf/sections/electricity.html`
- [x] `src/templates/report/pdf/sections/utility.html`
- [x] `src/templates/report/pdf/sections/kpi.html`
- [x] `src/templates/report/pdf/sections/footer.html`
- [x] Checkpoint closed and accepted as-is
- Durable summary:
  - utility page 4-5 pagination was rebalanced
  - empty electricity Top 10 shell was removed from PDF output
  - KPI zero-data pages now use explicit empty-state panels
  - daily Sensor Monitoring PDF was reworked target-first into grouped metric-table cards
  - all daily sensor detail cards now fit before the anomaly scan block
  - overview cards now merge `Domestic Water + Sakari Water`, while the anomaly scan keeps split water group labels for readability
  - the daily anomaly scan now uses `Group -> Sensor -> Type -> Latest -> Min -> Avg -> Max -> Reason` with compact numeric columns and a wider final reason column

### Step 2. Daily view layout audit
- [x] `src/templates/report/view/report_view_daily.html`
- [x] `src/templates/report/view/sections/header_daily.html`
- [x] `src/templates/report/view/sections/electricity.html`
- [x] `src/templates/report/view/sections/utility.html`
- [x] `src/templates/report/view/sections/kpi.html`
- [x] `src/templates/report/view/sections/footer.html`
- [x] Checkpoint closed after residual polish
- Durable summary:
  - electricity and utility chart/card spacing was tightened for the daily view family
  - daily KPI empty-state treatment was promoted into the view template
  - remaining sparse panels were compacted so low-activity days still read intentionally
  - daily Sensor Monitoring now uses compact grouped metric-table cards with icon-rich headers and context-shortened sensor labels

### Step 3. Weekly PDF layout audit
- [x] `src/templates/report/pdf/report_pdf_periodic.html`
- [x] `src/templates/report/pdf/sections/header_periodic.html`
- [x] `src/templates/report/pdf/sections/electricity.html`
- [x] `src/templates/report/pdf/sections/utility.html`
- [x] `src/templates/report/pdf/sections/kpi.html`
- [x] `src/templates/report/pdf/sections/footer.html`
- [x] Checkpoint closed and accepted for the approved current slice
- Progress to date:
  - P1: utility distribution donut label crowding reduced to acceptable PDF quality
  - P2: lone trailing weekly sensor trend card now spans full width
  - P3: utility deviation readability improved by simplifying PDF axis labeling
  - P4: periodic detail-table underline artifacts were reduced
  - P5+: periodic detail date/meter crowding and daily-vs-period visual semantics were improved without changing matrix structure
  - final electricity weekly pass keeps `DIODE Part 1/7` with `Daily Energy Summary`, then paginates the remaining detail blocks across 3 pages at 5 tables/page
  - final utility weekly pass removes the duplicate `This Week mix` beside the heatmap, keeps one retained mix beside `Utility Energy Trend (7 Days)`, and promotes the heatmap row to full width
  - final sensor-monitoring weekly pass keeps the anomaly page isolated and the detail continuation at 2 tables/page
  - final review used native page PNGs because stitched Telegram preview images created false size-perception drift

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
- [x] Checklist updated with findings
- [x] Findings doc/checkpoint committed
- [x] Findings mined to MemPalace
- [x] Approved fixes executed in narrow slices
