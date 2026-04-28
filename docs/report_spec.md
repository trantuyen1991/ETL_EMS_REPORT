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
- Ubuntu 24.04
- Python 3.12

### 3.2 Release Direction
The project is planned to be released as a Windows executable after backend and UI are stabilized.

### 3.3 Local Export Constraint
During development, PDF printing through Chromium may be unreliable when the project is located in a hidden path.

Recommended local setup:
- keep the actively developed project in a non-hidden path such as `/home/nbt/workspace/02_MySQL`
- if the project is moved to a new path, recreate the Python virtual environment in the new location

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

For the `periodic` template family, the electricity chart block should also support:
- a daily-total heatmap by area
- a period-only area delta chart (`Current - Previous`)
- PDF-safe static legend treatment when heatmap scale guidance is shown

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

### 7.7 Periodic Electricity Chart Rules
For the `periodic` template family:
- the heatmap should use daily total kWh by area, not average per active meter
- heatmap row colors should stay aligned with the area summary palette
- the total / plant row should use a distinct teal treatment
- the heatmap legend in PDF should be rendered as static HTML/CSS instead of interactive ECharts visualMap controls
- the area delta chart should show both delta kWh and delta % labels for quick attribution
- area comparison labels must stay readable for dense workshop names, including `ICO`

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

For the `periodic` template family, the utility-energy subsection should also support:
- four overview cards for `Total Utility Energy`, `Air Energy`, `Chilled Water Energy`, and `Boiler Energy`
- a `Utility Energy trend` line chart
- a `Utility Distribution` donut chart with a right-side legend and total kWh block

### 8.3 Utility Summary
Utility summary should include:
- utility name
- unit
- current period value
- previous period value
- delta
- delta %

For the `daily` template family, the utility overview cards should:
- keep the title area to a stable two-line height to avoid uneven card rows
- show `Current` and `Previous` inside a compact two-column compare block
- render delta percentage on its own support row with semantic color and short comparison note
- keep HTML and PDF card structure aligned so density changes do not diverge by renderer

For the `periodic` template family, the utility-energy overview cards should:
- reuse the same compact current/previous compare layout pattern
- keep the delta row visually separated under the compare block
- stay consistent between HTML and PDF renderers

### 8.4 Daily Utility Detail
Daily utility detail should:
- render all days in the period
- display missing values as "-"
- remain responsive on mobile and desktop

For utility energy detail tables:
- keep `Utility` and `Group` as identity columns
- visually separate identity columns from grouped consumption columns with a narrow divider cell
- preserve grouped headers for `Consumption` and `Flow Rate`
- stay printable in PDF mode after width tuning

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
For the `periodic` template family, sensor monitoring rollout must stay inside the utility-only scope.

Implemented periodic scope:
- header stat pills
- overview cards by sensor group
- grouped sensor cards using full-period rollup semantics
- anomaly scan table
- existing daily summary table as supporting detail
- period trend charts using daily aggregate values, grouped by unit
- documented follow-up list for business calibration of anomaly heuristics after correctness audits

Remaining follow-up scope:
- current vs previous comparison for sensor monitoring
- heatmap exploration
- optional completeness summary block after anomaly semantics are approved

Guardrails:
- scope is limited to `Utility` inside the `periodic` family
- do not modify Electricity or unrelated shared layout while rolling out this block
- if shared CSS becomes necessary, review impact before applying it

Period trend rules:
- stay inside `Utility -> Sensor Monitoring`
- prefer daily aggregate trend semantics over end-of-period snapshot semantics
- avoid mixing unrelated units on the same axis without explicit grouping
- keep daily template behavior unchanged while enabling periodic-only charts

### 8.8 Periodic Utility Energy Chart Rules
For the `periodic` template family:
- the utility trend chart should plot daily total kWh by utility energy group
- the trend chart should align visually with the other large periodic chart cards
- the distribution chart should use a PDF-stable donut layout
- the distribution legend should be rendered as regular HTML content beside the donut, not hidden inside the chart only
- the legend should show value and percentage for each utility energy group

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
- period header/date-chip styling aligned with the Utility section in the periodic template
- period chart wording that follows the resolved labels such as `This Week / Previous Week` or `This Month / Previous Month`

### 9.3 KPI Daily Detail
Daily KPI detail should include:
- date
- status
- source
- production values
- energy values
- KPI values
- coverage note

For the periodic template:
- the detail table should be rendered in a vertical area-stacked layout
- each report date should expand into `Plant`, `ICO`, `DIODE`, and `SAKARI` sub-rows
- shared `date / status / source` cells may span the four area rows
- the layout should stay within A4 PDF width without depending on landscape overflow

### 9.4 Coverage
Coverage must be visible and explicit.
Missing dates must still be rendered in daily KPI detail.

### 9.5 Production Day Rule
For non-daily KPI summary matrices:
- `Production day` means the count of dates in the resolved current / previous period where the relevant production metric is greater than zero
- counts must be calculated per area and for plant total
- do not use anchor-day snapshot production values for this row

---

## 10. Sensor Monitoring Extension

### 10.1 Current Backend Status
Backend context already supports utility sensor monitoring.

### 10.2 Intended UI Direction
Sensor monitoring UI should be designed as a Utility subsection, not a separate unrelated section.

For periodic reports, the first visible rollout should reuse existing backend data before introducing any new period-specific analytics.

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
- prefer SVG mode for PDF output
- initialize only after the chart container has a real measured size
- apply print-mode chart sizing before Chromium captures the page
- freeze rendered charts into static SVG markup inside `*_pdf_source.html` before print
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

---

## 15. Style and Theme Configuration Direction

### 15.1 Centralization Goal
Report presentation tokens should move toward a centralized JSON configuration instead of staying hard-coded across templates and CSS assets.

Initial direction:
- introduce `config/report_style.json`
- keep the file human-editable and fast to inspect
- use it as the source for colors, fonts, spacing, radius, and chart palette defaults

### 15.2 Render Rule
Custom report presentation must be rendered inline into output artifacts.

Required behavior:
- HTML view may continue using CDN vendor libraries where already allowed
- PDF source must continue using local vendor libraries for print safety
- custom style/theme must not depend on extra generated theme asset files
- custom CSS variables / CSS blocks should be emitted inline from backend context
- ECharts theme registration should also be emitted inline from backend context

### 15.3 Rollout Strategy
The style/theme refactor should be executed gradually:
1. create the JSON style config and token structure
2. add a backend style helper / service
3. wire style context into render flow
4. apply the new token flow to the daily family first
5. expand from title / section heading into cards, tables, semantic styles, and chart shells
6. port the stable pattern into the periodic family

Current implementation status:
- `config/report_style.json` is active as the central style-token source
- backend render context now emits inline CSS variables plus inline ECharts theme registration
- daily family rollout is complete through headers, cards, tables, badges, chart shells, notes, spacing, legends, and metadata
- periodic family currently includes a safe scoped base port plus first cleanup for electricity periodic detail, KPI periodic detail accents, and utility sensor range states
- final audit indicates the remaining hard-coded values are mostly section-specific visual recipes, not blockers for the shared style/theme architecture

### 15.4 Scope Guard
This refactor is presentation-only.

Must not change:
- KPI business logic
- utility / energy aggregation logic
- ETL pipeline behavior
- report period resolution logic
