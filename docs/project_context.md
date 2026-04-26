# Project Context

## Project Name
Energy Consumption Reporting Tool

## 1. Overview

This project is an automated energy reporting system.

It collects data from multiple database sources, processes and aggregates it in backend services, builds a unified report context, and renders it into HTML and PDF outputs.

The system is designed to run once per day and generate one or more reports for the effective anchor day.

---

## 2. High-Level Architecture

The system follows a layered architecture:

```text
Database Layer
    ↓
Repository Layer
    ↓
Service Layer
    ↓
Report Context Builder
    ↓
Template Rendering (HTML / PDF)
    ↓
Output Files
````

---

## 3. Data Sources

### 3.1 Energy Data

Source:

* `energy_kpi`

Purpose:

* official plant totals
* area totals
* KPI-related values
* production context

Rule:

* this is the source of truth for KPI and official totals

---

### 3.2 Raw Sensor Data

Source:

* `processvalue`

Purpose:

* utility sensor monitoring
* flow, pressure, temperature, etc.

Examples:

* ich_supflow
* dch_supflow
* iac_airflow
* boi_steamflow
* dom_waterflow

Configured scope (current):

* 18 sensors
* 6 system groups
* measurement types:
  * temperature
  * pressure
  * flow
  * capacity

---

## 4. Repository Layer

Repositories are responsible for:

* querying database
* returning raw structured data

Key repositories:

### 4.1 energy_repository

* fetch energy KPI data
* return rows used for:

  * electricity section
  * KPI section

---

### 4.2 processvalue_repository

* fetch sensor data from `processvalue`
* support:

  * time range query
  * dynamic column selection

---

## 5. Service Layer

Services contain business logic and aggregation.

---

### 5.1 energy_service

Responsibilities:

* build electricity section data
* build plant and area totals
* build comparison vs previous period
* build daily summary
* build daily detail tables

Key rules:

* must use `energy_kpi` as source of truth
* must not recompute totals from raw views

---

### 5.2 kpi_service (logical responsibility)

Responsibilities:

* build KPI-related context
* apply coverage-first logic
* integrate:

  * production
  * energy
  * KPI values

Rules:

* follow `kpi_report_ruler.md`
* no prorating
* explicit coverage status

---

### 5.3 utility_service

Responsibilities:

* build utility summary
* build daily utility detail
* build sensor monitoring context
* map sensor metadata into grouped UI-ready structures
* evaluate anomaly rules with measurement-type defaults and sensor-specific overrides

---

### 5.4 processvalue_service

Responsibilities:

* aggregate raw sensor data
* compute:

  * daily minimum
  * daily average
  * daily maximum
  * latest value
  * sample_count
  * non_null_count
  * zero_count
  * negative_count

Output:

* structured daily stats for each sensor
* anomaly-ready metrics such as coverage, zero ratio, negative tolerance checks, and latest value

---

## 6. Report Context Builder

### 6.1 Entry Point

* `main.py`

Main responsibilities:

* resolve effective anchor day
* determine all scheduled report periods for one run
* fetch all required data
* call services
* combine all outputs into `report_context`
* render all required output artifacts for each report

---

### 6.2 Context Structure

The final `report_context` contains:

```
report_context
├── header
├── electricity
├── utility
│   ├── summary
│   ├── daily_detail
│   └── sensor_monitoring
│       ├── metric_columns
│       ├── daily_rows
│       ├── overview_cards
│       ├── groups
│       └── anomaly_rows
├── kpi
└── metadata
```

---

### 6.3 Design Principle

* context must be UI-agnostic
* no HTML logic inside backend
* structured, reusable, extensible

Current sensor-monitoring-specific rule:

* one backend context should be flexible enough to support both:
  * compact periodic table rendering
  * richer daily sensor monitoring cards
* anomaly payload should also carry:
  * short label for fast scanning
  * reason detail for operators
  * tolerance-aware negative evaluation

---

## 7. Template Rendering

### 7.1 Templates

Two template families exist:

* `daily`
* `periodic` (shared by weekly + monthly)

---

### 7.2 Rendering Flow

```text
report_context
    ↓
TemplateRenderingService
    ↓
HTML output
    ↓
PDF (via Chromium)
```

### 7.2.1 PDF Print Flow (Current Stable Workflow)

For this project, the practical print workflow is:

```text
render selected report PDF template
    ↓
write rendered file to staging output directory
    ↓
print with Chromium headless to staging output PDF
    ↓
copy final PDF back to project output/reports/
```

Reason:

* Chromium snap cannot reliably write directly into hidden workspace paths during print
* `/home/nbt/Reports` is used as the safe print staging area

---

### 7.3 Template Differences

| Feature    | View          | PDF                |
| ---------- | ------------- | ------------------ |
| Responsive | Yes           | No                 |
| Animation  | Yes           | Limited            |
| CSS        | CDN / dynamic | Local / print-safe |
| Charts     | Interactive   | Static / stable    |

### 7.3.1 View vs PDF Template Map

```text
Daily report
    View -> src/templates/report/view/report_view_daily.html
    PDF  -> src/templates/report/pdf/report_pdf_daily.html

Weekly / Monthly report
    View -> src/templates/report/view/report_view_periodic.html
    PDF  -> src/templates/report/pdf/report_pdf_periodic.html
```

### 7.4 PDF Chart Rendering Rule

PDF chart rendering must follow the same stable pattern used by the electricity section:

1. measure `el.clientWidth` and `el.clientHeight`
2. initialize ECharts with `renderer: "svg"`
3. disable animation before `setOption`
4. schedule chart init after layout is ready so print-target containers have real size
5. flush ZRender after initial resize for print stability
6. freeze the rendered chart into static SVG markup inside `*_pdf_source.html`
7. print the staged HTML with Chromium headless into the staging PDF path

Important rule learned from implementation:

* if chart width / spacing looks wrong in PDF, first fix the backend chart option (`grid`, labels, axis spacing)
* do not depend on ad-hoc JS width forcing as the main solution
* PDF charts should be treated as static print assets, not long-lived interactive widgets

### 7.5 Output vs Staging Paths

```text
project_output_dir
    output/reports/
        <export_stem>_view.html
        <export_stem>_pdf_source.html
        <export_stem>.pdf

staging_output_dir
    /home/nbt/Reports (or another safe non-hidden print directory)
        <export_stem>_pdf_source.html
        <export_stem>.pdf
```

Responsibility split:

* `project_output_dir` stores the canonical report artifacts
* `staging_output_dir` is the Chromium-safe print location

The current stable PDF flow depends on this separation.

---

## 8. Output Pipeline

Current flow:

1. resolve effective anchor day
2. determine all report periods required for that day
3. build report_context per report
4. render `*_view.html`
5. render `*_pdf_source.html`
6. generate PDF with Chromium headless
7. copy PDF back into project output

Planned:
8. export CSV

---

## 9. Period Resolution

Handled in `main.py`:

Input:

* `REPORT_ANCHOR_DATE` (.env)
* `REPORT_FILENAME` (.env)

Logic:

* always export daily
* if anchor day is Sunday → also export weekly
* if anchor day is month-end → also export monthly

Fallback:

* if empty → use today

---

## 10. Sensor Monitoring Flow

```text
processvalue table
    ↓
processvalue_repository
    ↓
processvalue_service (aggregate avg/max)
    ↓
utility_service (build sensor context)
    ↓
report_context.utility.sensor_monitoring
    ↓
render in Utility section
```

---

## 11. Design Principles

### 11.1 Backend First

All business logic must live in backend services.

### 11.2 Single Source of Truth

* energy → energy_kpi
* KPI → energy_kpi
* sensor → processvalue

### 11.3 Explicit Data

* missing values must not be hidden
* no fake completeness

### 11.4 Extensibility

* context must support future UI
* avoid hardcoded UI behavior

---

## 12. OpenClaw Integration Context

OpenClaw is expected to:

### 12.1 Understand System Flow

* repositories
* services
* context builder
* templates

---

### 12.2 Suggest Changes Safely

* propose updates to code or docs
* must ask for user confirmation before applying

---

### 12.3 Keep Documentation in Sync

* detect mismatch between:

  * code
  * report_spec.md
  * project_status.md
* propose updates accordingly

---

### 12.4 Respect Development Control

* must not auto-commit
* must not change logic silently

---

## 13. Future Extensions

Planned improvements:

* sensor monitoring charts
* CSV export
* advanced KPI visualization
* alerting / anomaly detection
* improved PDF layout engine

````
