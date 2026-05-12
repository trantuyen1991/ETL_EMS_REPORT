# Release Checklist

Use this checklist before calling a build or report package ready for release.

Companion runbook: `docs/workflows/release_runbook.md`

## 1. Runtime and configuration

- [ ] Confirm the active working copy is `/home/nbt/workspace/02_MySQL`
- [ ] Recreate / validate the virtual environment after any path move
- [ ] Confirm Chrome or Chromium is available on the host for PDF export
- [ ] Confirm `REPORT_ANCHOR_DATE`, `OUTPUT_DIR`, and optional `PRINT_STAGING_DIR` are set correctly
- [ ] Confirm the effective print path is non-hidden when PDF export is tested

## 2. Automated checks

- [ ] Run `./venv/bin/pytest -q`
- [ ] Confirm period resolution tests pass
- [ ] Confirm style-config load / fallback tests pass
- [ ] Confirm render pipeline smoke tests pass
- [ ] Confirm PDF service CDP-first and legacy-fallback tests pass

## 3. Manual smoke checks

- [ ] Run one daily export and verify `.html`, `.pdf`, and `.xlsx` are produced under the correct monthly subfolders (`view_html`, `pdf_source_html`, `pdf`, `excel`)
- [ ] Run one Sunday anchor export and verify weekly report is generated
- [ ] Run one month-end anchor export and verify monthly report is generated
- [ ] Open the final PDF and verify layout width, chart sizing, and table overflow are acceptable
- [ ] Verify staged PDF output is copied into the canonical monthly `OUTPUT_DIR/YYYY_MM/pdf/` directory
- [ ] Verify filenames sort by prefix order: `01_monthly`, `02_weekly`, `03_daily`

## 4. Documentation and scope

- [ ] Confirm docs still match the live runtime: Chromium/CDP-first PDF flow, canonical `components.report.*` style schema, and `kpi_reporting_rules.md`
- [ ] Confirm project naming stays consistent as `Energy Consumption Reporting System`
- [ ] Confirm daily Excel export is documented as implemented in production flow, daily-only in v1, with weekly/monthly Excel still out of scope
- [ ] Confirm no stale dependency or release note still claims WeasyPrint is the active PDF engine

## 5. Release decision

- [ ] Record tested anchor dates and notable results
- [ ] Record the release candidate commit SHA
- [ ] Get explicit sign-off before tagging or packaging
