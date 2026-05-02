# Template Layout Fix Checklist

## Slice: Period detail daily-semantics alignment P6

### Goal
Align periodic `Daily Energy Detail` tables more closely to the daily visual semantics without changing sorting, matrix structure, or backend logic.

### Scope lock
- [x] CSS/tokens only
- [x] No backend logic changes
- [x] No sorting changes
- [x] No matrix/pagination structure changes

### Target alignment
- [x] Base numeric text tone should move closer to daily neutral readability
- [x] Heat ramp should feel softer and closer to daily contrast progression
- [x] `value-max` emphasis should feel strong but artifact-safe
- [x] Zero-state should stay de-emphasized without looking disconnected
- [x] Weekly and monthly re-render should confirm no new readability regression

### Observed result
- [x] First implementation pass successfully softened the tone but underpowered `value-max` emphasis
- [x] Revised pass recovered scanability for top cells while keeping the calmer daily-like tone
- [x] Weekly page 2 now reads closer to daily semantics without losing matrix readability
- [x] Monthly sample showed no obvious regression in tone, contrast, or date/meter separation
