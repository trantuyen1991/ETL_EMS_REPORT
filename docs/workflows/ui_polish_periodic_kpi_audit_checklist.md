# UI Polish Checklist

## Slice: KPI weekly/monthly wording audit

- [x] Recall periodic KPI context from MemPalace
- [x] Audit KPI weekly/monthly cards, charts, and tables for wording drift
- [x] Summarize what is already aligned and what still drifts

## Findings

### Already aligned
- KPI periodic cards already render `labels.current_period` and `labels.previous_period`, so weekly/monthly cards inherit `This Week / Last Week` and `This Month / Last Month` correctly.
- KPI periodic summary-matrix column headers already use shared period labels directly in both view and PDF templates.
- KPI builder chart layer is already period-aware for periodic mode:
  - compare bar subtitle uses resolved labels
  - compare bar legend series use resolved labels
  - waterfall subtitle uses resolved labels
  - variance title uses resolved labels
- KPI periodic date chip already uses `period.label` and `period.comparison_label`.

### Low-priority drift
- `Current period KPI summary` still exists in builder fallback/default data, but the live templates hardcode `KPI Summary Matrix`, so this does not currently surface in the rendered KPI section.
- A few internal/default helper strings still mention `Today` / `Yesterday` in parameter names or default arguments, but periodic execution overrides them with resolved weekly/monthly labels before rendering.

### Audit conclusion
- No meaningful weekly/monthly KPI wording drift is currently surfacing in the rendered periodic report.
- KPI does not need an immediate periodic wording fix slice right now.
