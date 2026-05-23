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
- [ ] audit `/reports` shell on mobile widths
- [ ] audit `view.html` daily on mobile widths
- [ ] audit `view.html` weekly on mobile widths
- [ ] audit `view.html` monthly on mobile widths
- [ ] list overflow hotspots by section
- [ ] list touch-usability problems by section
- [ ] record current responsive blockers in CSS/templates

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

## Current next action
Recommended next action after this checklist lands:
- begin **Phase 1 / Step 1** by auditing the `/reports` shell and existing `view.html` responsive foundations before changing visuals.
