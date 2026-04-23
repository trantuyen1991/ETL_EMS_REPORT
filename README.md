# Energy Consumption Reporting System

## Overview

This project is a backend-driven reporting system that generates daily, weekly, and monthly energy reports from industrial data sources.

The system:
- extracts data from MySQL
- builds a structured `report_context`
- renders HTML reports (view + PDF)
- exports PDF and CSV outputs

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

### 3. Dual Template System

| Template | Purpose |
|--------|--------|
| `report_view.html` | Responsive UI (mobile / desktop) |
| `report_pdf.html` | A4 print layout |

---

## Current Version

**Version: V4 preview (release tag pending final confirmation)**

---

## Implemented Features

### 1. Period Engine
- Automatic period detection:
  - Daily
  - Weekly (week-end trigger)
  - Monthly (month-end trigger)
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

- HTML (view)
- HTML (PDF layout)
- PDF export via Chromium (headless)

### PDF chart rendering workflow

For stable PDF chart output, use this sequence:

1. render `report/pdf/report_pdf.html`
2. write rendered file to `/home/nbt/Reports/report_pdf.html`
3. print with Chromium headless into `/home/nbt/Reports/*.pdf`
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

### 6. CSV Export (Planned)
- raw detail data
- same context as report

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

```

---

## Output

Generated files:

```

output/reports/
├── report_view.html
├── report.pdf
└── report.csv (future)

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
- dynamic UI (per period type)
- Windows executable packaging

---

## Author

Tuyen Tran
```
