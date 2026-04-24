# Energy Consumption Reporting System

## Overview

This project is a backend-driven reporting system that generates daily, weekly, and monthly energy reports from industrial data sources.

The system:
- extracts data from MySQL
- builds a structured `report_context`
- renders HTML reports (view + PDF source)
- exports final PDF outputs

---

## Key Concepts

### 1. Context-Driven Architecture

Instead of rendering directly from raw data:

```

Database → Services → report_context → Template → Output

```

- All business logic is handled in backend services
- Templates only render data (no calculations)

---

### 2. Multi-Section Report

The report is divided into:

- Electricity (energy consumption)
- Utility (water, air, steam, sensors)
- Energy KPI (kWh/Ton with production context)

---

### 3. Template Families

| Family | Purpose |
|--------|--------|
| `daily` | Dedicated layout for daily reports |
| `periodic` | Shared layout for weekly + monthly reports |

Current template files:
- `report/view/report_view_daily.html`
- `report/view/report_view_periodic.html`
- `report/pdf/report_pdf_daily.html`
- `report/pdf/report_pdf_periodic.html`

---

## Current Version

**Version: V4 preview (release tag pending final confirmation)**

---

## Implemented Features

### 1. Period Engine
- Anchor day priority:
  - use `REPORT_ANCHOR_DATE` from `.env` first
  - fallback to `today` if empty
- Scheduled export rules:
  - always export `daily`
  - if anchor day is Sunday, also export `weekly`
  - if anchor day is month-end, also export `monthly`
  - if both conditions are true, export `daily + weekly + monthly`
- Controlled by:
```

REPORT_ANCHOR_DATE (.env)

```

---

### 2. Energy Section

- Uses `energy_kpi` as source of truth
- No recalculation from raw meters
- Supports:
- plant total
- area breakdown (ICO, DIODE, SAKARI)
- comparison vs previous period
- V4 layout updates:
  - plant + area cards include `meter active / total`
  - plant Top 10 plus 3 additional Top 10 tables by area
  - area daily summary table added below plant daily summary
  - PDF layout keeps plant Top 10 immediately after electricity charts on page 1

---

### 3. KPI Section

- KPI = Energy / Production (kWh/Ton)
- Includes:
- grouped KPI summary matrix by area + total
- Daily KPI detail
- grouped daily KPI bar chart

Rules:
- coverage-first
- no prorating
- missing data handled explicitly
- delta color rule:
  - energy / KPI increase = red
  - production increase = green

---

### 4. Utility Section

Includes:

#### 4.1 Aggregated Utility
- water
- air
- steam

#### 4.2 Sensor Monitoring (NEW)
- data from `processvalue`
- daily aggregation:
- average (avg)
- maximum (max)

Example metrics:
- Domestic Water
- Chilled Water (ICO/DIODE)
- Air (ICO/DIODE)
- Steam
- Sakari Water

V4 additions:
- utility comparison bar chart after utility summary
- PDF chart sizing aligned with the same SVG init / resize flow used by electricity charts

---

### 5. Report Rendering

- one production run can render all reports scheduled for the effective anchor day
- each report exports:
  - view HTML
  - PDF source HTML
  - PDF
- PDF export via Chromium (headless)

### PDF chart rendering workflow

For stable PDF chart output, use this sequence:

1. render the selected PDF template for the report family
2. write rendered file to the configured staging output directory
3. print with Chromium headless into the staging directory
4. copy final PDF back into `output/reports/`

Chart rendering rule for PDF templates:

- use `renderer: "svg"`
- disable animation in option before `setOption`
- initialize chart with measured `el.clientWidth / el.clientHeight`
- call `resize()` on `beforeprint`, `resize`, and `ResizeObserver`
- flush ZRender after resize for print stability

Important lesson learned:

- if a PDF chart needs more usable width, adjust chart option layout (`grid`, labels, axis spacing) in the backend option builder first
- do not rely on ad-hoc JS width hacks as the primary fix

---

### 6. CSV Export
- CSV export service exists in the codebase
- production flow is not wired to export CSV yet
- final release workflow still treats CSV as pending

---

## Project Structure

```

src/
├── config/            # metadata, data sources
├── db/                # database access layer
├── services/          # business logic
├── templates/         # HTML templates
│   ├── report/pdf/
│   └── report/view/
├── utils/
└── main.py

```

Docs:

```

docs/
├── project_context.md
├── project_status.md
├── report_spec.md
├── kpi_reporting_rules.md
├── business_rules.md
├── prompt_openclaw.md

```

---

## Data Flow

### Step 1 – Extract
- energy data
- KPI data
- processvalue (sensor data)

### Step 2 – Transform
- aggregation
- comparison
- coverage handling

### Step 3 – Build Context

```

report_context = {
electricity: {...},
utility: {
summary: {...},
sensor_monitoring: {...}
},
kpi: {...}
}

```

### Step 4 – Render
- template → HTML
- HTML → PDF

---

## Configuration

### Environment (.env)

```

MYSQL_HOST=
MYSQL_PORT=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=

OUTPUT_DIR=
REPORT_ANCHOR_DATE=
REPORT_FILENAME=

```

---

## Output

Generated files:

```

output/reports/
├── <filename>_<period_type>_<anchor-date>_view.html
├── <filename>_<period_type>_<anchor-date>_pdf_source.html
└── <filename>_<period_type>_<anchor-date>.pdf

```

---

## Known Issues

- PDF chart rendering requires:
  - disable animation
  - resize before print
- Chromium (snap) cannot write into hidden directories
- large tables may need pagination handling
- rendered PDF source should be placed in `/home/nbt/Reports` before print, then copied back into project output

---

## Development Notes

- Backend-first approach
- context must be UI-agnostic
- no business logic in template

---

## Future Roadmap

- CSV export
- advanced charts (ECharts)
- heatmap visualization (daily KPI / sensor)
- continued daily-first UI refinement
- Windows executable packaging

---

## Author

Tuyen Tran
```
