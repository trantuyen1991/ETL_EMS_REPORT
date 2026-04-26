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
- refine daily UI first, then continue periodic polish
- stabilize PDF chart rendering and print flow
- extend sensor monitoring from backend-ready data into daily-first UI

Stable baseline:
- PDF export stable at tag `stable-pdf-export-20260426`

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

### 3.2 Energy KPI Section
- KPI summary matrix by area + total: ✅
- KPI summary matrix reordered to `Total -> DIODE -> ICO -> SAKARI`: ✅
- KPI summary matrix now shows `Today / Yesterday / Delta %`: ✅
- Header-only grouped color styling for summary matrix: ✅
- Delta% by area and total: ✅
- Delta color rule by metric type: ✅
- Daily KPI grouped bar chart: ✅
- Daily KPI cards now include `Today / Yesterday` comparison: ✅
- Daily KPI detail (with coverage status): ✅
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
- Utility section header now uses the shared `utilityheader.svg` icon in both HTML and PDF templates: ✅

#### Daily Utility Detail
- Dense daily rows: ✅
- Missing handling ("-"): ✅
- Utility daily header now uses the same boxed highlight style as Electricity: ✅
- Utility energy detail table now uses a narrow visual divider between identity columns and grouped consumption metrics for better scanability: ✅

---

### 3.4 Sensor Monitoring (Utility Extension)

Status: 🟢 **Step 1 implemented for daily**

Backend:
- Sensor data fetched from `processvalue`: ✅
- Configured sensor metadata for 18 sensors across 6 groups: ✅
- Daily aggregation (`min`, `avg`, `max`, `latest`): ✅
- Daily data-quality counters (`sample_count`, `non_null_count`, `zero_count`, `negative_count`): ✅
- Measurement-type tagging (`temperature`, `pressure`, `flow`, `capacity`): ✅
- Measurement-type anomaly defaults: ✅
- Negative tolerance handling for light negative values: ✅
- Sensor-specific anomaly overrides: ✅
- Context structure prepared for both compact table and daily v2 cards: ✅

UI:
- Daily sensor monitoring overview cards by group: ✅
- Daily sensor range cards using `min / avg / max`: ✅
- Anomaly scan table with alert highlighting: ✅
- Alert reason helper text on sensor cards: ✅
- `Reason` column in anomaly scan table with operator-friendly wording: ✅
- Periodic compact table remains available as fallback view: ✅

Current anomaly rules:
- `No data` → critical
- `Negative exceeds tolerance` → critical
- `Low coverage` / `Partial coverage`
- `All zero` / `Zero-heavy`
- `Flat signal`
- `Peak-dominant`
- `Latest drift` (ready for future use)

---

## 4. In Progress

### 4.1 Documentation + release wrapping
- refresh project docs to match V4 preview behavior
- keep release tag pending until final approval / final commit step

### 4.2 Daily UI refinement
- daily template is the current priority
- continue improving information density, readability, and PDF page flow
- keep HTML and PDF utility card density aligned when summary card layout changes
- periodic family will be adjusted after daily stabilizes

### 4.3 Sensor Monitoring UI
- Step 2:
  - enrich derived flags and data-quality metadata
  - prepare reusable periodic trend context
- Step 3:
  - add periodic sensor monitoring trend / heatmap exploration
  - decide whether to promote selected daily charts into periodic family

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
- periodic trend UI is not implemented yet
- heatmap / line trend / anomaly trend are planned next-stage candidates
- threshold-based alert rules are still heuristic and not business-calibrated yet

### 5.4 PDF Stability Improvements
- Chart rendering improved, but still needs regression checks when layout changes
- Table pagination still needs improvement on very wide / dense sections

---

## 6. Known Issues

### 6.1 PDF Export (Chromium Limitation)
- Cannot write directly into project directory (OpenClaw workspace)
- Current workaround:
  - export to `/home/nbt/Reports`
  - print PDF there
  - programmatically copy back to project `output/reports/`

---

### 6.2 Chart Rendering in PDF
Current stabilized approach:
- render charts with `renderer: svg`
- disable animation in option
- initialize using measured element width/height
- schedule chart init after PDF layout is ready
- keep the simple readiness signal: `window.status = "loading"` -> wait for `window.load` -> delay `3000ms` -> `window.status = "ready"`
- print Chromium with `--window-status=ready`
- flush ZRender after initial resize
- freeze chart output into static SVG markup inside `*_pdf_source.html`
- print the staged HTML from `/home/nbt/Reports` with Chromium headless
- chart height overrides are controlled in PDF CSS to avoid overflow into following sections

Important implementation rule:
- if chart width looks wrong, first adjust chart option layout (`grid`, axis labels, spacing)
- avoid solving PDF width issues only with JS width forcing

Do not change casually:
- Chromium print flags
- readiness delay
- staging output flow
- PDF SVG renderer
- `animation: false`
- freeze flow

Reference print flow:
1. render `report_pdf.html`
2. write rendered file to `/home/nbt/Reports/report_pdf.html`
3. print with Chromium headless into `/home/nbt/Reports/*.pdf`
4. copy final PDF back into `output/reports/`

---

### 6.3 Table Printing Issues
- large tables may break across pages
- header repetition not fully stable
- layout may break on wide tables

---

## 7. Runtime Context

### Development Environment
- OS: Ubuntu 22.04
- Python: 3.10
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

### 11.4 Future Integration with MemPalace
- Auto context recall
- Auto documentation sync
- Long-term project memory support

---

## 12. Next Focus

Immediate next priorities:

1. Finalize docs + release note consistency for V4 preview
2. Continue daily template refinement
3. Complete sensor monitoring UI
4. Implement CSV export wiring in production flow
5. Continue PDF regression hardening for future layout changes
