# Report Specification

## 1. Report Purpose
This report is a workshop-level reporting document designed for daily operational review, management visibility, and export-ready sharing.

The report is built from structured backend context and rendered into HTML first, then used for PDF export and future CSV export.

---

## 2. Rendering Targets

### 2.1 HTML View Template
The project currently has two HTML view template families:

- `report/view/report_view_daily.html`
- `report/view/report_view_periodic.html`

Purpose:
- responsive viewing on desktop and mobile
- CDN-based frontend libraries where suitable
- interactive behavior
- chart animation where allowed
- responsive layout and UI-oriented CSS

### 2.2 PDF Template
The project currently has two dedicated PDF template families:

- `report/pdf/report_pdf_daily.html`
- `report/pdf/report_pdf_periodic.html`

Purpose:
- fixed A4-oriented PDF rendering
- local Bootstrap and local ECharts assets
- PDF-specific CSS
- print-safe layout
- reduced visual effects for stable export

### 2.3 Shared Context Rule
All template families must consume the same backend report context as much as possible.
Differences should be handled at template/CSS/rendering layer, not by duplicating business logic.

### 2.4 Template Family Rule
- `daily` has its own layout and UI behavior
- `periodic` is shared by `weekly` and `monthly`
- template family selection is resolved in backend from the report period type

---

## 3. Runtime and Deployment Context

### 3.1 Current Development Runtime
Current development environment:
- Ubuntu 22.04
- Python 3.10

### 3.2 Release Direction
The project is planned to be released as a Windows executable after backend and UI are stabilized.

### 3.3 Local Export Constraint
During development, PDF printing through Chromium may fail when writing directly inside the project directory because the project is located under an OpenClaw hidden workspace.

Current workaround:
- export PDF to an external directory such as `/home/nbt/Reports`
- then copy the file back into the configured project output directory if needed

This is an implementation/runtime note and should not change report business logic.

---

## 4. Report Period Resolution

### 4.1 Supported Report Periods
The report currently supports:
- daily
- weekly
- monthly
- custom date range

### 4.2 Automatic Period Selection
The report is intended to run once per day.

The effective anchor day is determined from `REPORT_ANCHOR_DATE` in `.env`.
If `REPORT_ANCHOR_DATE` is empty, the system must use today.

Scheduled export rules:
- always export `daily`
- if the anchor day is Sunday → also export `weekly`
- if the anchor day is month-end → also export `monthly`
- if both conditions are true → export `daily + weekly + monthly`

### 4.3 Previous Period
Each report must include previous-period comparison using the matching previous block.

Examples:
- daily → previous day
- weekly → previous week
- monthly → previous month

---

## 5. Report Layout

The report is organized by business domain, not by aggregation level.

Current main sections:

1. Report Header
2. Electricity Consumption
3. Utility Usage
4. Energy KPI
5. Footer / Notes

Future-compatible extension:
6. Sensor Monitoring UI blocks inside Utility section

---

## 6. Report Header

The report header should include:
- report title
- workshop name
- creation/export timestamp
- reporting period
- key period summary values when applicable

Typical summary strip may include:
- start date
- end date
- total energy
- active / total meter count
- total days
- average per day

---

## 7. Electricity Consumption Section

### 7.1 Purpose
Show official electricity totals and meter-level detail for the selected period.

### 7.2 Content
This section should include:
- plant total summary card
- area total summary cards
- area comparison table
- top 10 meters
- daily summary table
- daily detail tables per area

### 7.3 Total Logic
Plant and area official totals must come from pre-calculated values stored in `energy_kpi`, not from summing all raw energy view columns.

### 7.4 Top 10 Rules
Top 10 ranking must exclude main feeder meters.
Residual Load may appear as a virtual meter when valid.

### 7.5 Daily Summary
The daily summary should include:
- total energy
- top 1 meter
- top 1 value
- active meter count
- average per active meter
- total meter count
- inactive meter count

### 7.6 Daily Detail Tables
Daily detail tables should:
- render dense daily rows for the whole period
- preserve full configured meter columns
- support backend-provided heatmap metadata
- sort current-day vertical detail rows from highest to lowest value
- scale value-bar fill consistently with the same descending ranking order
- support responsive horizontal scrolling in HTML view
- remain printable in PDF mode without breaking layout

---

## 8. Utility Usage Section

### 8.1 Purpose
Show business-level utility consumption values and their comparison across periods.

### 8.2 Content
This section should include:
- utility summary table
- daily utility detail table
- sensor monitoring block
- section header styling consistent with Electricity in the daily template

### 8.3 Utility Summary
Utility summary should include:
- utility name
- unit
- current period value
- previous period value
- delta
- delta %

### 8.4 Daily Utility Detail
Daily utility detail should:
- render all days in the period
- display missing values as "-"
- remain responsive on mobile and desktop

### 8.5 Sensor Monitoring Placement
Sensor monitoring belongs to the Utility domain and should be added under this section when UI rendering is enabled.

### 8.6 Daily Sensor Monitoring V2
For the `daily` template family, sensor monitoring currently uses a dedicated layout:
- overview cards by sensor group
- group-level sensor cards using current-day `min / avg / max`
- anomaly scan table
- short operator-facing reason text for flagged sensors
- allowed negative tolerance note for negative anomaly cases

Grouping rule:
- primary grouping by system group
- secondary ordering by measurement type

Current system groups:
- `ICO Chiller`
- `DIODE Chiller`
- `ICO Air`
- `DIODE Air`
- `Boiler`
- `Domestic Water`

### 8.7 Periodic Sensor Monitoring Rule
For the `periodic` template family, sensor monitoring currently remains a compact table view.
Trend charts and heatmap-style views are planned for a later phase.

---

## 9. Energy KPI Section

### 9.1 Purpose
Show energy intensity based on energy and production context.

### 9.2 Content
This section should include:
- plant KPI total
- area KPI comparison
- production context
- daily KPI detail
- KPI coverage information
- section header styling consistent with Electricity in the daily template

### 9.3 KPI Daily Detail
Daily KPI detail should include:
- date
- status
- source
- production values
- energy values
- KPI values
- coverage note

### 9.4 Coverage
Coverage must be visible and explicit.
Missing dates must still be rendered in daily KPI detail.

---

## 10. Sensor Monitoring Extension

### 10.1 Current Backend Status
Backend context already supports utility sensor monitoring.

### 10.2 Intended UI Direction
Sensor monitoring UI should be designed as a Utility subsection, not a separate unrelated section.

### 10.3 Current Backend Contract
Current backend contract is designed to support:
- daily business-metric compact table
- daily sensor-group overview cards
- per-sensor `min / avg / max / latest`
- lightweight anomaly flags
- operator-facing alert labels and detail text
- negative tolerance-aware anomaly handling

### 10.4 Current Daily UI Contract
Daily sensor cards should support:
- sensor display name
- unit
- measurement type label
- `min / avg / max`
- severity flag
- short anomaly reason
- allowed negative tolerance note when relevant

### 10.5 Planned Expansion
Next planned sensor monitoring enhancements:
- stronger threshold / abnormal logic
- periodic trend charts
- heatmap exploration
- anomaly trend summary

### 10.6 Context Design Rule
Backend context should remain flexible enough to support:
- compact table rendering
- current-day range rendering
- future trend series
- future alerting / abnormal logic

---

## 11. Charts and Interactive Behavior

### 11.1 Chart Library
Charts must use Apache ECharts.

### 11.2 Library Source
- PDF template uses local ECharts assets
- HTML view may use CDN-based frontend loading when allowed

### 11.3 Print Stability Rules
When exporting PDF, charts may require additional handling:
- disable animation when needed
- prefer SVG mode when needed
- refresh or resize chart before and after print
- ensure chart size updates correctly when layout changes
- apply print-mode chart sizing before Chromium captures the page
- control final chart height in PDF CSS to protect following tables from overflow

### 11.4 Future Expansion
More charts will be added over time.
Because the system now has a dedicated `daily` family and a shared `periodic` family, chart blocks and UI components may need:
- conditional show/hide
- resize logic
- responsive re-layout
- period-based rendering decisions

---

## 12. PDF Printing Rules

### 12.1 Paper Target
PDF rendering is designed for fixed A4 output.

### 12.2 CSS Separation
PDF mode must use dedicated CSS optimized for:
- page size
- page breaks
- print-safe spacing
- stable rendering

### 12.3 Table Printing Rules
Tables may require special handling for PDF export, including:
- repeating headers on new pages
- splitting large tables safely
- preventing broken rows where possible
- rotating layout or using alternative print layout when needed
- preserving readability for wide tables

### 12.4 Layout Safety
The PDF template must prioritize completeness and stability over animation or visual richness.

---

## 13. Output Files

### 13.1 Current Outputs
Current implemented output:
- rendered HTML view report
- rendered HTML PDF source report
- PDF export in development workflow

### 13.2 Planned Output
Planned export outputs:
- PDF
- CSV

CSV export is not yet implemented but is part of the intended release workflow.

### 13.3 Output Directory
Output paths must come from configuration in `.env`.

### 13.4 Output Naming
Output files must use the configured filename base and resolved report period.

Current naming rule:
- `<filename>_<period_type>_<anchor-date>`

Filename base source:
- `.env` variable: `REPORT_FILENAME`

Example:
- `daily_automatic_report_daily_20250520.pdf`

---

## 14. Design and Responsiveness

### 14.1 View Mode
The HTML view must support:
- desktop
- mobile
- responsive table containers
- responsive cards
- chart resizing

### 14.2 Print Mode
The PDF mode must support:
- fixed printable layout
- A4-safe design
- stable chart rendering
- safe table pagination

### 14.3 Shared Design Goal
The report should remain:
- professional
- readable
- data-dense but understandable
- suitable for both daily operations and export sharing
