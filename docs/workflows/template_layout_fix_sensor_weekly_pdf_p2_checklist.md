# Template Layout Fix Checklist

## Slice: Sensor weekly PDF page 9 trend layout fix P2

### Goal
Fix the next strongest weekly PDF layout issue: page 9 `Sensor Monitoring` block where the lower `Sensor daily average trend` chart sits alone on the left and leaves a large empty area to the right.

- [x] Identify the exact weekly PDF block and the lowest-risk layout lever
- [x] Apply a PDF-only layout fix for the lone trailing sensor trend card
- [x] Re-render weekly PDF sample (`2025-06-29`) and capture the updated page 9 image
- Observed result:
  - the lower `Sensor daily average trend` chart now expands to full content width
  - the section reads as an intentional two-chart stack instead of one full-width chart plus one awkward half-width leftover card
  - remaining sparseness is data-density related, not a layout break
- [x] Update checklist/findings, test if needed, then commit and mine the slice
