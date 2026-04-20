# KPI Report Ruler

## 1. Purpose
This file defines the decision rules for KPI reporting logic.

It exists to keep KPI aggregation, coverage evaluation, and daily presentation aligned with approved business behavior.

---

## 2. Core Principles

### 2.1 Coverage First
KPI reporting must follow coverage-first logic.

The system should prefer:
- correct partial coverage
- explicit uncovered ranges
- visible missing status

over artificial completeness.

### 2.2 No Prorating
Do not split `Week`, `Month`, or `Year` rows into smaller daily values.

Do not prorate any KPI block across uncovered days.

### 2.3 No Reconstruction from Raw Energy Views
KPI values and official total values used for KPI reporting must not be recomputed from raw electricity views.

KPI reporting must use pre-calculated values already stored in `energy_kpi`.

---

## 3. Source of Truth

### 3.1 Official Source
The `energy_kpi` table is the source of truth for KPI reporting.

This applies to:
- plant KPI-related energy totals
- area KPI-related energy totals
- production values
- KPI values
- coverage-ready reporting blocks

### 3.2 Latest Row Rule
If multiple rows represent the same reporting block, always select the row with the latest `dt_lastupdate`.

Older duplicates must be ignored.

---

## 4. Coverage Hierarchy

KPI coverage must follow this priority order: Day > Week > Month > Year

Rules:

- prefer more granular rows over less granular rows
- do not let broader rows override narrower approved rows
- do not double count overlapping coverage

---

## 5. Selection Rules

### 5.1 Use Only Fully Matching Blocks

Only use rows that fully match the intended reporting block.

Examples:

- a `Day` row can be used for one exact day
- a `Week` row can be used for one full weekly block
- a `Month` row can be used for one full monthly block

### 5.2 Prefer Detailed Coverage

If a day is already covered by a valid `Day` row, do not replace it with a broader block.

### 5.3 Use Broader Blocks Only as Stored Blocks

A `Week`, `Month`, or `Year` row may be used only as its own full stored block.

It must not be broken into synthetic daily values.

---

## 6. Rejection Rules

Reject a KPI row when:

- it only partially overlaps the report range
- it requires prorating
- it would override already covered more detailed data
- it is an outdated duplicate with older `dt_lastupdate`

### Custom Range Rule

Custom ranges are the strictest case.

If a stored KPI block does not fully fit inside the custom range, it must not be used.

Example:

- report range: `2025-04-10 -> 2025-04-20`
- stored row: full month `2025-04-01 -> 2025-04-30`

Result:

- reject the monthly row
- do not estimate partial KPI from it

---

## 7. Coverage Result Rules

Each KPI result must expose:

- `coverage_display`
- `coverage_note`
- `uncovered_ranges`
- `is_complete`

Coverage may be:

- full
- partial
- missing

Partial coverage is valid and must be shown explicitly.

The system must not hide missing KPI days just to make the report look complete.

---

## 8. Daily Presentation Rules

### 8.1 Dense Daily Rows

Daily KPI detail must render all dates in the report period, including uncovered dates.

### 8.2 Missing Rows

For uncovered dates:

- keep the row
- show missing status
- show "-" for unavailable KPI, production, and energy values

### 8.3 Daily Detail Content

Daily KPI detail should include:

- date
- status
- source
- plant production
- area production
- plant energy
- area energy
- plant KPI
- area KPI
- coverage note

### 8.4 Display Philosophy

Daily KPI detail is both:

- a reporting table
- a debugging / validation surface for KPI coverage behavior

