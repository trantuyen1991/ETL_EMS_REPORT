# Electricity Shutdown Analysis Checklist

## Purpose

Add a new periodic Electricity sub-section named `Shutdown Analysis`.

This block is intended to help readers compare:
- average electricity used on off-working days
- average electricity used on working / operation days
- derived hourly usage levels
- final `Shutdown Energy %`

## Business Rule Baseline

Day classification rule:
- use `workshop_timeline.work_status` to classify the date as `Working`, `Off day`, or `Holiday`
- `Working` is counted as an operation/working day
- `Off day` and `Holiday` are counted in the off-working bucket for the shutdown formula

Source-of-truth rule:
- Electricity energy must still come from `total_energy`
- day classification must use `workshop_timeline.work_status`
- KPI production data from `energy_kpi` remains available for audit/cross-checking
- operation-day working hours must come from `workshop_timeline`

Approved formula rule for V1:
- use the customer-aligned sheet formula (`Approach A`)
- do not apply baseline-adjusted operating-hour subtraction in V1

Approved hour assumptions for V1:
- off-day hours = `24`
- operation-day working hours = the largest MPC/ICO/SAKARI schedule duration for each working day

## Scope

Apply to:
- `periodic` template family only
- weekly + monthly unless business scope is narrowed later

Placement:
- Electricity section
- after the periodic Electricity heatmap
- as the last Electricity sub-section
- with its own sub-heading similar in visibility to `Sensor Monitoring`

Render target:
- HTML view
- PDF render

## Target Output

The report should render a 3-step table similar to the approved worksheet example.

### Step 1
- total electricity used during off days in the period
- number of off-working days in the period
- total electricity used during working days in the period
- number of working days in the period
- average electricity used during off days per day
- average electricity used during working days per day

### Step 2
- average electricity used during off hours per day
- working hours on off days = `24`
- average electricity used during working days per day
- working hours on operation days = largest daily MPC/ICO/SAKARI schedule from `workshop_timeline`
- average electricity used during off hours (`kW`)
- average electricity used during operation hours (`kW`)

### Step 3
- `Shutdown Energy %`

## Backend Data Contract Direction

Proposed backend payload under periodic Electricity:
- `sections.electricity.shutdown_analysis`

Suggested fields:
- `enabled`
- `title`
- `subtitle`
- `formula_version`
- `assumptions`
- `step1_rows`
- `step2_rows`
- `step3_rows`
- audit fields such as:
  - `off_days_count`
  - `operation_days_count`
  - `unknown_days_count`
  - `off_days_total_energy_kwh`
  - `operation_days_total_energy_kwh`
  - `avg_off_day_energy_kwh`
  - `avg_operation_day_energy_kwh`
  - `avg_off_hour_kw`
  - `avg_operation_hour_kw`
  - `shutdown_energy_pct`

## Safety Rules

- do not change Electricity official totals away from `total_energy`
- do not recompute plant official totals from raw area views
- keep sparse-day handling safe when `total_energy` has missing rows
- if production is missing for a date, do not silently classify it as an off day
- keep backend assumptions explicit in the payload
- keep rendering table-driven first; charts can follow later if needed

## Delivery Plan

### Checkpoint 1: docs + checkpoint baseline
- [x] confirm business formula direction with user
- [x] confirm placement in periodic Electricity section
- [x] create task checklist
- [x] update relevant docs
- [x] commit docs checkpoint
- [x] mine project memory

### Checkpoint 2: backend classification object
- [x] classify each periodic date by `Total Product`
- [x] join production-day classification with official electricity daily totals
- [x] compute off-day and operation-day totals and counts
- [x] expose explicit audit counts for unknown / excluded days

### Checkpoint 3: backend calculation object
- [x] compute Step 1 day-level averages
- [x] compute Step 2 hourly rates using approved fixed-hour assumptions
- [x] compute Step 3 `Shutdown Energy %`
- [x] validate divide-by-zero safety and sparse-day safety

### Checkpoint 4: template rendering
- [x] add shutdown-analysis subsection to periodic Electricity HTML template
- [x] add shutdown-analysis subsection to periodic Electricity PDF template
- [x] keep the block after the heatmap and at the end of Electricity section
- [x] tune table readability for A4 width

### Checkpoint 5: validation
- [x] verify weekly output
- [x] verify monthly output
- [x] verify missing `total_energy` day does not break the block
- [x] verify `work_status = Off day` and `Holiday` days are classified into the off-working formula bucket
- [x] verify `work_status = Working` days are classified as operation days
- [x] preview and review HTML/PDF
- [x] commit stable checkpoint
- [ ] mine again
