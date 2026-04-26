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
  - daily vertical detail tables sorted highest-to-lowest with ranking-aligned fill bars
  - PDF layout keeps plant Top 10 immediately after electricity charts on page 1

---

### 3. KPI Section

- KPI = Energy / Production (kWh/Ton)
- Includes:
- grouped KPI summary matrix by area + total
- `Today / Yesterday / Delta %` layout for daily summary matrix
- Daily KPI detail
- grouped daily KPI dashboard cards
- grouped daily KPI chart set

Rules:
- coverage-first
- no prorating
- missing data handled explicitly
- delta color rule:
  - energy / KPI increase = red
  - production increase = green

Daily UI refinement currently includes:
- richer doughnut chart callouts and top legend layout aligned with electricity charts
- reordered area groups in summary matrix: `Total -> DIODE -> ICO -> SAKARI`
- header-only color treatment for grouped columns
- daily KPI cards now show both `Today` and `Yesterday`
- daily KPI section header now matches the boxed Electricity header style

---

### 4. Utility Section

Includes:

#### 4.1 Aggregated Utility
- water
- air
- steam

#### 4.2 Sensor Monitoring
- data from `processvalue`
- current configured backend coverage: `18` sensors across `6` system groups
- daily aggregation:
  - minimum (min)
  - average (avg)
  - maximum (max)
  - latest value
  - sample / non-null / zero / negative counts

Daily UI V2 currently includes:
- overview cards by sensor group
- grouped sensor range cards using `min / avg / max`
- anomaly scan table highlighting critical and warning signals
- operator-facing alert reason text on both cards and anomaly table
- negative-tolerance note on cards when a sensor exceeds allowed negative range
- hybrid grouping:
  - primary by system group (`ICO Chiller`, `DIODE Chiller`, `ICO Air`, `DIODE Air`, `Boiler`, `Domestic Water`)
  - secondary ordering by measurement type (`Temperature`, `Pressure`, `Flow`, `Capacity`)

Current anomaly engine highlights:
- measurement-type-aware anomaly defaults
- negative tolerance handling:
  - small negative values can be tolerated
  - only negative values beyond allowed tolerance are alerted
- heuristic flags currently include:
  - negative exceeds tolerance
  - low / partial coverage
  - all zero / zero-heavy
  - flat signal
  - peak-dominant
  - latest drift (ready when enabled)

V4 additions:
- utility comparison bar chart after utility summary
- PDF chart sizing aligned with the same SVG init / resize flow used by electricity charts
- daily sensor monitoring now uses a dedicated UI path instead of the old compact metric table
- utility section header now matches the boxed Electricity header style

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
- apply print-mode sizing before Chromium captures the page
- keep final chart height under PDF CSS control so dense tables stay on the intended page

Important lesson learned:

- if a PDF chart needs more usable width, adjust chart option layout (`grid`, labels, axis spacing) in the backend option builder first
- do not rely on ad-hoc JS width hacks as the primary fix

---

### 6. CSV Export
- CSV export service exists in the codebase
- production flow is not wired to export CSV yet
- final release workflow still treats CSV as pending

---

## Near-Term Sensor Monitoring Plan

Implemented now:
- Step 1: `daily sensor monitoring v2`
  - overview by group
  - current-day range presentation (`min / avg / max`)
  - anomaly scan table

Planned next:
- Step 2:
  - extend backend sensor context for stronger derived flags and quality metadata
  - prepare reusable context for periodic trend rendering
- Step 3:
  - periodic sensor monitoring UI
  - heatmap and trend chart exploration using daily aggregates

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
PRINT_STAGING_DIR=
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
- rendered PDF source should be placed in a safe non-hidden staging directory such as `/home/nbt/Reports` before print, then copied back into project output

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
