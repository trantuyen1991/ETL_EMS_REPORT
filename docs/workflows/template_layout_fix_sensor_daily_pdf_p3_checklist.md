# Template Layout Fix Checklist

## Slice: Sensor monitoring daily PDF layout fix P3

### Goal
Improve underfilled sensor monitoring pages in the daily PDF, one page at a time, starting from the earliest page with the clearest layout win.

- [x] Recall sensor-monitoring finding from MemPalace
- [x] Re-audit daily PDF pages 6-8 and map sections to template blocks
- [x] Pick the first page to fix and apply the smallest safe layout adjustment

## First target
- Page 7 is the first page to fix.
- Reason: it has the clearest large blank lower half, caused by sparse sensor group detail cards using a tall layout.
- Planned direction: densify the daily sensor group/card layout before changing data content or adding new sections.

## Interim result
- First pass applied: daily sensor group cards switched to a denser 3-column layout with tighter card spacing.
- Observed result: total daily PDF page count dropped from 9 to 8 pages.
- Page 7 improved materially because the anomaly table moved up earlier and the large blank lower half was reduced.
- Second pass applied: daily no-data sensor tiles were compacted in the PDF template.
- Observed result: page 6 density improved materially while page 7 and page 8 remained stable.
- Follow-up still needed: the tiny explanatory line in the compact no-data tiles is near the lower limit of comfortable print readability, so later refinement may simplify that copy instead of shrinking layout further.
- [x] Re-render daily PDF sample (`2025-06-25`) and capture the fixed page image
- [x] Update checklist/findings, commit, and mine the slice
