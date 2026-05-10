# Daily Excel Export Checklist

## Scope lock

- Output target: **one `.xlsx` workbook for the daily report only**
- Do not export weekly or monthly workbooks in v1
- Do not spend time on workbook styling in v1
- Prioritize data completeness, stable generation, and clear sheet separation

## Checkpoints

- [ ] **Checkpoint 1, Audit + workbook contract**
  - inspect current daily report flow and artifact creation points
  - list the exact workbook sheets for v1
  - define columns and source mapping for each sheet
  - confirm what is intentionally excluded from v1

- [ ] **Checkpoint 2, Dependency + service skeleton**
  - add the Excel writer dependency
  - create a dedicated `ExcelExportService`
  - keep export logic backend-side, not template-side

- [ ] **Checkpoint 3, Summary sheet export**
  - `Meta`
  - `Electricity_Summary`
  - `Utility_Summary`
  - `KPI_Summary`

- [ ] **Checkpoint 4, Detail sheet export**
  - `Electricity_Top_Meter`
  - `Electricity_Detail`
  - `Utility_Detail`
  - `KPI_Detail`

- [ ] **Checkpoint 5, Batch integration**
  - generate the workbook only for `period_type == "daily"`
  - keep weekly/monthly output unchanged
  - archive the `.xlsx` alongside the current daily artifacts

- [ ] **Checkpoint 6, Verification**
  - confirm daily run generates `.xlsx`
  - confirm workbook opens successfully
  - confirm sheet count and names match the contract
  - confirm weekly/monthly do not generate Excel

- [ ] **Checkpoint 7, Documentation + closeout**
  - update README and export docs to match the implemented flow
  - create a clean checkpoint commit
  - re-mine MemPalace

## v1 exclusions

- Sensor Monitoring sheets
- chart-only / heatmap-presentation-only data
- workbook styling / visual polish beyond plain headers and raw values
