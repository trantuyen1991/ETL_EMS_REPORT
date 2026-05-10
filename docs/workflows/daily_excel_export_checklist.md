# Daily Excel Export Checklist

## Scope lock

- Output target: **one `.xlsx` workbook for the daily report only**
- Do not export weekly or monthly workbooks in v1
- Do not spend time on workbook styling in v1
- Prioritize data completeness, stable generation, and clear sheet separation
- `Sensor_Monitoring` is intentionally excluded from v1

## Checkpoints

- [x] **Checkpoint 1, Audit + workbook contract**
  - inspected the current daily report flow and artifact creation points
  - confirmed the workbook must hook into the existing backend batch flow, not templates
  - defined the v1 sheet contract and source mapping below
  - confirmed v1 exclusions and the current dependency gap (`openpyxl` missing)

- [x] **Checkpoint 2, Dependency + service skeleton**
  - added the Excel writer dependency
  - created a dedicated `ExcelExportService`
  - kept export logic backend-side, not template-side

- [x] **Checkpoint 3, Electricity sheets**
  - `Electricity_Summary`
  - `Electricity_Top_Meter`
  - `Electricity_Detail`

- [x] **Checkpoint 4, Utility sheets**
  - `Utility_Dashboard`
  - `Utility_Consumption_Totals`
  - `Utility_Consumption_Detail`
  - `Utility_Energy_Detail`

- [x] **Checkpoint 5, KPI sheets**
  - `KPI_Totals`
  - `KPI_Summary_Matrix`
  - `KPI_Detail`

- [x] **Checkpoint 6, Batch integration**
  - generate the workbook only for `period_type == "daily"`
  - keep weekly/monthly output unchanged
  - archive the `.xlsx` alongside the current daily artifacts

- [x] **Checkpoint 7, Verification**
  - confirmed daily run generates `.xlsx`
  - confirmed workbook opens successfully
  - confirmed sheet count and names match the contract
  - confirmed weekly/monthly do not generate Excel

- [ ] **Checkpoint 8, Documentation + closeout**
  - update README and export docs to match the implemented flow
  - create a clean checkpoint commit
  - re-mine MemPalace

## Audit notes from checkpoint 1

### Integration points

- Current artifact generation is still in `src/main.py::_render_report_artifacts(...)`
- Current artifact archiving is still in `src/main.py::_archive_report_batch(...)`
- Current batch output only includes:
  - `view_html`
  - `pdf_source_html`
  - `pdf`
- Therefore Excel should be added as a new backend artifact in the same batch flow, gated by daily period only

### Current dependency status

- `requirements.txt` does not yet declare `openpyxl`
- Project venv currently fails with `No module named 'openpyxl'`
- Dependency enablement belongs to checkpoint 2

## V1 workbook contract

### Sheet 1, `Meta`

**Columns**
- `field`
- `value`

**Primary source mapping**
- `meta`
- `period`
- `generated_at`
- `version`
- `context_mode`

**Planned rows**
- report title / report subtitle when available
- period type
- anchor date
- start date
- end date
- generated at
- version
- context mode

### Sheet 2, `Electricity_Summary`

**Columns**
- `row_type`
- `date`
- `scope_key`
- `scope_name`
- `total_energy_display`
- `top_1_meter`
- `top_1_value_display`
- `top_1_pct_display`
- `active_meter_count`
- `average_per_active_display`
- `total_meter_count`
- `inactive_meter_count`

**Primary source mapping**
- plant summary rows from `sections.electricity.daily_summary.rows`
- area summary rows flattened from `sections.electricity.daily_summary.area_rows`

### Sheet 3, `Electricity_Top_Meter`

**Columns**
- `rank`
- `area_key`
- `area_display`
- `meter_key`
- `meter_name`
- `display_name`
- `current_display`
- `current_pct_display`
- `previous_display`
- `previous_pct_display`
- `delta_display`
- `delta_pct_display`

**Primary source mapping**
- `sections.electricity.top10.rows`

### Sheet 4, `Electricity_Detail`

**Columns**
- `date`
- `area_key`
- `area_title`
- `meter_key`
- `meter_display_name`
- `meter_role`
- `raw_value`
- `display_value`
- `official_daily_total`
- `main_feeder_total`
- `submeter_total`
- `unknown_load`

**Primary source mapping**
- parent table metadata from `sections.electricity.daily_detail_tables[*]`
- row totals from `sections.electricity.daily_detail_tables[*].rows[*]`
- per-meter cells from `sections.electricity.daily_detail_tables[*].rows[*].cells[*]`
- meter display names joined from `sections.electricity.daily_detail_tables[*].columns`

### Sheet 5, `Utility_Dashboard`

**Columns**
- `key`
- `title`
- `theme_key`
- `status_label`
- `today_display`
- `yesterday_display`
- `delta_display`
- `delta_pct_display`

**Primary source mapping**
- `sections.utility.daily_dashboard.overview_cards`

### Sheet 6, `Utility_Consumption_Totals`

**Columns**
- `key`
- `display_name`
- `unit`
- `current_value`
- `current_display`
- `previous_value`
- `previous_display`
- `delta_display`
- `delta_pct_display`

**Primary source mapping**
- `sections.utility.consumption.totals.rows`

### Sheet 7, `Utility_Consumption_Detail`

**Columns**
- `date`
- `utility_key`
- `utility_display_name`
- `value_display`
- `family_class`
- `is_max`
- `status`
- `coverage_note`

**Primary source mapping**
- per-column metadata from `sections.utility.consumption.detail.daily_columns`
- per-day values from `sections.utility.consumption.detail.daily_rows[*].daily_values[*]`
- row status from `sections.utility.consumption.detail.daily_rows[*]`

### Sheet 8, `Utility_Energy_Detail`

**Columns**
- `key`
- `display_name`
- `group_label`
- `current_display`
- `previous_display`
- `delta_display`
- `delta_pct_display`
- `energy_current_display`
- `energy_previous_display`
- `energy_delta_display`
- `energy_delta_pct_display`

**Primary source mapping**
- `sections.utility.energy.detail_rows`

### Sheet 9, `KPI_Totals`

**Columns**
- `scope_key`
- `scope_name`
- `current_display`
- `previous_display`
- `coverage_display`
- `unit`

**Primary source mapping**
- plant totals from `sections.kpi.totals.plant`
- area totals from `sections.kpi.totals.areas`

### Sheet 10, `KPI_Summary_Matrix`

**Columns**
- `metric_label`
- `scope_key`
- `today_display`
- `yesterday_display`
- `delta_display`
- `delta_class`
- `delta_arrow`

**Primary source mapping**
- `sections.kpi.summary_matrix.rows`
- scope keys aligned to `sections.kpi.summary_matrix.group_columns`

### Sheet 11, `KPI_Detail`

**Columns**
- `date`
- `time_frame_source`
- `area_key`
- `area_label`
- `energy_display`
- `product_display`
- `kpi_display`
- `status`
- `coverage_note`

**Primary source mapping**
- parent row metadata from `sections.kpi.daily_detail.rows[*]`
- per-area values from `sections.kpi.daily_detail.rows[*].area_rows[*]`

## v1 exclusions

- `Sensor_Monitoring` sheets
- chart-only / heatmap-presentation-only data
- PDF-only readiness / rendering metadata
- workbook styling / visual polish beyond plain headers and raw values
- weekly / monthly workbook generation
