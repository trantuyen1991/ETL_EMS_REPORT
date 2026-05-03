# Template Layout Fix - Daily View Sensor Target Alignment (P12)

## Scope

Rework the **daily HTML view** `Sensor Monitoring` grouped sensor cards so they align much more closely with the approved target image.

## User-Confirmed Gaps

1. colors are still not balanced like the target
2. icons are still incomplete
3. the grouped card layout is still not airy/easy to scan enough
4. current output still carries too much old report structure around the target card area

## Target Direction Locked

- cleaner white cards with light, balanced accent usage
- stronger accent-colored group title identity
- full icon system:
  - group header icon
  - metric icon
  - status icon
- table-style metric rows with clearer breathing room
- separate `Domestic Water` and `Sakari Water` cards
- `Sakari Water` spans full width at the bottom when present
- reduce non-target quick-summary noise above the grouped sensor cards in daily view

## Guardrails

- daily HTML view only
- no PDF changes yet
- no periodic view changes yet
- no anomaly-scoring logic changes
- only minimal data/config changes when required for target card grouping

## Checklist

- [x] Confirm exact target deltas from latest render
- [x] Split `Sakari Water` into its own sensor group card for sensor monitoring display
- [x] Reduce daily quick-summary noise above grouped sensor cards
- [x] Rebalance group/card/title/status/icon styling toward the target
- [x] Add/update regression tests for grouping and template hooks
- [x] Render updated daily sample and capture focused review image
- [x] Summarize what still differs before any PDF port

## Verification

- `./venv/bin/pytest -q tests/test_daily_utility_labels.py tests/test_sensor_monitoring_context.py` → `17 passed`
- `./venv/bin/pytest -q` → `52 passed`
- Daily render anchor: `2025-06-25`
- Review image:
  - `/home/nbt/.openclaw/workspace/audit/render_review_sensor_p12/daily_view_20250625_sensor_metric_table_p12_focus.png`

## Result Summary

- Daily sensor cards are materially closer to the target than P11.
- `Domestic Water` and `Sakari Water` now render as separate grouped cards.
- Daily quick-summary group cards above the detailed grouped cards are removed.
- Group-title color identity and icon coverage are clearer.
- The main remaining mismatch is density: the grouped metric rows still read more table-heavy than the target.
