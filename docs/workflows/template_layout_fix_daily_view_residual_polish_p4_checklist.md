# Template Layout Fix Checklist

## Slice: Daily view residual polish P4

### Goal
Apply a very small residual polish pass to the remaining sparse daily view visuals only:
- electricity `Area comparison`
- the two daily `Utility comparison` charts
- KPI daily empty-state panels

- [x] Identify the smallest safe CSS/template hooks for the 3 remaining sparse visuals
- [x] Apply the residual polish without changing business logic or chart data
- [x] Re-render daily view sample (`2025-06-25`) and capture the updated view screenshot
- Observed result:
  - electricity area comparison reads more intentional in sparse/near-empty state
  - the two utility comparison charts look less malformed and more deliberately compact
  - KPI empty-state panels read more clearly as designed placeholders
- [x] Run tests and commit the slice with `AGENTS.md` included as requested
