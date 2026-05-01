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
- User feedback accepted:
  - page 7 is good enough
  - page 6 should prefer adding meaningful sensor information over further visual compression
- Follow-up direction: audit a page-6 enrichment block instead of shrinking the no-data tiles further.
- Approved enrichment direction: add `Sensor health snapshot` + `Top issues today` preview for the daily PDF overview page.
- Implementation scope confirmed by user: build both blocks for page 6 daily PDF and re-render page 6 for review.
- Split scope confirmed by user: pull the first sensor-group row onto page 5, then continue remaining groups + anomaly scan on page 6.
- Follow-up approved by user: split daily sensor group section so the first row renders on page 5 and the remaining groups continue on page 6 with the anomaly table.
- Enrichment applied:
  - `Sensor health snapshot`
  - `Top issues today` preview
- Split applied:
  - first sensor-group row now renders on page 5
  - remaining groups continue on page 6 with the anomaly scan
- Observed result:
  - page 5 improved materially and feels more complete
  - page 6 now has a more useful middle layer between the overview cards and the detailed sensor groups
  - page 6 remains balanced, though slightly denser in the lower half
- Tradeoff note: when the failure mode is uniformly `Missing data`, the page becomes slightly repetitive, but it is still more valuable than leaving the space empty.
- [x] Re-render daily PDF sample (`2025-06-25`) and capture the fixed page image
- [x] Update checklist/findings, commit, and mine the slice
