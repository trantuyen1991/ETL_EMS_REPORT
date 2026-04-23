# Project Status

## 1. Overview

This project is an automated daily energy reporting system.

It generates structured reports from database-backed data sources and renders them into:
- HTML (interactive view)
- PDF (A4 print-ready format)
- (Planned) CSV export

The system is designed to run once per day and automatically determine report period (daily / weekly / monthly) based on configuration.

---

## 2. Current Development Stage

The project is currently in **Report V4 preview stage**.

Focus:
- stabilize backend data pipeline
- finalize report structure changes requested by user
- stabilize PDF chart rendering and print flow
- update project documentation to match implementation

---

## 3. Completed Components

### 3.1 Electricity Section
- Plant total summary: ✅
- Area breakdown (DIODE / ICO / SAKARI): ✅
- Comparison vs previous period: ✅
- Line chart and Bar chart ✅
- Top 10 meters (with main feeder exclusion): ✅
- Daily summary: ✅
- Daily detail tables per area: ✅
- V4 card update (`meter active / total`): ✅
- Area daily summary table: ✅
- Top 10 by area (3 extra tables): ✅
- PDF layout rule: keep plant Top 10 after charts on page 1: ✅

### 3.2 Energy KPI Section
- KPI summary matrix by area + total: ✅
- Delta% by area and total: ✅
- Delta color rule by metric type: ✅
- Daily KPI grouped bar chart: ✅
- Daily KPI detail (with coverage status): ✅

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

#### Daily Utility Detail
- Dense daily rows: ✅
- Missing handling ("-"): ✅

---

### 3.4 Sensor Monitoring (Utility Extension)

Status: 🟡 **Partially implemented (in progress)**

Backend:
- Sensor data fetched from `processvalue`: ✅
- Daily aggregation (avg, max): ✅
- Context structure prepared: ✅

UI:
- Table rendering implemented under Utility section: ✅
- Showing:
  - Avg value
  - Max value
- Example metrics:
  - Domestic Water
  - ICO Chilled Water
  - DIODE Chilled Water
  - Air (ICO / DIODE)
  - Steam
  - Sakari Water

Limitations (current):
- Only table view available
- No chart visualization yet
- No threshold / abnormal highlighting
- Layout still basic
- Unit display incorect, need get info from "src/config/utility_metadata.py"

---

## 4. In Progress

### 4.1 Documentation + release wrapping
- refresh project docs to match V4 preview behavior
- keep release tag pending until final approval / final commit step

### 4.2 Sensor Monitoring UI
- Improve table layout and readability
- Add chart visualization (ECharts)
- Add abnormal detection / highlighting

---

## 5. Pending Features

### 5.1 CSV Export
- Not implemented yet
- Planned to export after PDF generation

### 5.2 Dynamic Output Naming
- Output file naming based on date/time not implemented yet
- Required for release

### 5.3 Chart Expansion
- More charts will be added across sections
- Requires:
  - responsive handling
  - period-based show/hide logic

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
- trigger resize on `beforeprint`, `resize`, and `ResizeObserver`
- flush ZRender after resize

Important implementation rule:
- if chart width looks wrong, first adjust chart option layout (`grid`, axis labels, spacing)
- avoid solving PDF width issues only with JS width forcing

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
- end of month → monthly report
- end of week → weekly report
- otherwise → daily report

---

## 9. Output Handling

### Output Types
- HTML (view)
- PDF (print)
- CSV (planned)

### Output Path
- defined via `.env`

### Output Flow (current)
1. render HTML
2. generate PDF via Chromium
3. (planned) export CSV

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
2. Complete sensor monitoring UI
3. Implement CSV export
4. Add dynamic output naming
5. Continue PDF regression hardening for future layout changes
