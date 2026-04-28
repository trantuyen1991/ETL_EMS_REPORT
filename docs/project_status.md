# Project Status

## 1. Overview

This project is an automated energy reporting system.

It generates structured reports from database-backed data sources and renders them into:
- HTML (interactive view)
- PDF (A4 print-ready format)
- (Planned) CSV export

The system is designed to run once per day and automatically determine which report set should be exported for the effective anchor day.

---

## 2. Current Development Stage

The project is currently in **Report V4 preview stage**.

Focus:
- stabilize backend data pipeline
- finalize the two-family template migration (`daily` / `periodic`)
- stabilize PDF chart rendering and print flow
- complete the JSON-driven inline style/theme rollout and document the stopping point
- keep sensor monitoring follow-up behind the now-stable presentation checkpoint
Stable baseline:
- PDF export stabilized after the 2026-04-27 chart-init timing fix and multi-anchor regression batches
- style/theme core is now active through backend-generated inline CSS variables and inline ECharts theme registration
- daily family rollout is complete, and periodic family has completed the tokenized base port plus the first scoped detail cleanup

---

## 3. Completed Components

### 3.0 Runtime and template orchestration
- Two template families introduced: ✅
  - `daily`
  - `periodic` shared by weekly + monthly
- Anchor day priority implemented: ✅
  - use `REPORT_ANCHOR_DATE` first
  - fallback to today when empty
- Scheduled export rules implemented: ✅
  - always export `daily`
  - add `weekly` on Sunday
  - add `monthly` on month-end
  - export all applicable reports in one run
- Production batch rendering implemented: ✅
  - one run renders every report needed for the effective anchor day
- Output filename base implemented: ✅
  - `REPORT_FILENAME` from `.env`
- Output artifact set implemented per report: ✅
  - `*_view.html`
  - `*_pdf_source.html`
  - `*.pdf`

### 3.1 Electricity Section
- Plant total summary: ✅
- Area breakdown (DIODE / ICO / SAKARI): ✅
- Comparison vs previous period: ✅
- Line chart and Bar chart ✅
- Top 10 meters (with main feeder exclusion): ✅
- Daily summary: ✅
- Daily detail tables per area: ✅
- Daily detail tables sorted descending by current-day value: ✅
- Daily detail bar fill aligned with ranking order: ✅
- V4 card update (`meter active / total`): ✅
- Area daily summary table: ✅
- Top 10 by area (3 extra tables): ✅
- PDF layout rule: keep plant Top 10 after charts on page 1: ✅
- Daily section header style unified across Electricity / Utility / KPI: ✅
- Periodic electricity heatmap using daily total kWh by area: ✅
- Static HTML/CSS heatmap legend for PDF stability: ✅
- Periodic area delta chart (`Current - Previous`) with delta kWh and delta % labels: ✅
- Periodic area comparison labels tuned for dense workshop names including `ICO`: ✅

### 3.2 Energy KPI Section
- KPI summary matrix by area + total: ✅
- KPI summary matrix reordered to `Total -> DIODE -> ICO -> SAKARI`: ✅
- KPI summary matrix now shows `Today / Yesterday / Delta %`: ✅
- Period KPI summary matrix now reuses the same structure with `This Week / Previous Week` and `This Month / Previous Month` labels: ✅
- Period `Production day` row now counts actual production days in each compared period: ✅
- Header-only grouped color styling for summary matrix: ✅
- Delta% by area and total: ✅
- Delta color rule by metric type: ✅
- Daily KPI grouped bar chart: ✅
- Daily KPI cards now include `Today / Yesterday` comparison: ✅
- Period KPI dashboard now reuses the daily chart family with period labels: ✅
- Daily KPI detail (with coverage status): ✅
- Period KPI detail now uses a vertical area-stacked layout for A4/PDF width control: ✅
- KPI daily header now uses the same boxed highlight style as Electricity: ✅

KPI logic:
- Coverage-first approach implemented
- Source of truth: `energy_kpi`
- No recalculation from raw energy view

---

### 3.3 Utility Section

#### Utility Summary
- Business-level utilities (water, air, steam, etc.): ✅
- Current vs previous comparison: ✅
- Utility comparison bar chart: ✅
- Daily utility cards now use a 2-up current/previous compare row with a dedicated delta line for tighter layout: ✅
- Periodic utility-energy overview cards now reuse the same compact compare-card pattern: ✅
- Periodic utility-energy trend line chart: ✅
- Periodic utility distribution donut chart with right-side legend + total kWh: ✅
- Utility section header now uses the shared `utilityheader.svg` icon in both HTML and PDF templates: ✅

#### Daily Utility Detail
- Dense daily rows: ✅
- Missing handling ("-"): ✅
- Utility daily header now uses the same boxed highlight style as Electricity: ✅
- Utility energy detail table now uses a narrow visual divider between identity columns and grouped consumption metrics for better scanability: ✅

---

### 3.4 Sensor Monitoring (Utility Extension)

Status:
- 🟢 Daily dedicated UI implemented
- 🟢 Periodic Utility rollout implemented for the current staged scope

Backend already available:
- Sensor data fetched from `processvalue`: ✅
- Configured sensor metadata for 18 sensors across 6 groups: ✅
- Daily aggregation (`min`, `avg`, `max`, `latest`): ✅
- Daily data-quality counters (`sample_count`, `non_null_count`, `zero_count`, `negative_count`): ✅
- Measurement-type tagging (`temperature`, `pressure`, `flow`, `capacity`): ✅
- Measurement-type anomaly defaults: ✅
- Negative tolerance handling for light negative values: ✅
- Sensor-specific anomaly overrides: ✅
- Context structure prepared for both compact table and daily v2 cards: ✅
- Period-ready data already present for current period snapshot:
  - overview cards by group ✅
  - grouped sensor detail rows ✅
  - anomaly scan rows ✅
  - daily summary table rows ✅

UI already implemented:
- Daily sensor monitoring overview cards by group: ✅
- Daily sensor range cards using `min / avg / max`: ✅
- Anomaly scan table with alert highlighting: ✅
- Alert reason helper text on sensor cards: ✅
- `Reason` column in anomaly scan table with operator-friendly wording: ✅
- Periodic compact table remains available as fallback view: ✅
- Periodic full-period rollup semantics enabled in UI: ✅
- Periodic line charts by unit using daily aggregate data: ✅

Periodic rollout roadmap:
- Step 1, document and lock scope to `periodic` -> `Utility` only: ✅
- Step 2, promote backend-ready, period-safe blocks into periodic UI: ✅
  - stat pills
  - overview cards
  - grouped sensor cards
  - anomaly scan table
  - keep existing daily summary table
- Step 3, extend backend for true period semantics: ✅
  - anomaly rollup across the whole period
  - period-level trend datasets for chart exploration
- Remaining follow-up:
  - current vs previous comparison block
  - heatmap exploration
  - completeness summary block after anomaly semantics are approved

Current anomaly rules:
- `No data` -> critical
- `Negative exceeds tolerance` -> critical
- `Low coverage` / `Partial coverage`
- `All zero` / `Zero-heavy`
- `Flat signal`
- `Peak-dominant`
- `Latest drift` (ready for future use)

---

## 4. In Progress

### 4.1 Documentation + release wrapping
- refresh project docs to match V4 preview behavior and the stabilized PDF flow
- create milestone tags only on explicit approval after docs + render verification are stable

### 4.2 Daily UI refinement
- daily template remains the main priority
- continue improving information density, readability, and PDF page flow
- keep HTML and PDF utility card density aligned when summary card layout changes
- periodic family has targeted polish in progress for Electricity and Utility chart readability / print stability

### 4.3 Sensor Monitoring UI
- Step 2:
  - enrich derived flags and data-quality metadata
  - prepare reusable periodic trend context
- Step 3:
  - add periodic sensor monitoring trend / heatmap exploration
  - decide whether to promote selected daily charts into periodic family
- Deferred follow-up after the 2026-04-27 period-rollup audit:
  - keep validating whether anomaly heuristics are business-meaningful, not only technically consistent
  - review the 6 currently-flagged weekly sensors with domain context before finalizing threshold logic
  - consider a compact completeness block (`full / partial / no data`) after anomaly semantics are approved

---

## 5. Pending Features

### 5.1 CSV Export
- CSV service exists, but production flow is not wired yet
- Planned to export after PDF generation

### 5.2 Chart Expansion
- More charts will be added across sections
- Requires:
  - responsive handling
  - period-based show/hide logic

### 5.3 Sensor Monitoring Expansion
- periodic trend UI now exists inside `Utility` only, using daily aggregate period lines grouped by unit
- heatmap / anomaly-trend exploration remain next-stage candidates
- threshold-based alert rules are still heuristic and not business-calibrated yet
- anomaly follow-up from the latest correctness audit is intentionally documented for a later business review pass

### 5.4 PDF Stability Improvements
- Chart rendering is currently stable with the timer-based kickoff fix, but still needs regression checks when layout changes
- Table pagination still needs improvement on very wide / dense sections

---

## 6. Known Issues

### 6.1 PDF Export (Chromium Staging Constraint)
- Chromium headless print is more reliable when staging HTML/PDF in a non-hidden directory
- Current workflow resolves a staging directory from:
  - `PRINT_STAGING_DIR`
  - otherwise `OUTPUT_DIR` when non-hidden
  - otherwise another safe non-hidden fallback
- The final PDF is still copied back into project `output/reports/`

---

### 6.2 Chart Rendering in PDF
Current stabilized approach:
- render charts with `renderer: svg`
- disable animation in option
- initialize using measured element width/height
- kick off chart init after `window.load` using `setTimeout(run, 100)`
- keep the readiness signal: `window.status = "loading"` -> wait for `window.load` -> delay `15000ms` -> `window.status = "ready"`
- print Chromium with `--window-status=ready`
- flush ZRender after initial resize
- freeze chart output into static SVG markup inside `*_pdf_source.html`
- stage the HTML in a safe print directory before Chromium print
- chart height overrides are controlled in PDF CSS to avoid overflow into following sections

Root cause found during investigation:
- `requestAnimationFrame(...)` was not stable as the PDF chart-init kickoff in headless Chromium
- intermittent runs never reached chart init / freeze before `window.status = "ready"`
- replacing RAF kickoff with `setTimeout(run, 100)` removed the fail/pass split in repeated regression batches

Important implementation rule:
- if chart width looks wrong, first adjust chart option layout (`grid`, axis labels, spacing)
- avoid solving PDF width issues only with JS width forcing

Do not change casually:
- Chromium print flags
- readiness delay
- timer-based kickoff (`setTimeout(run, 100)`)
- staging output flow
- PDF SVG renderer
- `animation: false`
- freeze flow

Validation completed with repeated 5-run batches on:
- weekday anchor
- Sunday anchor
- month-end anchor

---

### 6.3 Table Printing Issues
- large tables may break across pages
- header repetition not fully stable
- layout may break on wide tables

---

## 7. Runtime Context

### Development Environment
- OS: Ubuntu 24.04
- Python: 3.12
- PDF engine: Chromium

### Deployment Target
- Windows executable (planned)

---

## 8. Report Execution Logic

The report runs daily and determines its period using:

- `.env` variable: `REPORT_ANCHOR_DATE`
- If empty → use today

Rules:
- always export daily
- if anchor day is Sunday → also export weekly
- if anchor day is month-end → also export monthly
- if both conditions are true → export daily + weekly + monthly

---

## 9. Output Handling

### Output Types
- HTML (view)
- HTML (PDF source)
- PDF (print)
- CSV (planned)

### Output Path
- defined via `.env`

### Output Flow (current)
1. resolve effective anchor day
2. determine all required report periods for that day
3. render each report into view HTML
4. render each report into PDF source HTML
5. generate each PDF via Chromium
6. (planned) export CSV

### Output Naming
- Filename base comes from `.env`: `REPORT_FILENAME`
- Current format:
  - `<filename>_<period_type>_<anchor-date>`
- Example:
  - `daily_automatic_report_daily_20250520.pdf`

---

## 10. Development Philosophy

### 10.1 Backend First
- All business logic handled in backend
- UI consumes structured context only

### 10.2 Coverage Transparency
- Missing data must be visible
- No fake completeness

### 10.3 Flexible Context Design
- Context must support future UI extensions
- Avoid hardcoding UI assumptions in backend

---

## 11. OpenClaw Integration Direction

Future goal:
- OpenClaw assists development and maintains project consistency

Expected behavior:

### 11.1 Auto Suggest Documentation Updates
- When implementation changes
- OpenClaw should:
  - detect mismatch between code and documentation
  - propose updates to related `.md` files
  - request user confirmation before applying changes

### 11.2 No Auto Commit Without Approval
- OpenClaw must never commit automatically
- Commit only when explicitly requested by user

### 11.3 Context Awareness
- Must use project documentation (`report_spec.md`, `kpi_report_ruler.md`, etc.)
- Must stay consistent with real implementation

### 11.4 MemPalace-First Project Recall
- Default project recall path: `mempalace search`
- Do not rely on `memory_search` as the default recall path for this project while quota/availability remains unstable
- Recalled context must still be checked against the live repo and rendered outputs
- Future follow-up:
  - restore `memory_search` only as an optional secondary recall path when availability is confirmed again

---

## 12. Next Focus

Immediate next priorities:

1. Start the next layout batch with a documented header and top-summary rule for both template families
2. Keep the current style/theme rollout stable and avoid broad shared-CSS churn unless a concrete periodic regression appears
3. Treat remaining periodic hard-coded values as optional follow-up only when they materially improve maintainability or visual consistency
4. Update documentation whenever style tokens expand or periodic styling scope changes
5. Re-mine project memory after meaningful docs/code checkpoints
6. Keep business/data logic unchanged while presentation work continues
7. Continue sensor monitoring / CSV follow-up only after the presentation checkpoint remains stable
8. Continue PDF regression hardening for future layout changes

Header and top-summary rule for the upcoming layout batch:
- `period-strip-v1` remains `periodic`-only by design
- reason: `periodic` reports summarize a true date range and benefit from a dedicated range strip, while `daily` reports do not need the same treatment
- the intended cleanup target is not structural sameness between the two families
- instead, the next checkpoint should harmonize visual hierarchy, vertical rhythm, spacing density, and the transition from header into the first section while preserving the semantic difference between `daily` and `periodic`
