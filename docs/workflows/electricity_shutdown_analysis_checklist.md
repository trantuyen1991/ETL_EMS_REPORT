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
- if `Total Product = 0`, classify the date as an off-working day
- if `Total Product > 0`, classify the date as an operation day

Source-of-truth rule:
- Electricity energy must still come from `total_energy`
- day classification must use KPI production data from `energy_kpi`

Approved formula rule for V1:
- use the customer-aligned sheet formula (`Approach A`)
- do not apply baseline-adjusted operating-hour subtraction in V1

Approved hour assumptions for V1:
- off-day hours = `24`
- operation-day working hours = `12`

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
- working hours on operation days = `12`
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
- [ ] commit docs checkpoint
- [ ] mine project memory

### Checkpoint 2: backend classification object
- [ ] classify each periodic date by `Total Product`
- [ ] join production-day classification with official electricity daily totals
- [ ] compute off-day and operation-day totals and counts
- [ ] expose explicit audit counts for unknown / excluded days

### Checkpoint 3: backend calculation object
- [ ] compute Step 1 day-level averages
- [ ] compute Step 2 hourly rates using approved fixed-hour assumptions
- [ ] compute Step 3 `Shutdown Energy %`
- [ ] validate divide-by-zero safety and sparse-day safety

### Checkpoint 4: template rendering
- [ ] add shutdown-analysis subsection to periodic Electricity HTML template
- [ ] add shutdown-analysis subsection to periodic Electricity PDF template
- [ ] keep the block after the heatmap and at the end of Electricity section
- [ ] tune table readability for A4 width

### Checkpoint 5: validation
- [ ] verify weekly output
- [ ] verify monthly output
- [ ] verify missing `total_energy` day does not break the block
- [ ] verify `Total Product = 0` days are classified as off days
- [ ] verify non-zero production days are classified as operation days
- [ ] preview and review HTML/PDF
- [ ] commit stable checkpoint
- [ ] mine again
