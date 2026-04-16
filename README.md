# Energy Consumption PDF Reporting Tool

# 1. README.md (bản hoàn chỉnh cho V1)

# ETL EMS Energy Report Tool

## Overview

This project is an ETL-based reporting tool designed to extract, transform, and present energy consumption data from a MySQL database into structured reports.

The tool focuses on:
- Aggregating energy data from raw meter readings
- Generating clean, readable HTML reports
- Exporting reports to PDF
- Providing raw detail data in CSV format
- Supporting structured logging for traceability

---

## Current Version: v1 Scope

### Data Source
- MySQL database
- Source object: `ems_db.diode_energy` (view/table)
- Dynamic meter detection from columns

---

### Implemented Features

#### 1. Data Aggregation
- Daily aggregation of energy consumption
- Total energy calculation
- Dynamic meter handling (no hardcoded meter list)

#### 2. Daily Summary Table
Each row represents one day with:
- Date
- Total Energy
- Top 1 Meter
- Top 1 Value
- Active Meter Count
- Average per Active Meter
- Total Meter Count
- Inactive Meter Count

#### 3. Comparison vs Previous Period
- Automatically compares with previous period of equal duration
- Metrics:
  - Current Total
  - Previous Total
  - Delta
  - Delta %
  - Trend (Up/Down)

#### 4. Report Output
- HTML report (main format)
- PDF export via Chromium (headless mode)
- Raw detail export to CSV (full dataset)

#### 5. Logging
- Console + file logging
- Structured logs for:
  - ETL process
  - Database operations
  - File export
  - Error handling

---

## Output Files

After running, the system generates:

- HTML Report  
- PDF Report  
- Raw CSV Detail  

Example output:

```

output/
└── reports/
├── debug_report.html
├── energy_report.pdf
└── debug_report_raw_detail.csv

```

---

## Project Structure

```

src/
├── config/
│   └── config_loader.py
├── db/
│   ├── mysql_client.py
│   └── queries.py
├── services/
│   ├── aggregation_service.py
│   ├── report_service.py
│   ├── template_service.py
│   ├── table_service.py
│   ├── chart_service.py
│   ├── csv_export_service.py
│   ├── pdf_service.py
│   └── file_naming_service.py
├── utils/
│   ├── logger.py
│   ├── datetime_utils.py
│   └── validation.py
└── main.py

config/
├── .env
├── .env.example
├── app.yaml
└── logging.yaml

docs/
└── project_status.md

````

---

## Requirements

- Python 3.8+
- MySQL database
- Chromium / Google Chrome / Edge (for PDF export)

---

## Installation

```bash
pip install -r requirements.txt
````

---

## Configuration

### 1. Environment Variables

Copy `.env.example`:

```bash
cp config/.env.example config/.env
```

Update values:

```
MYSQL_HOST=
MYSQL_PORT=
MYSQL_DATABASE=
MYSQL_USER=
MYSQL_PASSWORD=

OUTPUT_DIR=

LOG_LEVEL=INFO
```

---

### 2. YAML Config

`config/app.yaml` controls:

* chart type
* PDF layout (A4, margins)
* optional browser path override

---

## Run

```bash
python3 -m src.main
```

---

## Notes

* PDF export uses Chromium headless mode
* On Ubuntu (snap), avoid writing into hidden folders (e.g. `.openclaw`)
* Use a normal directory like:

```
/home/user/Reports
```

---

## Known Limitations (V1)

* Chart section currently shows data (not fully embedded chart)
* Only 1 data source is supported
* No CLI arguments yet
* XLSX export not implemented
* No scheduling / automation yet

---

## Planned for V2

* Real embedded charts (ECharts)
* CLI support (input date range)
* XLSX export
* Multi-source support
* Batch job execution
* Windows executable packaging
* Improved file naming rules
* Better visualization (trend charts, KPI cards)

---

## Author

Tuyen Tran

---

## License

MIT

````

---

# 2. docs/project_status.md (snapshot v1)

Tạo file: `docs/project_status.md`

```markdown
# Project Status - V1

## Version: v1.0.0 (Frozen)

---

## Completed

### Data Pipeline
- MySQL connection
- Dynamic column detection for meters
- Raw data extraction

### Aggregation
- Daily aggregation logic
- Total energy calculation
- Top meter identification

### Reporting
- HTML report rendering (Jinja2)
- Daily Summary Table
- Comparison vs previous period

### Export
- CSV export (raw detail)
- PDF export (Chromium headless)

### Logging
- Centralized logging setup
- File + console logging
- Logging integrated across services

---

## Verified

- End-to-end ETL flow working
- Output files generated correctly:
  - HTML
  - CSV
  - PDF
- Logging working correctly
- PDF export fixed (permission + path issues)

---

## Known Issues / Limitations

- Chart not embedded yet (data only)
- No CLI interface
- No XLSX export
- Single data source only
- No scheduler

---

## Notes

- OUTPUT_DIR must not be a restricted or hidden path when using Chromium (snap)
- Logging should be initialized before any module execution

---

## Next Phase (V2)

- Chart integration
- CLI input
- Multi-report support
- Windows packaging
- Job scheduling (cron/systemd)

---

## Status

READY FOR V2 DEVELOPMENT 🚀
````
- Next: V2 (multi-source, KPI, utility, advanced reporting)

See details:
👉 docs/v2_roadmap.md
---


