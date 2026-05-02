# Template Layout Fix Checklist

## Slice: Utility weekly PDF page 7 deviation chart fix P3

### Goal
Fix the next strongest weekly PDF layout issue: page 7 `Consumption delta (%)` chart where bottom labels and axis text feel crowded under weekly density.

- [x] Identify the exact weekly PDF block and lowest-risk presentation lever
- [x] Apply a PDF-only readability fix for the periodic utility deviation chart
- [x] Re-render weekly PDF sample (`2025-06-29`) and capture the updated page 7 image
- Observed result:
  - first pass (smaller typography + taller chart) did not materially improve the real culprit
  - revised pass removed bottom PDF x-axis tick labels, which reduced clutter materially because the bar-end percentage labels already carry the key numeric reading
  - a small amount of left-side category-label tightness remains, but the chart is now acceptable for RC review
- [x] Update checklist/findings, test if needed, then commit and mine the slice
