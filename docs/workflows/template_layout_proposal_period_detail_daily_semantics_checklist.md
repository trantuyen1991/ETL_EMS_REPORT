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
- [ ] Reuse daily-like color hierarchy for periodic detail cells:
  - zero values
  - low/mid/high heat levels
  - row-max emphasis
- [ ] Reuse daily-like contrast balance so highlighted cells feel softer and more readable
- [ ] Keep periodic area theme accents (`accent_color`, `accent_tint`, `header_bg`) intact

### Out of scope
- [x] No sorting changes for weekly/monthly meter columns
- [x] No business-logic changes in energy calculation
- [x] No restructuring of periodic detail pagination flow
- [x] No attempt to convert periodic tables into daily-style value-bar columns

### Likely touch points
- [ ] `src/services/energy_service.py`
  - verify shared `heat_class` / `is_row_max` semantics stay unchanged
- [ ] `src/services/report_builder_service.py`
  - verify daily and periodic detail builders can share the same semantic meaning without changing ordering
- [ ] `src/templates/assets/report.css`
  - use as the daily visual reference for detail-table tone and emphasis
- [ ] `src/templates/assets/report_pdf_base.css`
  - identify periodic defaults currently diverging from daily semantics
- [ ] `src/templates/assets/report_pdf.css`
  - apply PDF-only periodic overrides for final alignment
- [ ] `src/templates/report/pdf/sections/electricity.html`
  - keep current periodic table structure; only consume refined styling hooks if needed

### Proposed implementation order
- [ ] Step 1: document the exact daily visual rules worth inheriting
- [ ] Step 2: map current periodic rules that differ only in presentation
- [ ] Step 3: align periodic PDF palette and emphasis to daily semantics without touching sorting
- [ ] Step 4: re-render weekly and monthly samples to confirm no regression in readability or pagination

### Done when
- [ ] Period detail colors feel like the same product family as daily detail
- [ ] Weekly/monthly tables keep stable column comparison across days
- [ ] No new crowding/pagination regression is introduced
- [ ] Sorting behavior remains unchanged from current periodic behavior
