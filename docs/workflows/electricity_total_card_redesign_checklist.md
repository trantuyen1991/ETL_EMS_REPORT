# Electricity Total Card Redesign Checklist

## Purpose

Redesign the Electricity summary-card surface so the report keeps:
- one primary `TOTAL` card for plant
- one standalone `DIODE` card
- one composite `ICO + SAKARI` card

The composite card must let the reader see, at one glance:
- `ICO` area total
- `SAKARI` area total
- combined `ICO + SAKARI` total

## Business Intent

The customer does not want to manually add `ICO` and `SAKARI` when reading the report.

This is a display and readability enhancement.

It must not change the source-of-truth rule:
- Electricity official totals still come from `total_energy`
- backend detail tables and source rows must remain available

## Scope

Apply to both:
- daily template family
- periodic template family

Render surfaces to review:
- HTML view
- PDF render

Likely touch points:
- `src/services/report_builder_service.py`
- `src/templates/report/view/sections/electricity.html`
- `src/templates/report/pdf/sections/electricity.html`
- `src/templates/assets/report.css`
- `src/templates/assets/report_pdf_base.css`
- `src/templates/assets/report_pdf.css`

## Target Card Layout

### Keep
- `TOTAL` card remains the strongest visual card
- `DIODE` remains a standalone area card

### Replace
- replace separate standalone `ICO` and `SAKARI` cards with one composite card

### Composite Card Content

The composite card should present 3 columns or sub-blocks:
1. `ICO`
2. `SAKARI`
3. `ICO + SAKARI`

Each sub-block should keep the same quick-read semantics where possible:
- current
- previous
- delta
- delta %
- meter active / total where meaningful

## Safety Rules

- do not change Electricity source logic away from `total_energy`
- do not remove backend detail builders
- do not silently change Top 10, chart, or daily summary logic unless required by the new card layout
- preserve Plant card hierarchy
- verify PDF width and height stability before claiming done

## Delivery Plan

### Checkpoint 1: spec and docs
- [ ] create task checklist
- [ ] update report spec with target Electricity card layout
- [ ] commit docs checkpoint
- [ ] mine project memory

### Checkpoint 2: backend/view-model prep
- [ ] add a composite-card payload for `ICO + SAKARI`
- [ ] keep existing raw area summary fields available during transition
- [ ] validate no logic regression in totals/comparison values

### Checkpoint 3: HTML view layout
- [ ] render `TOTAL`
- [ ] render standalone `DIODE`
- [ ] render composite `ICO + SAKARI`
- [ ] tune width hierarchy and spacing

### Checkpoint 4: PDF layout
- [ ] port the composite layout to PDF template
- [ ] tune PDF-safe spacing, wrapping, and column balance
- [ ] check daily and periodic variants

### Checkpoint 5: validation and docs sync
- [ ] validate template syntax
- [ ] generate sample daily output
- [ ] generate sample periodic output
- [ ] visually review HTML and PDF
- [ ] update reader-facing/technical docs if the final UI wording changes
- [ ] commit stable checkpoint
- [ ] mine again

## Validation Focus

Pay extra attention to:
- PDF line wrapping in the composite card
- title clarity for the combined total, prefer `ICO + SAKARI` over ambiguous `TOTAL`
- whether Plant and DIODE should shrink only slightly, not aggressively
- whether meter counts in the composite card should be shown per sub-block and/or combined
