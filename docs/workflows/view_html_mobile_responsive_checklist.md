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
- [ ] verify viewport/container assumptions for browser reading
- [ ] normalize responsive spacing tokens in `report.css`
- [ ] reduce fixed-width / nowrap constraints that break mobile layout
- [ ] define safe stack rules for cards and section grids
- [ ] isolate mobile-only rules so desktop and PDF are not affected

---

## Phase 3 — `/reports` shell mobile UX
- [ ] make filter controls fully touch-friendly on mobile
- [ ] keep collapsible `Filters & Actions` usable on narrow screens
- [ ] ensure action buttons remain readable and tappable
- [ ] reduce shell chrome height so the report gets more screen space
- [ ] verify iframe/report viewport behavior on mobile

---

## Phase 4 — Header and summary-card mobile layout
- [ ] reduce `view.html` header height pressure on small screens
- [ ] prevent title/subtitle overlap with artwork/logo treatment
- [ ] stack summary cards safely without horizontal overflow
- [ ] preserve readable hierarchy for title, generated time, and totals
- [ ] re-check seam/background behavior on narrow widths

---

## Phase 5 — Section layout for Electricity / Utility / KPI
- [ ] review each section card/grid on mobile
- [ ] stack multi-column blocks where needed
- [ ] reduce padding/density where it hurts readability
- [ ] preserve section hierarchy and readability on narrow widths
- [ ] clean up badge/chip/legend wrapping

---

## Phase 6 — Mobile table strategy
- [ ] classify tables into `stackable` vs `scroll-required`
- [ ] keep critical detail tables usable with horizontal scroll where necessary
- [ ] re-evaluate sticky-column strategy for narrow widths
- [ ] improve font-size, padding, and readable density for mobile tables
- [ ] define a mobile rule for periodic detail tables before deep styling polish

---

## Phase 7 — Mobile chart strategy
- [ ] audit chart crop/overflow behavior on mobile
- [ ] reduce label density where necessary
- [ ] move legends or resize chart areas when needed
- [ ] verify touch usability of interactive charts
- [ ] decide which charts should keep desktop behavior vs mobile adjustments

---

## Phase 8 — Recommended implementation order
- [ ] step 1: `/reports` shell baseline
- [ ] step 2: `view.html` header mobile layout
- [ ] step 3: summary-card stacking
- [ ] step 4: section-grid layout for Electricity / Utility / KPI
- [ ] step 5: long-table strategy
- [ ] step 6: chart mobile polish

Reason for the order:
- foundation first
- visible wins early
- reduce rework before table/chart tuning

---

## Phase 9 — Test matrix
- [ ] test `daily` at `360px`
- [ ] test `daily` at `390px`
- [ ] test `daily` at `430px`
- [ ] test `daily` at `768px`
- [ ] test `weekly` at `360px`
- [ ] test `weekly` at `390px`
- [ ] test `weekly` at `430px`
- [ ] test `weekly` at `768px`
- [ ] test `monthly` at `360px`
- [ ] test `monthly` at `390px`
- [ ] test `monthly` at `430px`
- [ ] test `monthly` at `768px`
- [ ] re-check desktop after each major slice
- [ ] verify PDF output remains unaffected

---

## Phase 10 — Done criteria
- [ ] no major horizontal overflow for primary mobile flows
- [ ] shell controls are touch-friendly
- [ ] header remains readable on mobile
- [ ] summary cards do not break layout
- [ ] long tables are still usable when scroll is required
- [ ] charts do not suffer severe crop/overlap issues
- [ ] desktop layout is not materially regressed
- [ ] PDF output is unchanged

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

## Current next action
Recommended next action after this checklist lands:
- continue with **Phase 2 / Step 2.1** by implementing the first `view.html` responsive-foundation slice, starting with header/banner mobile reflow and top summary-card stacking rules before touching deeper tables or chart polish.
