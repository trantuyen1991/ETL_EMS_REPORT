# Template Layout Fix Checklist

## Slice: Utility daily PDF pagination fix P1

### Goal
Pull the full `Utility Detail Summary` table back onto the same PDF page as the utility charts in the daily report, by reducing chart/spacing footprint before changing table structure.

- [x] Recall utility pagination finding from MemPalace
- [x] Inspect utility PDF layout blocks that control chart height and page spacing
- [x] Apply the smallest safe layout reduction for the daily PDF utility section
- [x] Re-render daily PDF sample (`2025-06-25`) and verify page 4-5 pagination
- [x] Update checklist/findings, commit, and mine the slice

## Result
- Success: page 4 now contains the full `Utility Detail Summary` table.
- Success: page 5 no longer starts with a leftover utility table fragment and now starts cleanly with the next section.
- Follow-up finding: later pages remain somewhat underfilled, especially around the next section start, but that is a separate pagination/layout slice.
