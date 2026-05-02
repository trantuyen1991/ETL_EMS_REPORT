# Template Layout Fix Checklist

## Slice: Electricity weekly PDF page 2 detail-table artifact fix P4

### Goal
Fix the next strongest weekly PDF presentation issue: page 2 `DIODE Daily Energy Detail (Part 1/7)` shows dark underline-like artifacts inside highlighted numeric cells.

- [x] Identify the exact weekly PDF block and safest presentation-only lever
- [x] Apply a PDF-only fix for periodic detail cell highlight rendering
- [x] Re-render weekly PDF sample (`2025-06-29`) and capture the updated page 2 image
- Observed result:
  - the dark underline-like artifacts in highlighted `DIODE Daily Energy Detail` cells were materially reduced
  - the original heavy black marks are no longer prominent
  - faint highlight remnants may still exist in a few cells, but they are now minor and acceptable for RC review
- [x] Update checklist/findings, test if needed, then commit and mine the slice
