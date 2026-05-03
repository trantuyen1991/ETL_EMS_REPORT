# Template Layout Fix - Daily View Sensor Reference Alignment (P11)

## Scope

Push the **daily HTML view** `Sensor Monitoring` group cards closer to the approved reference image while keeping the slice presentation-only.

## Guardrails

- daily HTML view only
- no PDF changes yet
- no periodic view changes yet
- no backend anomaly logic changes
- no sensor ordering/business-rule changes unless required only for layout hooks

## Reference Gaps To Close

- current cards still read more like generic report cards than the polished dashboard reference
- group header needs stronger icon-led identity
- row status should read as status content, not only as a pill
- row dividers / spacing / tint hierarchy should look cleaner and lighter
- card shell should be whiter and calmer, with pastel theme accent rather than a stronger gradient body
- layout should support a future full-width Sakari card without structural rewrite

## Checklist

- [x] Confirm exact template/CSS gaps from current daily sensor card layout
- [x] Add template hooks/macros for group icons and row status/icon treatment
- [x] Refine card shell, header, row divider, and metric/status presentation in `report.css`
- [x] Add/update regression checks for new template hooks
- [x] Render daily sample and capture updated review image
- [x] Summarize remaining differences before any PDF port

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py` → `12 passed`
- `./venv/bin/pytest -q` → `52 passed`
- Daily render anchor: `2025-06-25`
- Review image:
  - `/home/nbt/.openclaw/workspace/audit/render_review_sensor_p11/daily_view_20250625_sensor_metric_table_p11_focus.png`

## Result Summary

- Daily sensor group cards are now materially closer to the reference style:
  - icon-led group header
  - whiter card shell with lighter pastel accent treatment
  - clearer table-like metric rows
  - status icon + label treatment instead of status pill only
- Scope stayed daily-view-only.
- PDF and periodic sensor cards remain untouched.

## Remaining Gap Before PDF Port

- text density is still the main remaining issue
- long reason copy in the status column is still visually tight
- anomaly table below the cards is still functional-heavy rather than presentation-light
