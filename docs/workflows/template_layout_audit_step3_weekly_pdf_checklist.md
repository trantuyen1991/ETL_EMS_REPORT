# Template Layout Audit Checklist

## Step 3: Weekly PDF layout audit

### Scope
- `src/templates/report/pdf/report_pdf_periodic.html`
- `src/templates/report/pdf/sections/header_periodic.html`
- `src/templates/report/pdf/sections/electricity.html`
- `src/templates/report/pdf/sections/utility.html`
- `src/templates/report/pdf/sections/kpi.html`
- `src/templates/report/pdf/sections/footer.html`

### Audit targets
- [x] Render Sunday sample for anchor `2025-06-29`
- [x] Convert weekly PDF pages to PNG for page-by-page audit
- [x] Inspect pagination balance, chart density, and table overflow
- [x] Record strongest first issue by page + source block
- [x] If clean, explicitly mark no-finding areas

## Findings
- Rendered weekly PDF sample: `output/reports/daily_automatic_report_weekly_20250629.pdf`
- Weekly PDF page count in first-pass audit: 13 pages
- Strongest first issue:
  - Page 8
  - section: Utility Energy Overview
  - block: `Utility Distribution (This Week)` donut chart
  - symptom: percentage labels around the donut are clipped/crowded near the chart boundary
  - likely cause: donut radius/center/font-size are too aggressive for weekly PDF card width
- Step 3 fix P1 result:
  - weekly PDF page 8 donut label crowding reduced to acceptable RC quality
  - final fix used compact PDF-only donut geometry plus smaller in-slice labels
  - follow-up polish is optional, not blocking
- Step 3 fix P2 result:
  - weekly PDF page 9 trailing `Sensor daily average trend` card now spans full width
  - page balance improved materially without changing data or section order
  - remaining sparseness is acceptable and comes from low data density
- No-finding pages for this pass:
  - Page 10: sensor anomaly card grid looks balanced
  - Page 13: KPI continuation/footer page is sparse but visually stable
