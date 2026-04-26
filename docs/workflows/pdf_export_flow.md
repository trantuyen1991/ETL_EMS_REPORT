# PDF Export Flow

## Overview

This document describes the current stable PDF export pipeline confirmed on the baseline tag `stable-pdf-export-20260426`.

The goal of this flow is simple:

1. render report HTML from backend-built context
2. stage the PDF source HTML in a safe print directory
3. let Chromium wait until charts are ready
4. print a stable PDF without white charts

This workflow is intentionally conservative. Several details that may look redundant are part of the current stability baseline and should not be changed casually.

---

## 1. End-to-End Flow

```text
python3 -m src.main
    ↓
run_production()
    ↓
_run_report_batch()
    ↓
build report_context
    ↓
render view HTML + PDF source HTML
    ↓
write PDF source into project output and staging output
    ↓
Chromium headless prints staged HTML into staged PDF
    ↓
copy final PDF back into output/reports/
```

---

## 2. Entry Point -> Render -> Export

### Runtime entry point

- `src/main.py`
- `run_production()` is the production entry point
- `__main__` calls `run_production()`

### Batch render flow

`run_production()` resolves configuration, then calls `_run_report_batch()`.

`_run_report_batch()`:

1. resolves which report periods must be exported for the effective anchor day
2. builds report context for each report
3. calls `_render_report_artifacts()`
4. writes HTML outputs
5. calls `export_pdf_from_html()` to create the final PDF

### Template selection

`_select_template_bundle()` chooses the template family by report type:

- `daily` uses dedicated daily templates
- `weekly` and `monthly` use the shared `periodic` family

---

## 3. Template Mapping

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
- PDF shell:
  - `src/templates/report/base/base_pdf.html`

---

## 4. Output Paths

For each report, `_render_report_artifacts()` writes several files.

### Project output

These files stay under the normal project output directory:

- `output/reports/<export_stem>_view.html`
- `output/reports/<export_stem>_pdf_source.html`
- `output/reports/<export_stem>.pdf`

### Staging output

The PDF print flow also writes staging artifacts into a safe non-hidden directory:

- `<staging_output_dir>/<export_stem>_pdf_source.html`
- `<staging_output_dir>/<export_stem>.pdf`

This staging path exists because Chromium headless is more reliable when printing from a normal non-hidden location.

### Path responsibility

- `project_output_dir` is the canonical artifact location inside the repo output
- `staging_output_dir` is the print-safe location used only for Chromium staging and print

---

## 5. Chromium Command

The current command is built in `src/services/pdf_service.py`.

Current flags:

- `--headless`
- `--disable-gpu`
- `--no-sandbox`
- `--hide-scrollbars`
- `--run-all-compositor-stages-before-draw`
- `--virtual-time-budget=45000`
- `--window-status=ready`
- `--print-to-pdf=<output_pdf_path>`
- `file://<staging_html_path>`

### Why these flags matter

- `--headless`
  - run Chromium without a visible UI
- `--disable-gpu`
  - avoid GPU-related rendering differences in headless mode
- `--no-sandbox`
  - required by the current environment
- `--hide-scrollbars`
  - keep print output clean
- `--run-all-compositor-stages-before-draw`
  - helps Chromium complete compositor work before capture
- `--virtual-time-budget=45000`
  - gives the page enough virtual time to finish layout and chart rendering
- `--window-status=ready`
  - waits until the page explicitly marks itself ready
- `--print-to-pdf=...`
  - writes the PDF to the staging output file
- `file://...`
  - prints the staged local HTML file

---

## 6. Chart Lifecycle

The PDF chart lifecycle is intentionally different from the normal view page.

### Stable PDF chart flow

1. the PDF template renders chart containers and chart config data
2. `window.__scheduleReportChartInit(initFn)` waits until the page has loaded
3. after load, chart init is deferred until layout is stable
4. each section initializes its charts
5. rendered charts are frozen into static SVG or image content
6. Chromium prints the frozen result

### Chart init sequence

Inside each PDF chart section, the current stable sequence is:

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

This is part of the stable print pipeline and should be preserved.

### Animation

PDF charts force:

- `animation: false`

This avoids a print happening while chart animation is still mid-frame.

### Freeze flow

After charts render, `window.__freezeReportCharts()` converts them into static content:

- prefer `renderToSVGString()`
- fallback to `getDataURL()` if needed
- replace the live chart DOM with frozen SVG or image content

The freeze step is a major part of chart-print stability.

---

## 7. Readiness Mechanism

The PDF shell in `base_pdf.html` uses a simple readiness signal.

### Current behavior

- set `window.status = "loading"` at the start
- wait for `window.load`
- wait an additional `3000ms`
- set `window.status = "ready"`

Chromium waits on:

- `--window-status=ready`

### Why this matters

This extra delay gives the PDF page time to:

- finish layout
- let chart init retries complete
- freeze chart output before print starts

The delay is intentionally simple and should not be shortened casually.

---

## 8. Why the Stable Settings Matter

### Disable animation

PDF is a snapshot, not an interactive page.

If animation is enabled, Chromium may print before the chart reaches its final state. That can produce partial or blank output.

### Use SVG renderer

SVG output is more deterministic for print and works well with the freeze step.

### Freeze chart output

Printing a live chart instance is riskier than printing frozen SVG or image markup.

The freeze step reduces the chance of:

- repaint timing issues
- live resize side effects
- headless compositor races

---

## 9. Known Pitfalls

### Race condition during headless print

If Chromium prints before charts are fully rendered or frozen, the PDF may contain white chart areas.

### Container size equals zero

If a chart initializes before the container has real width and height, ECharts may render incorrectly or not render at all.

### Animation not finished

Animation introduces timing uncertainty. For PDF this is unnecessary risk, so it stays off.

### Printing from the wrong location

Printing directly from hidden workspace paths is less reliable than printing from the staging directory.

### Changing multiple timing mechanisms at once

Changing init timing, readiness delay, renderer, and freeze flow together makes regressions much harder to isolate.

---

## 10. DO NOT CHANGE

These items are part of the current stable baseline and should only be changed with focused regression testing:

- Chromium flags in `src/services/pdf_service.py`
- `--window-status=ready`
- the `window.status` readiness flow in `base_pdf.html`
- the `3000ms` readiness delay after `window.load`
- the staging output print flow
- PDF chart `renderer: "svg"`
- PDF chart `animation: false`
- the `dispose() -> init() -> setOption() -> resize() -> flush()` sequence
- the freeze flow in `window.__freezeReportCharts()`
- the separation between interactive view charts and PDF print charts

---

## 11. Debug Guide

When a PDF chart appears white, use a narrow debugging process.

### Check the generated artifacts

1. open `output/reports/*_pdf_source.html`
2. open the staging `*_pdf_source.html`
3. compare whether the expected chart markup is already present before print

### Check the first failing pages

Always inspect:

- daily page 1
- weekly page 1
- utility pages
- KPI pages

### Dump DOM from Chromium

Useful approach:

1. run Chromium headless against the staged HTML
2. use `--dump-dom` to inspect the final DOM Chromium sees
3. check whether the chart container contains frozen SVG or only an empty wrapper

### Screenshot the staged HTML

If needed:

1. open the staged HTML with Chromium headless
2. capture a screenshot
3. compare screenshot vs PDF result

If screenshot looks correct but PDF does not, the problem is likely in print timing rather than in chart init itself.

---

## 12. Regression Test Checklist

After any future PDF-related change:

1. run `python3 -m src.main` five times
2. verify daily page 1 layout
3. verify weekly page 1 layout
4. verify electricity charts are visible
5. verify utility pages are visible
6. verify KPI pages are visible
7. confirm no white chart blocks appear intermittently

Recommended quick log format:

- run1: daily ok/fail, weekly ok/fail
- run2: daily ok/fail, weekly ok/fail
- run3: daily ok/fail, weekly ok/fail
- run4: daily ok/fail, weekly ok/fail
- run5: daily ok/fail, weekly ok/fail

---

## 13. Stable Baseline Reference

Current stable baseline:

- tag: `stable-pdf-export-20260426`

Use this tag as the reference point before changing PDF timing, renderer choice, chart lifecycle, or Chromium print behavior.
