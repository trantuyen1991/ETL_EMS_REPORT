# UI Polish Summary

## Phase: Weekly / Monthly periodic normalization

### Status
- Completed for the primary rendered weekly/monthly report surfaces.
- Canonical periodic wording is now:
  - weekly: `This Week / Last Week`
  - monthly: `This Month / Last Month`

### Completed slices
1. **Electricity periodic audit**
   - reviewed weekly/monthly wording drift across builder and templates

2. **Electricity periodic fix #1**
   - normalized top-10 grouped headers to resolved period labels
   - normalized top-10 note wording away from generic `current-period`

3. **Electricity periodic fix #2**
   - normalized periodic electricity chart subtitles and legend labels to period-aware wording

4. **Periodic label policy normalization**
   - standardized shared weekly/monthly labels to `This Week / Last Week` and `This Month / Last Month`
   - updated related docs and tests to lock the policy

5. **Utility periodic audit**
   - confirmed template layer was mostly aligned
   - isolated drift to builder chart wording

6. **Utility periodic fix #1**
   - normalized utility periodic comparison legends
   - normalized utility periodic comparison, deviation, and trend subtitles
   - normalized utility periodic mix title

7. **KPI periodic audit**
   - confirmed rendered periodic KPI cards, summary headers, date chip, and main chart wording are already aligned
   - no immediate KPI periodic wording fix slice required

### Result by section
- **Electricity:** primary periodic wording aligned on both template and builder paths used in weekly/monthly rendering.
- **Utility:** primary periodic wording aligned in the rendered chart layer.
- **KPI:** rendered periodic wording already aligned; only non-surfacing fallback/default builder strings remain.

### Verification status
- Latest code-changing periodic UI checkpoint passed: `19 passed` via `./venv/bin/pytest -q`
- KPI periodic audit was docs-only and did not change runtime behavior

## Recommended small cleanups

### P1. Normalize remaining periodic electricity residual subtitles in builder
Residuals still use generic wording in `src/services/report_builder_service.py`, for example:
- `Sorted by current-period consumption within this area.`
- `Total and workshop change vs previous period`

These should be switched to resolved period-aware wording for consistency with the completed periodic policy.

### P2. Normalize non-surfacing KPI fallback/default titles
`Current period KPI summary` still exists in KPI builder fallback/default payloads. It does not currently surface in live templates, but changing it to a neutral or canonical title would reduce future drift risk.

### P3. Remove fallback display copy that still mentions generic `previous period`
A few template fallbacks still contain generic display text such as `previous period` when labels are missing. These are low risk because the normal render path provides labels, but they are worth cleaning if we want stricter wording consistency.
