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

**Version: V4 preview (milestone tags are created only for approved stable checkpoints)**

Current architecture direction:
- keep the current two-family report system (`daily` / `periodic`)
- move report presentation tokens toward a centralized JSON style config
- render custom style/theme inline into HTML / PDF source instead of shipping extra theme assets
- organize `config/report_style.json` so common report-wide tokens stay near the top, while section-specific tokens branch by `report -> section -> object type -> object`
- current schema root for report-owned presentation is now centered on `components.report.*`
- section-shared table/card foundations are now being mirrored under `components.report.section.common.*`
- prefer section-owned chart/card/table objects over flat token buckets when the goal is to tune one concrete report object

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
  - periodic electricity chart stack now adds:
    - a daily-total heatmap by area using total kWh per day
    - a static HTML/CSS heatmap legend for PDF stability
    - a period-only area delta chart (`Current - Previous`) with delta kWh and delta % labels
  - periodic area comparison axis labels are forced readable for workshop names including `ICO`

---

### 3. KPI Section

- KPI = Energy / Production (kWh/Ton)
- Includes:
- grouped KPI summary matrix by area + total
- `Today / Yesterday / Delta %` layout for daily summary matrix
- period summary matrix reuses the same structure with period labels such as `This Week / Previous Week` and `This Month / Previous Month`
- period `Production day` row now counts actual production days within each current / previous period
- Daily KPI detail
- periodic KPI detail now uses a vertical area-stacked layout (`Plant / ICO / DIODE / SAKARI`) so the PDF fits A4 width more reliably
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

Periodic KPI rollout currently includes:
- period header/date chip aligned with the Utility section style
- period dashboard charts reused from the daily KPI family with current/previous period labels
- period summary matrix filled with actual production-day counts instead of anchor-day snapshot values
- period KPI detail rotated into a stacked vertical layout for PDF page-width control

Presentation refactor direction and current implementation state:
- introduce `config/report_style.json` as the central style token source
- generate inline CSS variables / CSS blocks from backend context
- generate inline ECharts theme registration from the same config
- refactor daily family first, then extend the same pattern to the periodic family
- keep HTML output single-file for custom style/theme concerns
- keep PDF source on local vendor libraries while still rendering custom style/theme inline
- current implemented status:
  - `config/report_style.json` is active and wired through backend render context
  - inline CSS variables and inline ECharts theme registration are emitted from `ReportStyleService`
  - daily family rollout is completed through headers, cards, tables, badges, chart shells, chart notes, chart spacing, legends, and metadata
  - periodic family has completed the tokenized base port plus first scoped cleanup for electricity periodic detail, KPI periodic detail accents, and utility sensor range states
  - legend placement now supports shorthand object form such as `{ "top": "left" }` and `{ "bottom": "center" }`
  - chart grid / legend / chart-height tokens are now being reorganized under the report tree, for example `components.report.section.electric.chart.*`
  - Electricity `dailyTrend` and `areaComparison` now own their own `height.view / pdfBase / pdfCompact` branches instead of relying on a shared chart-height bucket
  - summary-card and table tokens have started the same migration path through `components.report.section.common.*` and section-owned card objects such as `components.report.section.utility.card.*`
  - final periodic audit found some remaining hard-coded values, but they are now mostly section-specific visual recipes rather than shared family blockers

Layout refresh decision before the next batch:
- `period-strip-v1` should remain a `periodic`-only element
- this is intentional because the `periodic` family represents a true date range summary while `daily` does not need the same strip
- the next layout pass should therefore target consistent visual hierarchy and page rhythm, not force `daily` and `periodic` to use identical top-of-page structures
- practical implication:
  - keep the daily hero header compact
  - keep the periodic hero header plus period strip
  - align spacing, density, first-section entry rhythm, and section-opening balance across both families without removing the semantic distinction
---

### 4. Utility Section

Includes:

#### 4.1 Aggregated Utility
- water
- air
- steam
- utility-energy rollup cards for `Total Utility Energy`, `Air Energy`, `Chilled Water Energy`, and `Boiler Energy`
- periodic utility-energy cards reuse the compact current/previous compare style from the daily family
- periodic utility-energy charts now include:
  - `Utility Energy trend` as a daily-total line chart by utility energy group
  - `Utility Distribution` as a donut chart with a right-side legend and total kWh summary

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

Periodic sensor monitoring rollout is split into controlled phases:
- Implemented in current periodic Utility scope:
  - header stat pills
  - overview cards by group
  - grouped sensor cards
  - anomaly scan table
  - existing daily summary table as supporting detail
  - full-period rollup semantics instead of end-of-period snapshot wording
  - period line charts using daily aggregate trend data, grouped by unit
- Deferred / next-stage items:
  - current vs previous sensor-monitoring comparison
  - heatmap exploration
  - completeness summary block when anomaly semantics are approved
  - business review of anomaly heuristics after technical correctness audits
- Scope guard:
  - changes must stay inside `Utility` for the `periodic` family
  - do not modify Electricity or unrelated shared layout while rolling out sensor monitoring

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
- current stable PDF path uses Chrome DevTools Protocol print control with fixed `scale=1.0`, `preferCSSPageSize=true`, print media emulation, and a legacy CLI fallback only when CDP print fails

### PDF chart rendering workflow

### PDF width-scaling note

A critical layout bug was confirmed during the 2026-04-28 layout checkpoint:
- `daily` and `periodic` could look identical in `*_pdf_source.html` but still export at visibly different physical scale in the final PDF
- the confirmed root cause was not the Electricity total cards themselves
- the true overflow came from the `periodic` Utility Sensor Monitoring detail table, which pushed weekly `scroll_width` far beyond page width and caused the whole periodic document to be shrunk during print

Current protective rules:
- control final print through CDP instead of relying only on raw `--print-to-pdf` defaults
- keep `preferCSSPageSize=true` and `scale=1.0`
- keep periodic Utility sensor table width constrained to the A4 printable area in PDF CSS
- when daily and periodic PDFs look different at the same viewer zoom, first check document-level `scroll_width` before tuning local card CSS

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

### PDF Export Flow

Current production flow:

1. `python3 -m src.main` calls `run_production()`
2. the report batch resolves which periods are required for the effective anchor day
3. the app renders both view HTML and PDF source HTML
4. the PDF source HTML is written into both `output/reports/` and the print staging directory
5. Chromium headless prints the staged HTML into a staged PDF
6. the final PDF is copied back into `output/reports/`

Template mapping:

- view daily: `src/templates/report/view/report_view_daily.html`
- view weekly/monthly: `src/templates/report/view/report_view_periodic.html`
- PDF daily: `src/templates/report/pdf/report_pdf_daily.html`
- PDF weekly/monthly: `src/templates/report/pdf/report_pdf_periodic.html`

Stable PDF chart rules:

- wait for page readiness using `window.status`
- keep the current `15000ms` readiness delay
- print with Chromium `--window-status=ready`
- use `renderer: "svg"` for PDF charts
- keep `animation: false`
- freeze rendered charts into static content before print
- do not use `requestAnimationFrame(...)` as the chart-init kickoff for PDF
- kick off PDF chart init after load using `setTimeout(run, 100)`
- print from the staging directory, not directly from hidden workspace paths

Local development note:

- prefer a non-hidden project path such as `/home/nbt/workspace/02_MySQL`
- if the project is moved to a new path, recreate `venv` in the new location instead of copying the old environment as-is

Important operational rule:

- `daily` is always exported
- `weekly` is exported only when the anchor day is Sunday
- `monthly` is exported only when the anchor day is month-end
- previous-week and previous-month values are comparison data inside the report, not separate output files

Detailed reference:

- `docs/workflows/pdf_export_flow.md`

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
  - `renderer: "svg"`
  - `animation: false`
  - timer-based kickoff after `window.load`
  - freeze to static SVG before print
- large tables may need pagination handling
- staged PDF source should stay in a safe non-hidden print directory when Chromium staging is required

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
