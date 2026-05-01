# Template Layout Fix Checklist

## Slice: Electricity daily PDF page 1-2 balance fix P2

### Goal
Improve daily PDF page 1-2 balance in the electricity section by reducing excess whitespace and making the Top 10 block start more intentionally.

- [x] Recall electricity page 1-2 finding from MemPalace
- [x] Inspect electricity PDF blocks that control chart/card/table footprint
- [x] Apply the smallest safe layout adjustment for daily PDF electricity
- [x] Re-render daily PDF sample (`2025-06-25`) and verify page 1-2 balance
- [x] Update checklist/findings, commit, and mine the slice

## Result
- Root cause for the awkward page 1 ending was the empty Top 10 block: the sample had a rendered Top 10 header/table shell with no body rows.
- Fix applied: the PDF electricity template now skips the Top 10 section when `sections.electricity.top10.grouped_rows` is empty.
- Result: page 1 now ends cleanly after the overview charts, and page 2 starts directly with `Daily Energy Detail`.
- Remaining note: page 1 and page 2 still have some whitespace because this sample is sparse/zero-heavy, but the whitespace now reads as normal breathing room instead of an obvious layout bug.
