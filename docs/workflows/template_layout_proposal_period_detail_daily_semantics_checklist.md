# Template Layout Proposal Checklist

## Proposal: inherit Daily color semantics into Period detail tables

### Goal
Align weekly/monthly `Daily Energy Detail` visual semantics with the daily template, while keeping the current periodic table structure and column order.

### Keep as-is
- [x] Keep daily layout as 3-column single-day vertical detail
- [x] Keep periodic layout as multi-day table split across multiple parts/pages
- [x] Keep periodic meter column order as-is
- [x] Do not inherit daily value-based sorting into periodic tables

### In-scope visual inheritance
- [x] Reuse daily-like color hierarchy for periodic detail cells:
  - zero values
  - low/mid/high heat levels
  - row-max emphasis
- [x] Reuse daily-like contrast balance so highlighted cells feel softer and more readable
- [x] Keep periodic area theme accents (`accent_color`, `accent_tint`, `header_bg`) intact

### Out of scope
- [x] No sorting changes for weekly/monthly meter columns
- [x] No business-logic changes in energy calculation
- [x] No restructuring of periodic detail pagination flow
- [x] No attempt to convert periodic tables into daily-style value-bar columns

### Likely touch points
- [x] `src/services/energy_service.py`
  - shared semantic source already exists and should remain unchanged
  - current contract is reusable as-is: `value-zero`, `heat-1..4`, `is_row_max`
- [x] `src/services/report_builder_service.py`
  - daily and periodic builders already share the same cell semantics
  - the intentional difference is only presentation: daily sorts one-day entries, periodic keeps stable multi-day columns
- [x] `src/templates/assets/report.css`
  - confirmed as the daily visual reference for tone and emphasis
- [x] `src/templates/assets/report_pdf_base.css`
  - confirmed as the periodic default layer that currently diverges in presentation
- [x] `src/templates/assets/report_pdf.css`
  - remains the right PDF-only override layer for final alignment
- [x] `src/templates/report/pdf/sections/electricity.html`
  - periodic table structure should stay unchanged; only styling hooks should evolve

### Step 1 findings: exact daily visual rules worth inheriting
- [x] Keep the current backend semantic tiers unchanged:
  - `value-zero` means explicit zero-value rendering
  - `heat-1 .. heat-4` means increasing intensity relative to the row max
  - `is_row_max` means the strongest cell in the row/day
- [x] Preserve area theming as the base color source:
  - `detail-accent-color`
  - `detail-accent-tint`
  - `detail-head-bg`
  - `detail-soft-bg`
  - `detail-strong-bg`
- [x] Reuse the daily contrast hierarchy rather than the daily layout:
  - neutral/default rows stay white
  - `heat-1` uses a soft background only
  - `heat-2` and `heat-3` use accent-tint-led soft gradients
  - `heat-4` uses the strongest area-tinted fill but should still fade into white instead of becoming a hard block
- [x] Reuse daily text emphasis rules:
  - normal numeric text stays readable and dark enough against tinted fills
  - `value-zero` should be visibly de-emphasized
  - `is_row_max` should stand out through stronger weight/color, not through a heavy border artifact
- [x] Do not inherit daily-only value-bar mechanics:
  - no `fill_pct`
  - no `electricity-daily-value-bar-fill`
  - no per-entry ranked vertical cards
- [x] Do not inherit daily ordering behavior:
  - daily sorts by one-day value for readability
  - periodic keeps fixed meter-column order for cross-day comparison

### Step 1 output: implementation constraints for the next slice
- [x] Period detail should feel like the same product family as daily through tone and emphasis only
- [x] Period detail must remain a stable matrix, not a ranked card layout
- [x] Preferred inheritance path is CSS/token alignment, not backend logic change
- [ ] Step 2: map current periodic rules that differ only in presentation
- [ ] Step 3: align periodic PDF palette and emphasis to daily semantics without touching sorting
- [ ] Step 4: re-render weekly and monthly samples to confirm no regression in readability or pagination

### Done when
- [ ] Period detail colors feel like the same product family as daily detail
- [ ] Weekly/monthly tables keep stable column comparison across days
- [ ] No new crowding/pagination regression is introduced
- [ ] Sorting behavior remains unchanged from current periodic behavior
