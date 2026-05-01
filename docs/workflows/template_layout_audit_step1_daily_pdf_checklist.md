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
- [ ] Render daily-only PDF sample for anchor `2025-06-25`
- [ ] Inspect every PDF page for whitespace / pagination balance
- [ ] Check whether any chart is too tall and pushes a small table fragment to the next page
- [ ] Check whether chart labels collide with y-axis or frame
- [ ] Check whether any table content overflows page/card width
- [ ] Record findings by page + section + probable source template/block
- [ ] If clean, explicitly mark no-finding areas

## Findings
- Pending
