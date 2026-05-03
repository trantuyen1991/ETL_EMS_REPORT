# Template Layout Fix - Daily PDF Sensor Card Rework (P15)

## Trigger

The first PDF port (P14) is technically working, but visually fails against the approved target.

## Failure Summary

- typography is too small and dense
- cards still feel like compressed report blocks, not target sensor cards
- table columns are too tight for A4 at the current scale
- the current PDF layout was over-optimized for fitting, not for matching the desired sensor-card design
- this needs a real rework, not a micro-polish

## New Direction

Rebuild the **daily PDF sensor cards** target-first for A4 readability:

- stronger title/icon hierarchy
- larger metric typography
- roomier rows
- simpler status treatment
- less compressed per-card density
- preserve separate `Domestic Water` / `Sakari Water`
- keep `Sakari Water` full-width only if it still helps the print layout after rework

## Guardrails

- daily PDF only
- no periodic PDF changes
- no business logic changes
- prefer PDF-specific template/CSS hooks rather than weakening the approved daily HTML view

## Checklist

- [x] Create this active checklist
- [ ] Rework PDF sensor card layout around A4 readability first
- [ ] Rebalance grid/card density for page 6-7
- [ ] Update regression checks for the reworked PDF hooks
- [ ] Render new PDF sample and capture page review images
- [ ] Summarize whether the PDF now matches the target direction closely enough
