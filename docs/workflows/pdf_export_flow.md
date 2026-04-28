# PDF Export Flow

## Overview

This document describes the current stabilized PDF export workflow for `02_MySQL` after the intermittent missing-chart investigation completed on 2026-04-27 and the document-shrink investigation completed on 2026-04-28.

The main outcomes of those investigations were:

- PDF chart init must not be kicked off with `requestAnimationFrame(...)`
- raw Chromium `--print-to-pdf` defaults do not provide enough print control for stable family-to-family scaling
- the stable kickoff now uses `setTimeout(run, 100)` after `window.load`
- the stable print path now prefers Chrome DevTools Protocol `Page.printToPDF` with explicit `scale=1.0` and `preferCSSPageSize=true`
- wide periodic tables must be kept inside document width or Chromium may shrink the whole exported PDF

This workflow should be treated as the current print baseline.

---

## 1. End-to-End Flow

```text
python3 -m src.main
    ↓
run_production()
    ↓
_run_report_batch()
    ↓
resolve scheduled periods for the anchor day
    ↓
build report_context per report
    ↓
render view HTML + PDF source HTML
    ↓
write canonical artifacts into output/reports/
    ↓
write staged PDF source HTML into Chromium-safe staging directory
    ↓
Chromium headless prints staged HTML into staged PDF
    ↓
copy final PDF back into output/reports/
```

---

## 2. Runtime Entry Points

### Production entry point

- `src/main.py`
- `run_production()` is the normal production entry point
- `__main__` calls `run_production()`

### Batch render flow

`_run_report_batch()` does the following:

1. resolve the effective anchor day
2. determine which report periods must be exported for that day
3. build backend report context for each report
4. render both view HTML and PDF source HTML
5. print the staged PDF source with Chromium
6. copy the staged PDF back into the canonical output directory

---

## 3. Period Scheduling Rules

Handled by `src/services/period_service.py`.

Rules:

- always export `daily`
- export `weekly` only when the anchor day is **Sunday**
- export `monthly` only when the anchor day is **month-end**
- if both conditions are true, export all applicable reports in one run

Important clarification:

- there is no separate `weekly_previous` file
- previous-week and previous-month values are comparison data rendered inside the weekly or monthly report itself

---

## 4. Template Mapping

### View templates

- Daily view:
  - `src/templates/report/view/report_view_daily.html`
- Weekly / monthly view:
  - `src/templates/report/view/report_view_periodic.html`

### PDF templates

- Daily PDF:
  - `src/templates/report/pdf/report_pdf_daily.html`
- Weekly / monthly PDF:
  - `src/templates/report/pdf/report_pdf_periodic.html`

### Base shells

- View shell:
  - `src/templates/report/base/base_view.html`
  - includes `assets/report.css`
- PDF shell:
  - `src/templates/report/base/base_pdf.html`
  - includes `assets/report_pdf_base.css` first
  - then includes `assets/report_pdf.css` as the compact print override layer

### CSS layer intent

The CSS split is intentional, because the project renders two different HTML artifacts and one final print-tuned presentation mode:

1. view HTML
   - screen-oriented layout
   - responsive spacing
   - interactive chart behavior

2. PDF source HTML (`pdfBase`)
   - print-safe baseline for the document Chromium will capture
   - same overall product identity as the view, but without relying on screen-only assumptions

3. compact PDF override (`pdfCompact`)
   - last-mile compression for A4 pagination
   - tighter card heights, smaller gaps, and denser chart/table layout where print requires it

---

## 5. Output and Staging Paths

For each report, `_render_report_artifacts()` writes several files.

### Canonical project output

- `output/reports/<export_stem>_view.html`
- `output/reports/<export_stem>_pdf_source.html`
- `output/reports/<export_stem>.pdf`

### Chromium staging output

The PDF print flow also writes staging artifacts into a Chromium-safe non-hidden directory:

- `<staging_output_dir>/<export_stem>_pdf_source.html`
- `<staging_output_dir>/<export_stem>.pdf`

### Staging resolution rule

`_resolve_pdf_staging_dir()` resolves the staging directory in this order:

1. `PRINT_STAGING_DIR` if explicitly configured
2. `OUTPUT_DIR` if it is a non-hidden path
3. `project_output_dir` if it is non-hidden
4. fallback to `~/Reports`

Responsibility split:

- `project_output_dir` is the canonical report artifact location
- `staging_output_dir` is the print-safe location used only for Chromium staging and print

---

## 6. Chromium Print Path

Built in `src/services/pdf_service.py`.

### Primary path

The current primary print path uses Chrome DevTools Protocol.

Key controls:
- `Emulation.setEmulatedMedia` with `media=print`
- `Page.printToPDF`
- `scale=1.0`
- `preferCSSPageSize=true`
- `printBackground=true`

This path exists to avoid document-level auto-fit differences between report families.

### Fallback path

If CDP print fails, the service falls back to the legacy Chromium CLI path:

- `--headless`
- `--disable-gpu`
- `--no-sandbox`
- `--hide-scrollbars`
- `--run-all-compositor-stages-before-draw`
- `--virtual-time-budget=45000`
- `--window-status=ready`
- `--print-to-pdf=<output_pdf_path>`
- `file://<staging_html_path>`

The fallback should remain available, but it is no longer the preferred stability baseline.

---

## 7. Stable PDF Chart Lifecycle

The PDF chart lifecycle is intentionally different from the normal interactive view page.

### Stable flow

1. render chart containers and chart config into the PDF template
2. wait for `window.load`
3. kick off chart init with `setTimeout(run, 100)`
4. each section measures chart container width and height
5. initialize ECharts with `renderer: "svg"`
6. force `animation: false`
7. `setOption(...)`
8. `resize(...)`
9. `chart.getZr().flush()`
10. freeze the live chart into static SVG markup
11. mark the page ready for Chromium print

### Why `setTimeout(run, 100)` matters

This was the key stabilization change.

Previous behavior:

- chart init kickoff used `requestAnimationFrame(...)`

Observed problem:

- Chromium headless intermittently did not execute the RAF callback before `window.status = "ready"`
- some runs never reached chart init / freeze
- resulting PDFs sometimes had missing charts

Current stable behavior:

- chart init kickoff uses `setTimeout(run, 100)`
- repeated regression batches showed stable chart rendering across:
  - weekday anchors
  - weekend anchors
  - month-end anchors
- print now also runs through CDP with explicit page-size and scale control before any fallback to legacy CLI mode

---

## 8. PDF Chart Init Sequence

Inside each PDF chart section, the stable sequence is:

1. check container width and height
2. if an old chart instance exists, `dispose()` it
3. `echarts.init(..., { renderer: "svg", width, height })`
4. build option with `animation: false`
5. `setOption(option, true)`
6. `resize({ width, height })`
7. `chart.getZr().flush()`
8. collect chart references for freeze
9. call `window.__freezeReportCharts(...)`

### Renderer

PDF charts use:

- `renderer: "svg"`

### Animation

PDF charts force:

- `animation: false`

This avoids printing while chart animation is still mid-frame.

---

## 9. Freeze Flow

After charts render, `window.__freezeReportCharts()` converts them into static content:

- prefer `renderToSVGString()`
- fallback to `getDataURL()` if needed
- replace the live chart DOM with frozen SVG or image content

The stabilized regression runs on the current baseline consistently produced frozen SVG output and no `freeze.empty` events during the verified batches.

---

## 10. Readiness Mechanism

The PDF shell in `base_pdf.html` uses a simple readiness signal.

### Current behavior

- set `window.status = "loading"` at the start
- wait for `window.load`
- allow chart init to start through `setTimeout(run, 100)`
- wait an additional `15000ms`
- set `window.status = "ready"`

Chromium waits on:

- `--window-status=ready`

### Why the delay still exists

The delay is still intentionally conservative so that Chromium does not print while sections are still initializing or freezing.

The stable fix was **not** reducing the delay. The stable fix was replacing the unreliable RAF kickoff.

---

## 11. Key Lessons Learned

### 11.1 Root cause

The intermittent missing-chart bug was primarily caused by:

- unstable chart-init kickoff using `requestAnimationFrame(...)` inside headless Chromium print flow

### 11.2 Not the real root cause

The issue was **not** solved by:

- simply increasing the readiness delay
- changing chart data logic
- changing backend report context

### 11.3 Practical rule

For this PDF workflow:

- do not use RAF as the primary chart-init trigger
- use a deterministic timer-based kickoff after `window.load`

---

## 12. Known Pitfalls

### Race condition during headless print

If Chromium prints before charts are initialized and frozen, the PDF may contain white or missing chart areas.

### Container size equals zero

If a chart initializes before the container has real width and height, ECharts may render incorrectly or not render at all.

### Animation not finished

Animation introduces timing uncertainty. For PDF this is unnecessary risk, so it stays off.

### Hidden-path staging risk

Printing from hidden or unusual workspace paths is less reliable than printing from a normal staging directory.

### Changing multiple timing mechanisms at once

Changing kickoff timing, readiness delay, renderer, and freeze flow together makes regressions much harder to isolate.

---

## 13. DO NOT CHANGE CASUALLY

These items are part of the current stable print baseline and should only be changed with focused regression testing:

- Chromium flags in `src/services/pdf_service.py`
- `--window-status=ready`
- the `window.status` readiness flow in `base_pdf.html`
- the `15000ms` readiness delay after `window.load`
- timer-based kickoff using `setTimeout(run, 100)`
- PDF chart `renderer: "svg"`
- PDF chart `animation: false`
- the `dispose() -> init() -> setOption() -> resize() -> flush()` sequence
- the freeze flow in `window.__freezeReportCharts()`
- separation between interactive view charts and PDF print charts

---

## 14. Regression Test Checklist

After any future PDF-related change:

1. run `python3 -m src.main` five times
2. verify daily page 1 layout
3. verify weekly page 1 layout when the anchor is Sunday
4. verify monthly page 1 layout when the anchor is month-end
5. verify electricity charts are visible
6. verify utility charts are visible
7. verify KPI charts are visible
8. confirm no white or missing chart blocks appear intermittently

Recommended regression anchors:

- one normal weekday
- one Sunday
- one month-end day

---

## 15. Validation Reference

Validated stabilization batches were run on the main project with these representative anchors:

- weekday: `2025-05-14`
- weekend / Sunday: `2025-05-18`
- month-end: `2025-05-31`

Observed result:

- PDF sizes remained within a tight stable range per report type
- no large fail/pass size split remained
- visual review confirmed charts were consistently present in the tested batches
