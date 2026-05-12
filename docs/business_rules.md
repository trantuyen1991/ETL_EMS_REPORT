# Business Rules

## 1. General Reporting Rules
- The report is built per workshop and organized into structured sections.
- All sections must support comparison between current period and previous period.
- The report must support:
  - daily
  - weekly
  - monthly
  - custom date range
- All daily tables must render **dense rows** (no missing dates in the period).

---

## 2. Period & Comparison Rules

### 2.1 Period Resolution
- Each report contains:
  - current period
  - previous period (same length and type)

### 2.2 Comparison Logic
For all comparable metrics:
- current_value
- previous_value
- delta = current - previous
- delta_pct:
  - only computed when previous_value != 0
  - otherwise display "-"

### 2.3 Display Rules
- Missing values must be displayed as "-"
- Zero is a valid value and must not be treated as missing

---

## 3. Electricity Rules

### 3.1 Scope
- Electricity totals for plant and area must be taken from pre-calculated values stored in `total_energy`.
- Do not derive plant total or area total by summing all meter values from energy views, because energy views may include main feeder meters and downstream overlap.
- `total_energy` is the source of truth for:
  - plant total energy in the Electricity section
  - area official total energy in the Electricity section
- `energy_kpi` remains the source of truth for:
  - KPI-related official energy values
- Main feeder definitions and area topology must be controlled by `config/energy_metadata.py`.
- Residual Load is defined as:

  `Residual Load = Official Area Total - Sum of branch meters excluding main feeders`

- Residual Load represents the portion of area load that is not directly measured by branch submeters.
- Residual Load must be treated as one virtual meter in downstream reporting logic.

### 3.2 Summary
- Provide total consumption for:
  - plant
  - each area

### 3.3 Area Comparison
- Compare current vs previous period
- Include:
  - current
  - previous
  - delta
  - delta %

### 3.4 Top Meter Ranking
- Rank meters by current period consumption.
- Attach previous-period value for comparison.
- Exclude main distribution feeders from:
  - Top Meter ranking
  - Top 1 daily meter logic
- Feeder exclusion rules must follow `config/energy_metadata.py`.
- Residual Load may appear in the ranking as one virtual meter when it has valid calculated value.
- Current display limits:
  - daily = Top 10
  - weekly = Top 10
  - monthly = Top 5
- The effective display limit should be exposed by backend context so templates can render the correct heading and table size without re-implementing period-specific logic.
- If no valid meter data exists:
  - do not generate fake ranking rows
  - allow the table to be empty

### 3.5 Daily Summary
- Must include:
  - total energy
  - top 1 meter
  - active meter count
  - average per active meter
- Must render all dates in the period (dense)

### 3.6 Daily Detail
- Each area must render:
  - full list of configured meter columns
  - even when no data exists for some or all days
- Missing values must be displayed as "-".
- Daily detail rows must support heatmap-related metadata for table rendering.
- Heatmap preparation must be based on row-level or column-level comparison logic prepared in backend context.
- Daily detail may include:
  - cell display value
  - raw numeric value
  - heatmap class or level
  - row maximum marker when applicable

---

## 4. Utility Rules

### 4.1 Scope
- Covers utility consumption such as:
  - water
  - chilled water
  - compressed air
  - steam

### 4.2 Utility Summary
- Must include:
  - current
  - previous
  - delta
  - delta %

### 4.3 Daily Utility Detail
- Must render full date range (dense)
- Each column represents one utility type
- Missing values displayed as "-"

### 4.4 Business Mapping
- Utility metrics must be mapped from raw sensors into business-level names:
  - Domestic Water
  - ICO Chilled Water
  - Diode Air
  - Steam
  - etc.

---

## 5. KPI Rules

### 5.1 KPI Definition
- KPI unit: kWh / Ton
- KPI is derived from:
  - energy
  - production

---

### 5.2 Coverage-First Rule (CRITICAL)
- KPI data must only use rows that were already calculated and stored in `energy_kpi`.
- Do not recompute KPI coverage values from raw electricity views or utility views.
- Do not prorate.
- Do not split `Week`, `Month`, or `Year` rows into smaller daily values.
- Only use rows that fully match the intended reporting block for display.
- If multiple rows represent the same reporting block, always select the row with the latest `dt_lastupdate`.
- KPI rendering must reflect stored business-approved values, not inferred or reconstructed values.

Reference principle:
- coverage-first, no prorating. See `docs/kpi_reporting_rules.md`.

---

### 5.3 KPI Aggregation Behavior

When building KPI for a period:

1. Use all available `Day` rows
2. If gaps exist:
   - optionally use `Week` rows that fully fit uncovered ranges
3. Then `Month`, then `Year`
4. Never overlap or double count

---

### 5.4 KPI Coverage

Each KPI result must include:
- coverage_display (e.g. "6/7")
- coverage_note
- uncovered_ranges
- is_complete flag

---

### 5.5 KPI Daily Detail

Must include:
- production (plant + area)
- energy (plant + area)
- KPI (plant + area)
- status:
  - OK
  - Missing
  - Partial

Daily rows must be dense.

---

## 6. Sensor Monitoring Rules

### 6.1 Scope
- Based on raw sensor data from `processvalue` table

### 6.2 Metric Mapping
Each business metric must define:
- key
- display_name
- unit
- source_sensor column

Example:
- domestic_water → dom_waterflow
- ico_air → iac_airflow
- steam → boi_steamflow

---

### 6.3 Aggregation
For each day and each metric, backend aggregation should preserve the current quality-oriented structure, including:
- min value
- avg value
- max value
- latest value
- sample_count
- non_null_count
- zero_count
- negative_count
- anomaly-ready quality signals such as coverage, zero-heavy patterns, and negative-tolerance checks

---

### 6.4 Output Structure
Sensor monitoring must return a structured UI-ready payload that can support both daily and periodic Utility surfaces.

Current output families include:
- metric_columns
- daily_rows
- overview_cards
- groups
- anomaly_rows
- period_detail_tables
- trend_clusters_render
- period_trend_clusters_render

Each daily row should remain dense and carry structured metric payloads such as:
- date
- date_display
- min / avg / max / latest
- formatted display values
- data-quality metadata when available

---

### 6.5 Missing Data Handling
- If no data:
  - min = None
  - avg = None
  - max = None
  - latest = None
  - display = "-"

---

## 7. Data Quality & Reliability Rules

### 7.1 Safety
- The system must not crash due to bad records

### 7.2 Null Handling
- Null values must be handled safely
- Display "-" instead of crashing or showing invalid numbers

### 7.3 Logging
- Log important steps:
  - data fetching
  - aggregation
  - rendering
- Include row counts and key debug info

### 7.4 Maintainability
- Avoid hard-coded logic
- Prefer dynamic metadata (e.g. sensor mapping)
- Keep logic modular and testable