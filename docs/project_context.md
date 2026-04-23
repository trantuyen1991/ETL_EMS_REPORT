# Project Context

## Project Name
Energy Consumption Reporting Tool

## 1. Overview

This project is an automated energy reporting system.

It collects data from multiple database sources, processes and aggregates it in backend services, builds a unified report context, and renders it into HTML and PDF outputs.

The system is designed to run once per day and generate a report based on dynamic period selection.

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

---

### 5.4 processvalue_service

Responsibilities:

* aggregate raw sensor data
* compute:

  * daily average
  * daily maximum

Output:

* structured daily stats for each sensor

---

## 6. Report Context Builder

### 6.1 Entry Point

* `main.py`

Main responsibilities:

* resolve report period
* fetch all required data
* call services
* combine all outputs into `report_context`

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
├── kpi
└── metadata
```

---

### 6.3 Design Principle

* context must be UI-agnostic
* no HTML logic inside backend
* structured, reusable, extensible

---

## 7. Template Rendering

### 7.1 Templates

Two templates exist:

* `report_view.html`
* `report_pdf.html`

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
render report_pdf.html
    ↓
write rendered file to /home/nbt/Reports/report_pdf.html
    ↓
print with Chromium headless to /home/nbt/Reports/*.pdf
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

### 7.4 PDF Chart Rendering Rule

PDF chart rendering must follow the same stable pattern used by the electricity section:

1. measure `el.clientWidth` and `el.clientHeight`
2. initialize ECharts with `renderer: "svg"`
3. disable animation before `setOption`
4. call `resize()` on:
   * initial render
   * `beforeprint`
   * window `resize`
   * `ResizeObserver`
5. flush ZRender after resize for print stability

Important rule learned from implementation:

* if chart width / spacing looks wrong in PDF, first fix the backend chart option (`grid`, labels, axis spacing)
* do not depend on ad-hoc JS width forcing as the main solution

---

## 8. Output Pipeline

Current flow:

1. build report_context
2. render HTML
3. write rendered PDF HTML to `/home/nbt/Reports/report_pdf.html`
4. generate PDF with Chromium headless
5. copy PDF back into project output

Planned:
6. export CSV

---

## 9. Period Resolution

Handled in `main.py`:

Input:

* `REPORT_ANCHOR_DATE` (.env)

Logic:

* end of month → monthly
* end of week → weekly
* otherwise → daily

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
