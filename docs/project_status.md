# Project Status

## 1. Overview

This project is an automated energy reporting system.

It generates structured reports from database-backed data sources and renders them into:
- HTML (interactive view)
- PDF (A4 print-ready format)
- daily Excel workbook export for the daily report only

The system is designed to run once per day and automatically determine which report set should be exported for the effective anchor day.

---

## 2. Current Development Stage

The project is currently in **Report V4 preview stage**.

Focus:
- stabilize backend data pipeline
- finalize the two-family template migration (`daily` / `periodic`)
- stabilize PDF chart rendering and print flow
- complete the JSON-driven inline style/theme rollout and document the stopping point
- begin the approved enterprise color-palette rollout from a documentation + checkpoint baseline
- keep sensor monitoring follow-up behind the now-stable presentation checkpoint
Stable baseline:
- PDF export stabilized after the 2026-04-27 chart-init timing fix and multi-anchor regression batches
- PDF print flow now also uses a controlled Chrome DevTools Protocol path with `scale=1.0` and `preferCSSPageSize=true`, keeping the old Chromium CLI print as fallback only
- style/theme core is now active through backend-generated inline CSS variables and inline ECharts theme registration
- daily family rollout is complete, and periodic family has completed the tokenized base port plus the first scoped detail cleanup
- legend placement now supports shorthand config objects such as `{ "top": "left" }` and `{ "bottom": "center" }`
- chart grid / legend / chart-height tokens are now moving under `components.report.section.<section>.<object-type>.<object>` in `config/report_style.json`
- Electricity trend and area-comparison charts now carry their own `height` variants under the object node, reducing reliance on shared electricity chart-height buckets
- Electricity `areaShare` now exposes object-local donut config under its chart node, including `legend`, `pie`, `centerGraphic`, and `height`, and the daily PDF path no longer depends on one catch-all chart-height override for the two daily electricity cards
- layout-oriented chart height tokens now prefer a public `view` / `pdf` split in config, while `report_pdf_base.css` and `report_pdf.css` remain internal PDF layers that can share the same `pdf` branch
- summary-card and table tokens have now moved into shared report-tree foundations under `components.report.section.common.*`
- the active `config/report_style.json` has dropped duplicated top-level legacy branches such as `components.summaryCard`, `components.table`, `components.reportContainer`, `components.reportTitle`, `components.reportSubtitle`, `components.reportMetadata`, `components.reportHeader`, and `components.footer`; `ReportStyleService` now expects the canonical `components.report.*` tree and only keeps the narrow `pdfBase` / `pdfCompact` to `pdf` height collapse inside the report tree
- the report header/title/subtitle/metadata CSS consumers have also been repointed to direct `components.report.titleHeader.*` variables, and the old generic alias bridge is no longer part of the active CSS path
- the active CSS assets now consume canonical report tokens directly for colors, text, borders, shadows, radii, and spacing, so the old generic alias bridge variables are no longer emitted by `ReportStyleService`
- electricity heatmap/delta chart heights and the shared table/card CSS layer now consume report-tree variables directly, reducing the old compatibility bridge surface in `ReportStyleService`
- the 2026-04-28 periodic shrink bug was traced to a Utility Sensor Monitoring table overflow in PDF, and the weekly document width is now back in sync with daily at document level

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
  - `view_html/*.html`
  - `pdf_source_html/*.html`
  - `pdf/*.pdf`
  - `excel/*.xlsx` for daily only

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
- Periodic `Daily Energy Summary` now uses a 2-family semantic fill policy (`Total` in blue, `Avg / meter active` in purple), with each family normalized only against its own metric group: ✅
- Periodic electricity heatmap using daily total kWh by area: ✅
- Static HTML/CSS heatmap legend for PDF stability: ✅
- Periodic area delta chart (`Current - Previous`) with delta kWh and delta % labels: ✅
- Periodic area comparison labels tuned for dense workshop names including `ICO`: ✅
- Weekly periodic `Daily Energy Detail` now keeps `DIODE Part 1/7` on the same page as `Daily Energy Summary`, with the remaining detail blocks repaginated into 3 follow-up pages at 5 tables per page: ✅
- Weekly lower `Daily Energy Detail` pages now use the same table scale as `DIODE Part 1/7`, while fitting through tighter inter-block spacing instead of smaller text/table sizing: ✅

### 3.2 Energy KPI Section
- KPI summary matrix by area + total: ✅
- KPI summary matrix reordered to `Total -> DIODE -> ICO -> SAKARI`: ✅
- KPI summary matrix now shows `Today / Yesterday / Delta %`: ✅
- Period KPI summary matrix now reuses the same structure with `This Week / Last Week` and `This Month / Last Month` labels: ✅
- Period `Production day` row now counts actual production days in each compared period: ✅
- Header-only grouped color styling for summary matrix: ✅
- Delta% by area and total: ✅
- Delta color rule by metric type: ✅
- Daily KPI grouped bar chart: ✅
- Daily KPI cards now include `Today / Yesterday` comparison: ✅
- Period KPI dashboard now reuses the daily chart family with period labels: ✅
- Weekly KPI top insight row now renders `Energy KPI daily trend` + `Deviation vs Last Week` in a 6:4 layout: ✅
- Weekly KPI lower comparison row now uses a 6:4 layout for `Energy KPI comparison` + `Total KPI change explanation`, with `Energy KPI comparison` restored on the left after the accepted regression cleanup: ✅
- Weekly KPI deviation chart now uses a centered symmetric zero axis, thicker bars, and two-line labels (`delta%` above `delta value + unit`): ✅
- Weekly KPI compare / waterfall charts now render `This Week` before `Last Week`: ✅
- Daily KPI lower chart row now renders `Energy KPI: Today vs yesterday` beside `Total KPI change explanation`, while `Deviation vs yesterday` keeps a centered zero axis on its own row: ✅
- Daily KPI compare / waterfall charts now render `Today` before `Yesterday`, and the daily deviation card height is rebalanced back to match the upper chart row: ✅
- Monthly KPI dashboard now renders as:
  - total cards
  - full-width `Energy KPI daily trend`
  - shared 50/50 row: `Deviation vs Last Month` | `Energy KPI comparison`
  - full-width `Total KPI change explanation`
  - full-width `Energy KPI heatmap`: ✅
- Monthly KPI compare / waterfall charts now render `This Month` before `Last Month`: ✅
- Monthly KPI heatmap now hides in-cell values and Y-axis labels, and uses a bottom-center legend (`Total`, `DIODE`, `ICO`, `SAKARI`): ✅
- The exploratory monthly `Workshop energy share` donut was removed from the accepted KPI layout: ✅
- Daily KPI detail (with coverage status): ✅
- Period KPI detail now uses a vertical area-stacked layout for A4/PDF width control: ✅
- Weekly/periodic KPI detail now adds a leading `Index` column, reorders each day to `Plant -> DIODE -> ICO -> SAKARI`, and uses per-column heat-fill for `KPI / Product / Energy`: ✅
- Weekly/periodic KPI metric cells now use neutral dark text, column-local max-based fill intensity, and neutral missing-value cells to avoid false heat cues: ✅
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
- Monthly Utility Energy layout now uses `Trend` full-width, `Distribution + Deviation vs Last Month` in a shared row, and `Utility energy heatmap` as a full-width row below: ✅
- Monthly Utility distribution donut now uses a slightly right-shifted geometry to avoid left-edge label crowding, while keeping the pie visually large and the legend/total left-aligned in the right column: ✅
- Monthly Utility energy heatmap now hides the misleading `Low ... kWh ... High` scale legend: ✅
- Monthly PDF Utility `Detail Summary` and `Daily Utility Detail` now fit on the same page through targeted periodic/PDF compaction instead of backend logic changes: ✅
- Utility section header now uses the shared `utilityheader.svg` icon in both HTML and PDF templates: ✅
- Weekly `This Week mix` donut now uses corrected PDF geometry, with a 90° start rotation and upward-centered total/caption positioning: ✅
- Weekly `Utility daily total heatmap` now renders full-width after removing the duplicate `This Week mix` donut from the same row: ✅

#### Daily Utility Detail
- Dense daily rows: ✅
- Missing handling ("-"): ✅
- Utility daily header now uses the same boxed highlight style as Electricity: ✅
- Utility energy detail table now uses a narrow visual divider between identity columns and grouped consumption metrics for better scanability: ✅
- Periodic `Daily Utility Detail` now uses per-column heat fill with light utility-family header tint, while zero stays neutral and missing stays pale: ✅

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
- Daily HTML now uses grouped metric-table cards with icon-rich headers and compact `Metric / Min / Avg / Max / Status` rows: ✅
- Daily PDF now mirrors the grouped metric-table card family instead of the old compressed range-card port: ✅
- Daily overview cards now merge `Domestic Water + Sakari Water`, while the detail cards keep a merged water card and the anomaly scan keeps split water group labels for readability: ✅
- Context-aware short sensor labels now remove repeated group prefixes in daily cards/anomaly scan (`Flow`, `Pressure`, `Cooling Capacity`, `Sakari Flow`, ...): ✅
- Daily anomaly scan table now places `Group` before `Sensor`, compresses numeric columns, and widens the final `Reason` column: ✅
- Anomaly scan table with alert highlighting: ✅
- Alert reason helper text on sensor cards: ✅
- `Reason` column in anomaly scan table with operator-friendly wording: ✅
- Periodic compact table remains available as fallback view: ✅
- Periodic full-period rollup semantics enabled in UI: ✅
- Periodic line charts by unit using daily aggregate data: ✅
- Periodic Utility anomaly/detail follow-up is now focused on table-width cleanup and duplicate-chart removal after the accepted Utility detail polish checkpoint
- Weekly PDF sensor-monitoring follow-up is now closed for the approved slice:
  - `Sensor anomaly scan` remains isolated before the detail pages
  - period `Daily Max / Avg detail` now renders at 2 tables per page
  - weekly sensor-card head spacing was tightened to pull the anomaly page upward without changing data semantics: ✅

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

### 3.5 Presentation cleanup and durable doc consolidation
- Canonical report wording is now stabilized across the primary rendered surfaces:
  - daily: `Today / Yesterday`
  - weekly: `This Week / Last Week`
  - monthly: `This Month / Last Month`
- Daily PDF layout audit is closed for the current sparse sample baseline:
  - utility page 4-5 pagination was rebalanced
  - empty electricity Top 10 shell was removed from PDF output
  - KPI zero-data pages now use explicit empty-state handling
  - daily Sensor Monitoring PDF was reworked into grouped metric-table cards with all detail cards placed before the anomaly scan
  - daily anomaly scan was compacted onto the same page as the cards and now uses split water group labels for readability
- Daily view spacing cleanup is closed for the current baseline:
  - electricity, utility, and KPI chart footprints were tightened
  - sparse daily panels now read as intentional rather than malformed
  - daily Sensor Monitoring HTML now uses compact grouped cards with clearer icons, calmer spacing, and context-shortened metric labels
- Weekly PDF audit is now closed for the approved current slice:
  - utility distribution donut label crowding improved
  - trailing weekly sensor trend card rebalanced
  - utility deviation readability improved in PDF
  - weekly electricity `Daily Energy Detail` now uses explicit page control (`summary + DIODE Part 1/7`, then 3 pages at 5 tables/page)
  - weekly utility heatmap/mix duplication was removed, leaving a full-width heatmap row and a single retained `This Week mix` beside `Utility Energy Trend (7 Days)`
  - weekly utility sensor detail now begins only after the anomaly page and stays at 2 tables per page
  - latest targeted regression batch remained green at `48 passed`
  - utility weekly comparison row now uses a 6:4 layout with centered-zero deviation behavior
  - utility weekly insight row now adds `Utility daily total heatmap` + `This Week mix`
  - utility weekly heatmap / mix geometry is now style-configurable under dedicated config nodes
  - monthly Utility Energy now uses the approved layout progression `Trend -> Distribution + Deviation -> Heatmap`
  - monthly Utility distribution donut was nudged right in both view/PDF so the left percentage label no longer feels cropped
  - monthly Utility energy heatmap scale legend was intentionally removed
  - monthly PDF `Utility Detail Summary` + `Daily Utility Detail` now share one page after targeted compaction
  - weekly KPI now adds a top insight row (`trend + deviation`) and a tuned lower 6:4 compare/waterfall row
  - weekly KPI deviation labels now split across two lines and the compare / waterfall order now starts from `This Week`
  - periodic detail highlight artifacts/date crowding were reduced
  - periodic `Daily KPI Detail` now scans closer to `Daily Energy Detail`, with a wider index column, stronger day-group anchors, Plant-first row ordering, and metric-column heat fills normalized by each column's own max
  - periodic KPI missing metric cells are now visually neutral so `-` rows do not read as real heat intensity
- Periodic `Daily Energy Detail` presentation now aligns more closely with the daily family without changing backend sorting or matrix structure:
  - calmer daily-like heat hierarchy
  - stronger area identity in DIODE / ICO / SAKARI blocks
  - clearer separation of missing, zero, and small nonzero states
- Chart-style externalization status now includes:
  - utility sensor dual-axis tuning under `reportStyle.components.report.section.utility.chart.sensorCluster.dualAxis`
  - canonical visible chart background token under `reportStyle.components.chartCard.background`
  - daily KPI deviation chart config under `reportStyle.components.report.section.kpi.chart.variance`
  - Utility deviation config under `reportStyle.components.report.section.utility.chart.deviation`
  - KPI deviation label positions now match Utility (`positivePosition: left`, `negativePosition: right`)
  - both KPI and Utility horizontal deviation charts now support near-zero label fallback spacing so tiny bars can move away from the 0% axis without changing the main left/right policy
- Completed temporary implementation checklists were retired from `docs/workflows/` after consolidation.
  Durable references are now:
  - `docs/project_status.md`
  - `docs/style/ui_style.md`
  - `docs/workflows/ui_polish_periodic_phase_summary.md`
  - `docs/workflows/template_layout_audit_master_checklist.md`

---

## 4. In Progress

### 4.1 Documentation + release wrapping
- refresh project docs to match V4 preview behavior and the stabilized PDF flow
- create milestone tags only on explicit approval after docs + render verification are stable

### 4.2 Style schema consolidation
- continue moving report presentation controls toward a clearer JSON tree
- keep common report-wide tokens near the top of `report_style.json`
- move section-specific tuning toward `components.report -> section -> object type -> object`
- keep shared 1-source geometry where HTML preview, PDF source, and final PDF should match
- keep CSS and templates on canonical `components.report.*` variables, and avoid reintroducing generic compatibility aliases unless a short-lived migration is unavoidable
- allow renderer-specific overrides only where print behavior really differs

### 4.3 Approved color-architecture reset (2026-04-30)
Current implemented baseline:
- `reportStyle.palette` exists in `config/report_style.json`
- `reportStyle.themes` exists and is consumed by `src/services/style_service.py`
- `themeRef` is already active across multiple report components
- backend normalization already derives reusable shell colors from seed themes for CSS and chart consumers

Remaining migration work:
1. continue replacing leftover local color literals in section-specific branches
2. continue moving remaining component ownership toward `themeRef` / `...Ref`
3. remove inline hardcoded SVG colors as assets are touched
4. shrink compatibility bridges further only when the canonical report-tree consumers are verified stable

### 4.4 Enterprise color palette rollout
Approved architecture:
- `config/report_style.json` remains the single source of truth for the report theme
- `src/services/style_service.py` remains the mapper that normalizes config, emits CSS variables, and derives the ECharts theme
- no separate JS-only theme source should be introduced for this report system

Approved visual direction:
- project primary brand color is now approved as `#005496`
- the palette should stay clean, professional, and PDF-safe
- `TOTAL` cards should use the strongest brand treatment
- workshop cards should use softer tinted surfaces by area color
- section headers should use a white / soft-blue enterprise shell
- chart cards should stay neutral and readable

Approved rollout order:
1. Batch 1, foundation palette + common shell + Electricity pilot
2. Batch 2, KPI section remap
3. Batch 3, Utility section remap + remaining chart hardcode cleanup

Current status after the implemented baseline:
- Batch 1 foundation is already in place through palette/theme registry support and shared shell wiring
- Electricity token ownership is already substantially migrated into the canonical report tree
- KPI and Utility now both consume tokenized section/chart branches, with remaining cleanup focused on residual hardcoded recipes rather than first-time adoption

Current execution rule:
- preserve layout and business logic
- prioritize compatibility and render stability over broad visual rewrites
- use incremental section cleanup rather than restart the rollout from Batch 1

### 4.4 Sensor Monitoring UI
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

### 4.5 Approved chart-style preset rollout (2026-04-30)
Current implemented baseline:
- `reportStyle.chartPreset` already exists in `config/report_style.json`
- preset-ref resolution support already exists in `src/services/style_service.py`
- `familyRef` / preset-driven branching is already part of the active style architecture

Remaining rollout work:
1. continue repointing more chart objects toward shared preset families where reuse is real
2. validate each migration in both `view` and `pdf` before broadening preset ownership
3. keep object-local overrides only for section-specific differences that should not be normalized away

Execution rule remains:
- presets should remain project-owned schema, not unrestricted raw ECharts blobs
- interactive view-only behavior such as tooltip, hover, and zoom must stay isolated from PDF mode rules
- builder runtime patching is still allowed as the last merge layer when data-driven chart logic requires it

---

## 5. Pending Features

### 5.1 Daily Excel Export
- one daily-only `.xlsx` workbook is now generated per daily run
- weekly and monthly Excel exports are intentionally excluded from v1
- workbook formatting is intentionally minimal for v1, prioritizing data completeness, sheet separation, and stable generation
- the workbook is built from backend report context through `ExcelExportService`

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
- The main print path now uses CDP-controlled PDF export instead of depending only on raw `--print-to-pdf` defaults
- A major periodic-vs-daily PDF scale mismatch was resolved by fixing overflow in the periodic Utility Sensor Monitoring detail table rather than continuing to tune Electricity total-card CSS
- Table pagination still needs improvement on very wide / dense sections

### 5.5 Enterprise palette follow-up
- the foundation semantic palette is already present in `config/report_style.json`
- theme/preset resolution is already active in `src/services/style_service.py`
- remaining work is now a cleanup/migration pass:
  - repoint lingering local color literals toward palette/theme ownership
  - keep reducing section-specific hardcoded chart colors where practical
  - continue removing compatibility aliases only after each affected surface is verified stable

---

## 6. Known Issues

### 6.1 PDF Export (Chromium Staging Constraint)
- Chromium headless print is more reliable when staging HTML/PDF in a non-hidden directory
- Current workflow resolves a staging directory from:
  - `PRINT_STAGING_DIR`
  - otherwise `OUTPUT_DIR` when non-hidden
  - otherwise another safe non-hidden fallback
- Final canonical artifacts now write directly into monthly grouped project output under `output/reports/YYYY_MM/`
- Each month folder is split into `pdf/`, `pdf_source_html/`, `view_html/`, and `excel/`

---

### 6.2 Chart Rendering in PDF
Current stabilized approach:
- render charts with `renderer: svg`
- disable animation in option
- initialize using measured element width/height
- kick off chart init after `window.load` using `setTimeout(run, 100)`
- keep the readiness signal: `window.status = "loading"` -> wait for `window.load` -> delay `5000ms` -> `window.status = "ready"`
- print through Chrome headless after `window.status = "ready"`
- use CDP `Page.printToPDF` with `scale=1.0`, `preferCSSPageSize=true`, and print media emulation
- keep the legacy CLI `--print-to-pdf` path as fallback only
- flush ZRender after initial resize
- freeze chart output into static SVG markup inside `*_pdf_source.html`
- stage the HTML in a safe print directory before Chromium print
- chart height overrides are controlled in PDF CSS to avoid overflow into following sections
- when PDF physical scale differs between `daily` and `periodic`, inspect document-level `scroll_width` for hidden overflow before adjusting local component sizing

Root cause found during investigation:
- `requestAnimationFrame(...)` was not stable as the PDF chart-init kickoff in headless Chromium
- intermittent runs never reached chart init / freeze before `window.status = "ready"`
- replacing RAF kickoff with `setTimeout(run, 100)` removed the fail/pass split in repeated regression batches

Important implementation rule:
- if chart width looks wrong, first adjust chart option layout (`grid`, axis labels, spacing)
- avoid solving PDF width issues only with JS width forcing
- if one whole template family prints smaller than another at the same viewer zoom, treat it as a document-overflow / print-fit problem first, not as a card-height problem

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
- daily Excel workbook (`.xlsx`) for the daily report only

### Output Path
- defined via `.env`

### Output Flow (current)
1. resolve effective anchor day
2. determine all required report periods for that day
3. render each report into view HTML
4. render each report into PDF source HTML
5. generate each PDF via Chromium
6. export one daily-only Excel workbook for the daily report

### Output Naming
- Filename base comes from `.env`: `REPORT_FILENAME`
- Current format:
  - `<sort-prefix>_<period_type>_<filename>_<anchor-date>`
- Period sort prefixes:
  - `00_monthly`
  - `20_weekly`
  - `30_daily`
- Example:
  - `00_monthly_daily_automatic_report_20250531.pdf`

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
- Must use project documentation (`report_spec.md`, `kpi_reporting_rules.md`, etc.)
- Must stay consistent with real implementation

### 11.4 MemPalace-First Project Recall
- Default project recall path: `mempalace search`
- Do not use `memory_search` for this project workflow; use MemPalace recall instead
- Recalled context must still be checked against the live repo and rendered outputs
- If `memory_search` becomes healthy again, treat it as optional only, not the primary recall path

---

## 12. Next Focus

Immediate next priorities:

1. Start the next layout batch with a documented header and top-summary rule for both template families
2. Keep the current style/theme rollout stable and avoid broad shared-CSS churn unless a concrete periodic regression appears
3. Treat remaining periodic hard-coded values as optional follow-up only when they materially improve maintainability or visual consistency
4. Update documentation whenever style tokens expand or periodic styling scope changes
5. Re-mine project memory after meaningful docs/code checkpoints
6. Keep business/data logic unchanged while presentation work continues
7. Continue sensor monitoring / daily Excel export follow-up only after the presentation checkpoint remains stable
8. Continue PDF regression hardening for future layout changes

Header and top-summary rule for the upcoming layout batch:
- `period-strip-v1` remains `periodic`-only by design
- reason: `periodic` reports summarize a true date range and benefit from a dedicated range strip, while `daily` reports do not need the same treatment
- the intended cleanup target is not structural sameness between the two families
- instead, the next checkpoint should harmonize visual hierarchy, vertical rhythm, spacing density, and the transition from header into the first section while preserving the semantic difference between `daily` and `periodic`
