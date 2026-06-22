# View HTML Mobile Responsive Checklist

## Purpose

Track the next browser-only implementation phase focused on improving `Interactive (view.html)` usability on mobile devices.

This phase is intended to improve responsive reading and touch usability for the Web GUI without changing current report business logic or PDF export behavior.

---

## Scope Guardrails

### In Scope
- `Interactive (view.html)` browser surface only
- mobile and tablet responsive behavior
- `/reports` shell mobile usability
- `view.html` layout, spacing, stacking, and scrolling behavior
- browser-only chart and table readability improvements when safe

### Out of Scope
- `Print Preview` PDF rendering changes
- PDF CSS or PDF template redesign
- report business-rule changes
- CSV contract work
- ThingsBoard/API work

---

## Device Targets
- mobile small: `360px`
- mobile common: `390px` to `430px`
- tablet portrait: `768px`

Primary validation order:
1. portrait mobile
2. larger mobile
3. tablet portrait
4. landscape follow-up only after portrait is stable

---

## Phase 0 — Scope and responsive guardrails
- [x] confirm this phase applies to `Interactive (view.html)` only
- [x] confirm this phase should not change report business logic
- [x] confirm this phase should not affect current PDF output
- [x] define initial target widths (`360`, `390`, `430`, `768`)
- [x] define implementation priority as browser readability first, polish second

Current approved rules:
- keep PDF output unchanged unless separately approved
- treat `Print Preview` as a different surface with its own stability constraints
- prefer browser-only CSS/template work first
- do not start from periodic-table micro-polish before responsive foundation is in place

---

## Phase 1 — Mobile audit baseline
- [x] audit `/reports` shell on mobile widths
- [x] audit `view.html` daily on mobile widths
- [x] audit `view.html` weekly on mobile widths
- [x] audit `view.html` monthly on mobile widths
- [x] list overflow hotspots by section
- [x] list touch-usability problems by section
- [x] record current responsive blockers in CSS/templates

Expected audit buckets:
- shell/filter chrome
- header/banner
- summary cards
- Electricity
- Utility
- KPI
- long tables / periodic detail
- charts / legends / labels

---

## Phase 2 — Responsive foundation
- [x] verify viewport/container assumptions for browser reading
- [x] normalize responsive spacing tokens in `report.css`
- [x] reduce fixed-width / nowrap constraints that break mobile layout
- [x] define safe stack rules for cards and section grids
- [x] isolate mobile-only rules so desktop and PDF are not affected

---

## Phase 3 — `/reports` shell mobile UX
- [x] make filter controls fully touch-friendly on mobile
- [x] keep collapsible `Filters & Actions` usable on narrow screens
- [x] ensure action buttons remain readable and tappable
- [x] reduce shell chrome height so the report gets more screen space
- [x] verify iframe/report viewport behavior on mobile

---

## Phase 4 — Header and summary-card mobile layout
- [x] reduce `view.html` header height pressure on small screens
- [x] prevent title/subtitle overlap with artwork/logo treatment
- [x] stack summary cards safely without horizontal overflow
- [x] preserve readable hierarchy for title, generated time, and totals
- [x] re-check seam/background behavior on narrow widths

---

## Phase 5 — Section layout for Electricity / Utility / KPI
- [x] review each section card/grid on mobile
- [x] stack multi-column blocks where needed
- [x] reduce padding/density where it hurts readability
- [x] preserve section hierarchy and readability on narrow widths
- [x] clean up badge/chip/legend wrapping

---

## Phase 6 — Mobile table strategy
- [x] classify tables into `stackable` vs `scroll-required`
- [x] keep critical detail tables usable with horizontal scroll where necessary
- [x] re-evaluate sticky-column strategy for narrow widths
- [x] improve font-size, padding, and readable density for mobile tables
- [x] define a mobile rule for periodic detail tables before deep styling polish

---

## Phase 7 — Mobile chart strategy
- [x] audit chart crop/overflow behavior on mobile
- [x] reduce label density where necessary
- [x] move legends or resize chart areas when needed
- [x] verify touch usability of interactive charts
- [x] decide which charts should keep desktop behavior vs mobile adjustments

---

## Phase 8 — Recommended implementation order
- [x] step 1: `/reports` shell baseline
- [x] step 2: `view.html` header mobile layout
- [x] step 3: summary-card stacking
- [x] step 4: section-grid layout for Electricity / Utility / KPI
- [x] step 5: long-table strategy
- [x] step 6: chart mobile polish

Reason for the order:
- foundation first
- visible wins early
- reduce rework before table/chart tuning

---

## Phase 9 — Test matrix
- [x] test `daily` at `360px`
- [x] test `daily` at `390px`
- [x] test `daily` at `430px`
- [x] test `daily` at `768px`
- [x] test `weekly` at `360px`
- [x] test `weekly` at `390px`
- [x] test `weekly` at `430px`
- [x] test `weekly` at `768px`
- [x] test `monthly` at `360px`
- [x] test `monthly` at `390px`
- [x] test `monthly` at `430px`
- [x] test `monthly` at `768px`
- [x] re-check desktop after each major slice
- [ ] verify PDF output remains unaffected

---

## Phase 10 — Done criteria
- [x] no major horizontal overflow for primary mobile flows
- [x] shell controls are touch-friendly
- [x] header remains readable on mobile
- [x] summary cards do not break layout
- [x] long tables are still usable when scroll is required
- [x] charts do not suffer severe crop/overlap issues
- [x] desktop layout is not materially regressed
- [x] PDF output is unchanged

---

## Phase 1 kickoff note

Started on 2026-05-23 with a code/CSS baseline audit for **Phase 1 / Step 1**.

Initial findings from the current browser shell and responsive CSS:
- `/reports` shell already stacks to one column at `760px`, but it still uses `height: 100vh` plus `overflow: hidden`, which may be fragile on mobile browsers with dynamic viewport chrome.
- shell controls currently have only two responsive breakpoints (`1280px`, `760px`), so there is no finer tuning yet for `360px`, `390px`, or `430px` widths.
- `view.html` responsive rules in `report.css` currently focus on broad layout collapse at `1100px`, `900px`, and `700px`, but not on a dedicated mobile reading strategy.
- several critical tables intentionally keep large `min-width` values (`680px` to `920px`), which is acceptable for scroll fallback but confirms that a mobile table strategy must be handled explicitly later in the phase.
- the first implementation slice should therefore stay focused on shell/mobile foundation before touching section-level table or chart polish.

Phase 1 / Step 1.2 audit result for `/reports` shell at `360`, `390`, `430`, and `768` widths:
- title/subtitle and the top-right status chip remain readable across all tested widths and should be preserved with minimal redesign.
- the collapsed `Filters & Actions` shell is visually clean, but it is still too tall on narrow phones because summary chips wrap into too many rows.
- the disclosure/action affordance feels visually detached from the summary chip cluster and should be made denser and more obviously tappable.
- narrow mobile widths currently lose too much vertical viewport to shell chrome before the embedded report becomes visible.
- the shell is strongest at `768px`; the main weaknesses are concentrated at `360px` to `430px`.

Prioritized shell-only fixes derived from Step 1.2:
1. compress the collapsed filter-card height on mobile
2. enlarge and better anchor the disclosure tap target
3. tighten summary-chip wrapping and spacing for `360` to `430` widths
4. reduce dead space inside the collapsed shell so the iframe gets more initial viewport
5. keep current heading/status behavior largely unchanged because it is already working well

Phase 1 / Step 1.3 implementation result:
- collapsed `/reports` shell received a first mobile-only compaction pass in `src/templates/web/report_shell.html`
- changed shell viewport handling from pure `100vh` to `100dvh` fallback-aware behavior to better tolerate mobile browser chrome
- reduced mobile shell padding and toolbar padding
- hid the collapsed helper note on narrow widths to save vertical space
- tightened summary-chip padding and spacing for phone widths
- increased the collapsed disclosure tap target to `44px`
- anchored the collapsed summary chips and disclosure control into one tighter row for `390px+` widths, while keeping a narrow-stack fallback below `389px`
- added narrower mobile breakpoints for `430px` and `389px` instead of relying only on the older `760px` collapse

Quick verification after Step 1.3:
- collapsed shell is visibly shorter at `360px` and `390px`
- the disclosure control is easier to tap and no longer feels as detached from the chip cluster
- initial report viewport is improved because less vertical chrome is consumed before the iframe begins
- one remaining shell-only issue is small alignment unevenness between the left title block and the chip/caret row, but it is now a polish issue rather than a major mobile blocker

Phase 1 / Step 1.4 shell-polish result:
- added one more alignment-focused pass for the collapsed shell so the left `Filters & Actions` title block and the chip/caret group sit more cleanly together on narrow widths
- kept the compact horizontal collapsed layout for `390px+` widths, while preserving the stacked fallback below `389px`
- cleaned the shell CSS structure while keeping the same browser-only scope

Representative `view.html` audit baseline for daily / weekly / monthly (`390px` and `430px` widths, top-of-report focus):
- daily, weekly, and monthly all show the same primary mobile blocker: the HTML-native header/banner compresses poorly and the right-side report copy becomes crowded.
- the first summary/overview card rows remain too dense on mobile, with long values and secondary metadata competing inside cards that are still effectively too narrow.
- monthly is currently the most stressed top-of-report case because value lengths are longest and card density is highest.
- weekly remains usable, but date-range and comparison metadata still read as visually dense on narrow widths.
- daily shows the same density pattern, especially in the total card and the first overview cards.

Phase 1 shared blockers recorded from screenshots plus CSS audit:
- header/banner currently keeps a two-column structure (`236px` left art column plus right copy) that is not yet mobile-optimized.
- the header shell keeps `min-height: 142px`, which increases pressure on narrow screens before the first section content begins.
- top summary card systems such as `.electricity-total-grid` and `.kpi-total-grid` still need a mobile-first stacking strategy beyond the current broad responsive collapse.
- several important report tables intentionally retain large mobile fallback widths (`680px` to `920px`), confirming that Phase 1 should stop at audit and shell foundation, while later phases define explicit mobile table strategy.
- top-of-report reading density is currently the most visible mobile pain point before users even reach deep table/chart sections.

Phase 1 outcome:
- shell audit slice is now complete
- shell compactness improved enough to stop being the top mobile blocker
- Phase 1 has identified the next two major responsive fronts: `view.html` header reflow and top summary-card stacking

Phase 2 implementation result:
- responsive foundation work was implemented primarily in `src/templates/assets/report.css`
- mobile header/banner received a first reflow pass with smaller mobile-specific header heights, narrower art columns, lighter right-side text pressure, and mobile-only readability support for the copy block
- periodic period-strip metadata was collapsed into a single-column mobile flow under `700px`
- top card systems were given explicit mobile stacking rules so `electricity-total-grid`, `kpi-daily-card-grid`, `kpi-daily-dashboard-grid`, `kpi-periodic-insight-grid`, and `kpi-monthly-insight-grid` all move to a safer single-column layout on narrow screens
- card compare blocks and footer/meta rows were converted to mobile-safe stacked behavior where needed to reduce width pressure from long values and comparison labels
- section date-chip metadata was made more mobile-friendly by allowing full-width chips and wrapped text instead of hard `nowrap`
- all of the above were kept in browser/mobile media rules and did not alter PDF-family templates or PDF CSS

Phase 2 verification result:
- daily, weekly, and monthly were re-checked at `390px` and `430px`
- header/banner readability is improved enough to keep content contained and readable at phone widths
- top summary-card stacking is now stable enough to close the foundation phase
- date/metadata readability is materially improved, especially in weekly/monthly
- top-of-report density is reduced enough that the next work can move deeper into section layout instead of fighting the initial viewport

Phase 2 non-blocking carry-over:
- the banner copy over the background image can still benefit from later polish, especially for the smaller subtitle and created timestamp, but it is no longer the main blocker for continuing the mobile phase

Phase 3 / Step 3.1 implementation result (mapped to checklist Phase 5 section layout):
- section-level mobile work was completed in `src/templates/assets/report.css` without touching PDF CSS, PDF templates, or report business logic
- compacted Electricity / Utility / KPI section headers for phone widths by reducing icon size, badge density, title spacing, and metadata pressure
- rebalanced weekly/monthly period-strip summary cards into a denser two-column mobile layout at `390px+`, while preserving a one-column fallback below `389px`
- tightened Electricity total cards, Utility overview cards, KPI cards, and shared compare blocks so the first screenful of each section consumes less height on mobile
- normalized chip/badge behavior so status pills and unit badges stay predictable on narrow widths instead of competing with titles
- stacked remaining multi-column section grids where needed, including mobile-safe one-column behavior for section-level chart pair layouts and KPI weekly compare layouts
- reduced shared chart-card padding and mobile chart heights enough to stabilize section rhythm, while still deferring deeper chart-specific polish to a later phase
- kept all changes inside browser/mobile media rules for `Interactive (view.html)` only

Phase 3 / Step 3.1 verification result:
- re-checked `daily`, `weekly`, and `monthly` at `360px`, `390px`, and `430px`
- no blocking section-level overflow or clipped card shells were observed in the verified mobile screenshots
- section rhythm is now more consistent across Electricity, Utility, and KPI, especially for the primary card stacks and the handoff into chart blocks
- weekly/monthly summary strips are denser at common phone widths without reintroducing the older readability issues on the narrowest fallback
- chart interiors and long data tables still have later-phase polish opportunities, but they are no longer blocking closure of the section-layout slice

Phase 3 / Step 3.1 non-blocking carry-over:
- some chart internals remain visually dense at `360px`, which belongs to the later chart-specific mobile polish phase
- long detail tables still rely on the existing scroll fallback and need the explicit mobile table strategy phase next
- a few tiny secondary metric rows inside cards remain tight, but they are readable and no longer a layout blocker

Phase 4 / Step 4.1 implementation result (mapped to checklist Phase 6 mobile table strategy):
- classified current browser tables into two practical mobile buckets: compact tables continue to fit within the section flow, while dense matrix/detail tables explicitly stay scroll-first instead of forcing unsafe card conversion
- added a dedicated browser-only `mobile-scroll-table-wrap` treatment for the key long-table surfaces across Electricity, Utility, and KPI so horizontal scrolling gets clearer containment, visible scrollbars, and right-edge affordance on phone widths
- tightened mobile table density through smaller padding, smaller table typography, and more compact bar-cell internals without changing report business logic or PDF templates/CSS
- preserved or expanded sticky-first-column behavior where it materially helps narrow-width reading, including Electricity Top 10 rank/meter columns, Utility summary first-column labels, and KPI metric/index/date anchors
- made the periodic-detail mobile rule explicit: keep merged/detail tables tabular and scrollable with stable minimum widths rather than collapsing them into stacked cards
- kept all implementation changes inside `Interactive (view.html)` templates and browser CSS only

Phase 4 / Step 4.1 verification result:
- re-checked `daily`, `weekly`, and `monthly` at `360px`, `390px`, `430px`, and `768px`
- ran an additional desktop sanity check at `1280px` after the table-strategy CSS/template changes
- no blocking table-shell regressions, clipped sticky columns, or broken section wrappers were observed in the verification screenshots
- long-table sections now stay contained and readable with explicit scroll behavior instead of feeling accidentally overflowed on narrow screens
- tablet portrait (`768px`) now passes for the three supported browser period types in this mobile phase

Phase 4 / Step 4.1 non-blocking carry-over:
- some chart interiors still look dense at phone widths, especially where axis labels and legends compete inside short chart cards
- table internals are now stable enough to stop being the main blocker, so the next best slice is chart-specific mobile polish rather than more table restructuring
- PDF-family output was intentionally not changed in this slice and still needs a separate explicit verification step if we want to close the final PDF-related checklist item

Phase 5 / Step 5.1 implementation result (mapped to checklist Phase 7 mobile chart strategy):
- completed a browser-only chart polish pass in `src/templates/assets/report.css` focused on Electricity, Utility, and KPI chart readability for `Interactive (view.html)` at phone and tablet widths
- expanded mobile chart stacking by moving the remaining dense chart grids to safer one-column behavior on narrow screens, including periodic Utility grids, Utility energy grids, and sensor-trend preview grids that still felt cramped after the table phase
- increased effective plot area for the chart types that were visibly too shallow on mobile, with differentiated height adjustments for trend, comparison, heatmap, delta, donut/distribution, and KPI dashboard charts instead of one blanket mobile height
- reduced chart-card chrome pressure through tighter mobile title/subtitle spacing and better legend sizing/wrapping, especially for heatmap legends and chart cards that combine subtitle plus legend plus axis labels
- rebalanced the Utility energy distribution card on narrow screens by collapsing the internal donut-and-legend split into a single-column mobile layout so the chart center, legend, and total block no longer compete horizontally
- kept all changes inside browser/mobile CSS for `Interactive (view.html)` only, without touching PDF templates, PDF CSS, or report business logic

Phase 5 / Step 5.1 verification result:
- re-checked `daily`, `weekly`, and `monthly` at `360px`, `390px`, `430px`, and `768px`
- ran a desktop sanity check at `1280px` after the chart-specific mobile changes
- no blocking chart-shell regressions, severe crop/overlap issues, or broken section wrappers were observed in the verification screenshots
- the previously cramped weekly/monthly chart cards now have materially more usable plot area on phone widths, and the remaining chart-dense states stay contained rather than visually broken
- desktop-width chart layout remained stable in the sanity check

Phase 5 / Step 5.1 non-blocking carry-over:
- the smallest `360px` views are still information-dense in a few multi-series Utility and KPI states, but the charts now remain contained and readable enough for this phase
- some labels and legends are necessarily compact at the narrowest widths, especially in heatmap and comparison views, but they do not show blocking clipping/overflow after this pass
- `768px` works well functionally, though a few chart sections still feel like scaled mobile compositions rather than a fully spacious tablet-specific layout

Phase 6 / Step 6.1 verification result (PDF unaffected check):
- confirmed the mobile-responsive implementation range from `35c4aff` to current HEAD stayed on browser-only paths, with no diffs under PDF templates, PDF CSS, `base_pdf.html`, `pdf_service.py`, `report_builder_service.py`, or `report_engine_service.py` from the responsive slices
- rendered representative real PDFs through the live Web GUI preview path for `daily`, `weekly`, and `monthly`
- verified the generated PDFs still use A4 page size and remain structurally stable without blocking clipping, overflow, missing content blocks, or severe section misalignment
- reviewed full-page PDF contact sheets for the representative outputs and found only non-blocking pagination whitespace on some weekly/monthly trailing pages, not a regression tied to the mobile browser work
- this closes the final checklist item for the browser-only mobile responsive phase

Phase 6 / Step 6.1 non-blocking carry-over:
- some weekly/monthly PDF pages still have large unused lower-page whitespace in later sections, but this appears to be a pre-existing pagination efficiency issue rather than a mobile-phase regression
- if needed later, PDF pagination compactness should be handled as a separate PDF-specific optimization task, not mixed back into the browser-responsive stream

## Post-Closure Mobile Polish — 2026-05-30

This follow-up checkpoint keeps the previously closed mobile phase intact while applying narrow `Interactive (view.html)` mobile fixes requested during phone review. It remains browser-only and does not change report business logic, backend context generation, PDF templates, or PDF CSS.

Implemented fixes:
- Daily Electricity `Area Share` and `Area Comparison` charts now stack into one chart per row on phone widths, including iPhone 11 Pro Max-sized viewports.
- Electricity `Top 10 Meter Consumption` now uses a table `colgroup` for the grouped table so the mobile Rank column width is enforced by table structure instead of only cell CSS.
- Electricity `Top 10 Meter Consumption` mobile mode now keeps only the Rank column sticky; Meter and remaining columns scroll horizontally.
- Daily Electricity `Daily Energy Detail` now keeps one scrollable mobile table per Area (`MPC`, `ICO`, `SAKARI`) instead of showing multiple split column tables per Area. Desktop behavior remains unchanged.
- Utility `Utility Detail Summary` mobile mode now reduces the Utility-name column width to roughly 60% of the previous allocation for daily, weekly, and monthly views, with wrapped labels so long utility names do not force the column wider again.

Verification notes:
- Chromium/CDP computed checks at `414px` confirmed the Electricity chart grid stacks, Top 10 Rank/Meter sticky behavior is correct, Daily Energy Detail exposes one visible mobile table per Area with vertical scroll, and Utility summary column widths are reduced across daily/weekly/monthly.
- `./venv/bin/pytest -q` remained green with `85 passed`.
- `/health` returned `200`.

## Post-Closure WebUI Polish — 2026-05-31

This checkpoint extends the closed `Interactive (view.html)` mobile polish stream without changing report data, backend business rules, PDF templates, or PDF CSS.

Implemented fixes:
- HTML view line charts now receive an interactive ECharts inside zoom and bottom slider through the shared view template helper. Electricity, Utility, and KPI view chart initializers apply the helper; PDF templates remain untouched.
- Daily KPI dashboard charts stack into one column on phone-sized viewports.
- KPI summary matrix now uses a compact fixed metric column in HTML view so wide KPI period columns get more usable horizontal space without changing PDF sizing.
- Daily Utility Sensor Monitoring mobile view restores overview cards only for the mobile layout, moves daily alert text into the metric-note area, and removes the previous average-cell alert layout that caused cramped wrapping.
- Monthly Utility Distribution now becomes a full-width block at `900px` and below, including iPhone 11 Pro Max landscape, and its donut/legend layout stacks vertically for more chart width.

Verification notes:
- Chromium/CDP computed checks confirmed Monthly Utility Distribution is full-width at `414x896`, `430x932`, and `896x414`.
- `tests/test_daily_utility_labels.py` passed with `20 passed`.
- Full pytest passed with `91 passed`.
- `git diff --check` passed.

## Post-Closure WebUI Polish — 2026-06-22

This checkpoint extends the interactive chart polish stream for `view.html` without changing report data, backend business rules, PDF templates, or PDF CSS.

Implemented fixes:
- Electricity periodic `Daily total heatmap` now uses backend-provided point metadata so tooltip content can distinguish date cells from the `Average` column.
- The same heatmap tooltip now hides the redundant `Category: Date` line and shows a clearer order: date/average label, area, total kWh, period MAX, MAX date, and `% of MAX`.
- Weekly heatmap x-axis data now includes the `Avg` category when the average column is present, so ECharts category mapping stays explicit.
- The heatmap now gets browser-only ECharts inside zoom plus a bottom slider in `view.html`; PDF output remains static.
- Periodic Electricity area-delta tooltip metadata now includes current, previous, delta, and delta percent values for the shared WebUI formatter.

Verification notes:
- Focused tests passed with `22 passed`.
- Full pytest passed with `98 passed`.
- `/health` returned OK after restarting WebUI.

## Current next action
Recommended next action after this checklist lands:
- the dedicated `Interactive (view.html)` mobile responsive phase remains complete after the 2026-05-31 WebUI polish checkpoint.
- continue with the broader Web GUI backlog or commit/release hygiene rather than reopening the full mobile-responsive checklist.
