# Template Layout Fix Checklist

## Slice: KPI daily view empty-state + chart footprint polish P3

### Goal
Improve the daily KPI view by tightening chart footprint and making near-empty states feel more intentional without changing KPI business logic.

- [x] Identify KPI daily view CSS/template blocks that drive empty-state presentation and chart height
- [x] Apply the smallest safe KPI daily view polish
- [x] Re-render daily view sample (`2025-06-25`) and capture the updated view screenshot
- Observed result:
  - KPI chart footprint is materially tighter
  - zero/near-zero KPI charts now fall back to explicit empty-state panels in daily view
  - empty-state presentation is clearer than before, but still visually subtle when the whole section is near-empty
- [x] Update checklist/findings, commit, and mine the slice
