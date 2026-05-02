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
- The periodic cleanup chain was extended through three final follow-up slices:
  - P1: residual electricity builder subtitle cleanup
  - P2: KPI fallback title cleanup
  - P3: template fallback copy cleanup
- Final verification state after the completed cleanup chain: `24 passed` via `./venv/bin/pytest -q`

## Follow-up cleanups completed
- **P1 completed:** electricity residual builder subtitles were normalized to period-aware wording.
- **P2 completed:** KPI fallback/default title `Current period KPI summary` was normalized to `KPI Summary Matrix`.
- **P3 completed:** utility template fallback copy now uses `last period` instead of `previous period` when labels are missing.

## Final conclusion
- The wording cleanup chain for this phase is effectively closed.
- Primary rendered report surfaces and remaining low-risk fallback paths now follow the intended daily and periodic label policy.

## Period detail semantics follow-up (2026-05-02)
- The periodic `Daily Energy Detail` tables were polished further so they read closer to the daily product family without changing backend logic, sorting, or matrix structure.
- P6 aligned the base periodic value hierarchy toward daily semantics:
  - default numeric tone was made more neutral
  - heat tiers were softened away from hard block fills
  - `value-max` stayed artifact-safe in Chrome PDF
  - zero-state stayed subdued but readable
- P7 completed the remaining presentation gap:
  - area identity now reads more clearly inside each table, not only in the title
  - DIODE / ICO / SAKARI blocks now carry distinct area-tinted index/date bands and table surfaces
  - in-table heat separation is stronger, so high/mid/low values scan faster
  - missing (`-`), zero (`0.00`), and very small nonzero states are more clearly separated
  - date/index columns remain visually subordinate after a final small saturation reduction
- Validation result:
  - weekly page 2 improved materially in area identity and cell-state readability
  - monthly page 2 showed no obvious regression in readability or column separation
  - automated regression status remained `43 passed`

## Next workstream
- Next planned workstream: template layout audit by surface/page, starting with the daily PDF output.
- See `docs/workflows/template_layout_audit_master_checklist.md` for the audit order and checks.
