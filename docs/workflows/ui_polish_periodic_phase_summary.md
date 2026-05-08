# UI Polish Summary

## Phase: Weekly / Monthly periodic normalization

### Status
- Completed for the primary rendered weekly/monthly report surfaces.
- Canonical periodic wording is now:
  - weekly: `This Week / Last Week`
  - monthly: `This Month / Last Month`

### Completed slices
1. **Electricity periodic audit**
   - reviewed weekly/monthly wording drift across builder and templates

2. **Electricity periodic fix #1**
   - normalized top-10 grouped headers to resolved period labels
   - normalized top-10 note wording away from generic `current-period`

3. **Electricity periodic fix #2**
   - normalized periodic electricity chart subtitles and legend labels to period-aware wording

4. **Periodic label policy normalization**
   - standardized shared weekly/monthly labels to `This Week / Last Week` and `This Month / Last Month`
   - updated related docs and tests to lock the policy

5. **Utility periodic audit**
   - confirmed template layer was mostly aligned
   - isolated drift to builder chart wording

6. **Utility periodic fix #1**
   - normalized utility periodic comparison legends
   - normalized utility periodic comparison, deviation, and trend subtitles
   - normalized utility periodic mix title

7. **KPI periodic audit**
   - confirmed rendered periodic KPI cards, summary headers, date chip, and main chart wording are already aligned
   - no immediate KPI periodic wording fix slice required

### Result by section
- **Electricity:** primary periodic wording aligned on both template and builder paths used in weekly/monthly rendering.
- **Utility:** primary periodic wording aligned in the rendered chart layer.
- **KPI:** rendered periodic wording already aligned; only non-surfacing fallback/default builder strings remain.

### Verification status
- The periodic cleanup chain was extended through three final follow-up slices:
  - P1: residual electricity builder subtitle cleanup
  - P2: KPI fallback title cleanup
  - P3: template fallback copy cleanup
- Final verification state after the completed cleanup chain: `24 passed` via `./venv/bin/pytest -q`

## Follow-up cleanups completed
- **P1 completed:** electricity residual builder subtitles were normalized to period-aware wording.
- **P2 completed:** KPI fallback/default title `Current period KPI summary` was normalized to `KPI Summary Matrix`.
- **P3 completed:** utility template fallback copy now uses `last period` instead of `previous period` when labels are missing.

## Final conclusion
- The wording cleanup chain for this phase is effectively closed.
- Primary rendered report surfaces and remaining low-risk fallback paths now follow the intended daily and periodic label policy.

## Period detail semantics follow-up (2026-05-02)
- The periodic `Daily Energy Detail` tables were polished further so they read closer to the daily product family without changing backend logic, sorting, or matrix structure.
- P6 aligned the base periodic value hierarchy toward daily semantics:
  - default numeric tone was made more neutral
  - heat tiers were softened away from hard block fills
  - `value-max` stayed artifact-safe in Chrome PDF
  - zero-state stayed subdued but readable
- P7 completed the remaining presentation gap:
  - area identity now reads more clearly inside each table, not only in the title
  - DIODE / ICO / SAKARI blocks now carry distinct area-tinted index/date bands and table surfaces
  - in-table heat separation is stronger, so high/mid/low values scan faster
  - missing (`-`), zero (`0.00`), and very small nonzero states are more clearly separated
  - date/index columns remain visually subordinate after a final small saturation reduction
- Validation result:
  - weekly page 2 improved materially in area identity and cell-state readability
  - monthly page 2 showed no obvious regression in readability or column separation
  - automated regression status remained `43 passed`

## Documentation status
- This file is now the durable record for the completed periodic wording + periodic detail presentation cleanup chain.
- The temporary per-slice checklist files used during implementation were retired after consolidation.

## Weekly KPI / Utility extension follow-up (2026-05-03 to 2026-05-04)
- Weekly Utility comparison polish was extended beyond wording-only normalization:
  - weekly deviation chart now mirrors Electricity with centered zero axis and reversed label direction
  - weekly comparison row now uses a 6:4 layout
  - a third weekly insight row now adds `Utility daily total heatmap` + `This Week mix`
  - the new weekly Utility heatmap / mix row is style-configurable from `report_style.json`
- Weekly KPI periodic dashboard was expanded materially:
  - added a weekly-only top insight row with `Energy KPI daily trend` on the left and `Deviation vs Last Week` on the right
  - tuned both weekly KPI rows to a 6:4 layout pattern for visual consistency with Utility
  - tightened trend-chart grid spacing, centered the deviation zero axis, and widened weekly KPI bars
  - weekly KPI deviation labels now split into 2 lines (`delta%` above `delta value + unit`)
  - weekly compare + waterfall order now renders `This Week` before `Last Week`
- Weekly `Daily KPI Detail` readability polish was then extended in two follow-up slices:
  - first pass improved scanability with a dedicated leading `Index` column, stronger grouped identity on the left, and clearer area tinting per day block
  - second pass aligned the weekly table closer to `Daily Energy Detail` semantics by reordering rows to `Plant -> DIODE -> ICO -> SAKARI`
  - `KPI`, `Product`, and `Energy` now use per-column heat fills, each normalized against that metric column's own maximum across the visible weekly table
  - metric text now stays in a neutral dark tone instead of inheriting the old accent colors directly
  - missing (`-`) KPI/Product/Energy cells are forced back to neutral so they do not look like valid heatmap intensity
- Verification status for the KPI/Utility follow-up chain:
  - regression tests remained green after each slice
  - periodic sample renders were regenerated and cropped section screenshots were reviewed in chat
  - the latest `Daily KPI Detail` review checkpoint was accepted by the user before docs consolidation

## Periodic Electricity summary + Utility detail follow-up (2026-05-04)
- `Daily Energy Summary` in the periodic Electricity section received one final readability pass after screenshot review:
  - the exploratory per-area body-fill approach was retired
  - the approved final direction now uses only 2 semantic color families
  - all `Total` cells share one blue family
  - all `Avg / meter active` cells share one purple family
  - fill intensity is still value-based, but normalization is split into 2 independent pools (`all totals` vs `all avg/meter active`)
- `Daily Utility Detail` then received its approved Option B treatment for weekly/monthly rendering:
  - headers use a light tint by utility family
  - body values use per-column heat fill instead of cross-utility comparison color
  - `0` stays visually neutral
  - missing values stay pale
  - business logic and row ordering were intentionally left unchanged
- Verification status for this follow-up:
  - targeted Electricity + Utility regressions stayed green
  - weekly and monthly PDFs were regenerated after each accepted UI slice
  - exact cropped section screenshots were reviewed in chat before consolidation

## Weekly PDF pagination + utility chart/layout checkpoint (2026-05-05)
- Weekly periodic Electricity `Daily Energy Detail` received its final approved pagination/layout pass:
  - `DIODE Daily Energy Detail (Part 1/7)` now stays on the same page as `Daily Energy Summary`
  - the remaining detail blocks render across 3 follow-up pages at 5 tables per page
  - lower weekly detail pages now use the same table scale as `Part 1/7`
  - the 5-per-page fit is achieved through tighter inter-block/title spacing, not by shrinking the tables below the approved `Part 1/7` reference
- Weekly Utility overview then received its approved layout cleanup:
  - the duplicate `This Week mix` donut beside `Utility daily total heatmap` was removed
  - `Utility daily total heatmap` now spans the full row width
  - the retained `This Week mix` stays paired with `Utility Energy Trend (7 Days)`
  - the retained weekly donut now uses the approved PDF geometry tweak (`startAngle: 180`, centered total shifted upward)
- Weekly Sensor Monitoring PDF follow-up was also closed in the same approved batch:
  - `Sensor anomaly scan` stays on its own page before the detail continuation
  - period `Daily Max / Avg detail` now renders at 2 tables per page after the anomaly page
  - weekly sensor-card head spacing was tightened to improve the anomaly-page balance without touching data/business logic
- Verification status for this checkpoint:
  - targeted regression batch remained green at `48 passed`
  - weekly PDF was re-rendered after each accepted adjustment
  - review switched from stitched long artifacts to native page PNGs when Telegram scaling created false size-perception drift
  - the final native-page review was accepted by the user before consolidation

## Utility monthly energy follow-up (2026-05-08)
- The periodic Utility Energy monthly layout received a dedicated screenshot-driven cleanup pass:
  - moved `Utility energy heatmap` to its own full-width row
  - inserted `Deviation vs Last Month` into the old heatmap slot beside `Utility Distribution`
  - kept `Utility Energy Trend` as the opening full-width chart
- The `Utility Distribution` donut was then refined in 2 accepted micro-passes:
  - legend stayed in the right column with `Total` aligned to the same left edge
  - donut geometry was enlarged/retuned without shrinking the visible pie feel
  - final donut/center graphic position was nudged further right so the left percentage label no longer feels cramped against the card edge
- The monthly Utility Energy heatmap scale legend (`Low ... kWh ... High`) was intentionally removed because it was not helpful for the approved presentation.
- Monthly PDF table/pagination follow-up was also closed in the same chain:
  - `Utility Detail Summary` was compacted through tighter PDF spacing only
  - `Daily Utility Detail` was allowed to flow instead of staying overly protected as one keep-together block
  - verification via `pdftotext -layout` confirmed both blocks now appear on the same PDF page

## Next workstream
- No immediate weekly periodic PDF blocker remains for the approved slice.
- The current monthly Utility Energy polish slice is also closed at the accepted checkpoint.
- Use `docs/workflows/template_layout_audit_master_checklist.md` for the next broader audit step when the user opens the next pass.
