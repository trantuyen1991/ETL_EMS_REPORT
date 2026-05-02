# Template Layout Fix Checklist

## Slice: Electricity weekly PDF page 2 detail-table style + width cleanup P5

### Goal
Fix the weekly `Daily Energy Detail` issues raised in review:
- cell fill / color treatment looks worse than the daily version
- the first meter column can feel crowded by the date column in some rows

- [x] Identify the exact weekly PDF table/template hooks for style and column sizing
- [x] Apply a PDF-only cleanup for periodic detail cell palette and column widths
- [x] Re-render weekly PDF sample (`2025-06-29`) and capture the updated page 2 image
- Observed result:
  - periodic detail cell fills now read closer to the daily table palette and feel less visually harsh
  - the date column no longer crowds the first meter column in the reviewed weekly page
  - remaining emphasis on the first few highlighted cells is acceptable and no longer a layout problem
- [x] Update checklist/findings, test if needed, then commit and mine the slice
