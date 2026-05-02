# AGENTS.md — Project Rules

## Project Identity

This project is an automated energy reporting system.

It generates structured workshop-level reports from database-backed data and exports:

- HTML interactive view
- HTML PDF source
- PDF A4 print-ready report
- CSV export in a planned future stage

The current project focus is Report V4 preview.



## Current Runtime

Development runtime:
- Ubuntu 24.04
- Python 3.12
- MySQL database
- Chromium for PDF export

Planned release direction:
- Windows executable after backend and UI are stable

Main working directory:
- `/home/nbt/workspace/02_MySQL`



## Main Report Domains

The report is organized by business domain:

1. Report Header
2. Electricity Consumption
3. Utility Usage
4. Energy KPI
5. Footer / Notes

Sensor Monitoring belongs inside the Utility domain.

Do not treat Sensor Monitoring as a separate unrelated report system.



## Rendering Architecture

The system renders from backend context into multiple targets.

HTML view templates:
- `report/view/report_view_daily.html`
- `report/view/report_view_periodic.html`

PDF templates:
- `report/pdf/report_pdf_daily.html`
- `report/pdf/report_pdf_periodic.html`

Template family rules:
- `daily` has its own layout and UI behavior
- `periodic` is shared by weekly and monthly reports
- backend resolves the correct family from report period type

All template families should consume the same backend report context as much as possible.

Business logic belongs in backend services, not duplicated inside templates.



## Report Execution Rules

The report is intended to run once per day.

The effective anchor day is resolved from:

- `.env` variable: `REPORT_ANCHOR_DATE`
- if empty, use today

Scheduled export rules:
- always export `daily`
- if anchor day is Sunday, also export `weekly`
- if anchor day is month-end, also export `monthly`
- if both are true, export `daily + weekly + monthly`

Output filename base comes from:
- `.env` variable: `REPORT_FILENAME`

Current output artifacts per report:
- `._view.html`
- `._pdf_source.html`
- `..pdf`

CSV export is planned but not yet the primary flow.



## Database Rules

The project uses MySQL.

Do not assume PostgreSQL.

Important source-of-truth rule:
- `energy_kpi` is the official source for KPI reporting and official energy totals.

Do not recompute official plant or area totals from raw electricity views when the approved rule says to use `energy_kpi`.

Raw/detail views may be used for supporting detail, meter ranking, visual tables, or diagnostic context only when aligned with business rules.



## Business Logic Guardrails

### General Reporting

- Each report contains current period and previous period.
- Comparable metrics should expose:
  - current value
  - previous value
  - delta
  - delta percentage
- `delta_pct` is computed only when previous value is not zero.
- Missing values display as `-`.
- Zero is valid data and must not be treated as missing.
- Daily tables must render dense rows with no missing dates in the period.

### Electricity

- Official plant and area totals come from `energy_kpi`.
- Do not sum all meter values to derive official totals because feeder overlap may exist.
- Main feeder definitions and area topology are controlled by `config/energy_metadata.py`.
- Main feeders must be excluded from Top 10 meter logic.
- Residual Load may appear as a virtual meter when valid.

### KPI

- Use coverage-first logic.
- Do not prorate KPI blocks.
- Do not reconstruct KPI values from raw energy views.
- Prefer Day > Week > Month > Year coverage.
- Reject partial overlaps that would require prorating.
- Always expose coverage status clearly.
- Missing KPI dates must remain visible in daily detail.

### Utility

- Utility section includes water, chilled water, compressed air, steam, and utility energy where configured.
- Sensor Monitoring belongs under Utility.
- Utility tables must remain dense and printable.



## PDF Export Rules

PDF target:
- fixed A4 output
- print-safe layout
- local Bootstrap and local ECharts assets
- reduced visual effects for stability

PDF export uses Chromium.

Preferred current print path:
- controlled Chrome DevTools Protocol print path
- `scale=1.0`
- `preferCSSPageSize=true`

Legacy Chromium CLI print path should remain fallback only.

When PDF output scale looks wrong:
- inspect document-level overflow first
- especially wide tables
- do not immediately tune unrelated card or chart CSS



## Style and Theme Rules

`config/report_style.json` is the single source of truth for report presentation tokens.

Do not introduce separate frontend-only theme files for this report system.

Approved style direction:
- master palette under `reportStyle.palette`
- reusable theme registry under `reportStyle.themes`
- report components under canonical `components.report..`
- object color references should move toward `themeRef` or similar reference-based ownership
- avoid adding new direct hex or rgba literals into component branches unless necessary

Brand color:
- primary: `#005496`

Visual priorities:
- clean enterprise style
- PDF readability
- consistent Electricity / Utility / KPI visual grammar
- neutral chart cards
- strong but controlled TOTAL cards
- softer area/workshop cards



## Chart Rules

Charts use Apache ECharts.

PDF chart rules:
- disable animation when needed
- prefer SVG mode for PDF output
- initialize charts only after containers have measured size
- freeze rendered charts into static SVG when needed for print stability
- keep interactive behavior isolated to HTML view mode

Approved chart config direction:
- shared chart preset registry
- object-local overrides only where needed
- public mode split:
  - `view`
  - `pdf`

Do not store unrestricted raw ECharts option blobs in JSON.

Prefer controlled project schema and symbolic references such as `formatterRef`.



## Development Workflow

Default workflow:

text
BUILD → CHANGE → BUILD → REVIEW → CHECKLIST UPDATE → COMMIT → MINE
`

Use small checkpoint-based changes.

Before meaningful logic changes:

. run or build current state
. record whether the baseline already fails

After meaningful changes:

. run again
. verify output
. commit only when stable and approved
. re-mine MemPalace if docs/code changed significantly



## MemPalace Workflow

Use after meaningful approved code or documentation changes.

Required commands:

bash
cd /home/nbt/workspace/02_MySQL
pwd
/home/nbt/services/mempalace/.venv/bin/mempalace mine .


Optional:

bash
/home/nbt/services/mempalace/.venv/bin/mempalace status


Never run MemPalace mining from `~`.

Always confirm the project path first.



## Refactor Rules

When refactoring:

1. build/run baseline
2. analyze without changing
3. report duplicate / unused / risky items
4. wait for approval before deletion
5. remove only approved items
6. build again
7. commit stable checkpoint
8. reorder functions separately
9. update docstrings separately

Never mix:

. deletion
. reordering
. behavior change
. documentation update

unless the user explicitly approves a larger combined change.



## OpenClaw Behavior in This Project

OpenClaw must:

. read project docs before large changes
. keep implementation aligned with docs
. propose doc updates when implementation changes
. avoid silent doc rewrites
. avoid auto-commit without approval
. avoid business logic changes during UI-only tasks
. preserve PDF stability when changing layout
. prioritize backend correctness before UI polish

OpenClaw must not:

. assume PostgreSQL
. introduce ThingsBoard or AVEVA concepts
. introduce unrelated architecture
. add new frameworks without clear reason
. hide missing data to make reports look complete
. silently change KPI or energy business rules
