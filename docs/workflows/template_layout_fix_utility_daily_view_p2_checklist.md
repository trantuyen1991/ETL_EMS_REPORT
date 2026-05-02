# Template Layout Fix Checklist

## Slice: Utility daily view spacing + chart height fix P2

### Goal
Tighten the daily view utility section by reducing excess vertical spacing and oversized chart height before changing data structure or fallback behavior.

- [x] Identify utility daily view CSS/template blocks that drive spacing and chart height
- [x] Apply the smallest safe utility daily view layout reduction
- [x] Re-render daily view sample (`2025-06-25`) and capture the updated view screenshot
- Observed result:
  - utility section is materially tighter and more even vertically
  - daily deviation and comparison charts consume less height without changing data structure
  - the two utility comparison charts still feel sparse when one dominant bar drives the whole chart
- [x] Update checklist/findings, commit, and mine the slice
