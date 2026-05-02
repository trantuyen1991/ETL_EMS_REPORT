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
  - section: Utility Overview
  - block: right-side `Consumption delta (%)` comparison chart
  - symptom: horizontal bars, long labels, and percentage text are overcrowded/overlapping, especially on the dominant positive bar near the bottom
  - likely cause: chart label/axis spacing is too tight for weekly data density in the periodic utility PDF chart container
- No-finding pages for this pass:
  - Page 10: sensor anomaly card grid looks balanced
  - Page 13: KPI continuation/footer page is sparse but visually stable
