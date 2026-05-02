# Template Layout Fix Checklist

## Slice: Utility weekly PDF page 8 donut label fix P1

### Goal
Fix the strongest weekly PDF layout issue first: page 8 `Utility Distribution (This Week)` donut chart, where percentage labels are clipped/crowded under weekly PDF density.

- [x] Identify the exact periodic utility PDF chart block and CSS controls
- [x] Apply the smallest safe fix for weekly PDF label/axis spacing
- [x] Re-render weekly PDF sample (`2025-06-29`) and capture the updated page 8 image
- Observed result:
  - donut label crowding improved materially
  - chart and legend spacing feel more balanced
  - a small amount of edge-tightness still remains on some left-side percentage labels
- [x] Update checklist/findings, test if needed, then commit and mine the slice
