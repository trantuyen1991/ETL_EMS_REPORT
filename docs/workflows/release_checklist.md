# Release Checklist

Use this checklist before calling a build or report package ready for release.

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

- [ ] Run one daily export and verify `_view.html`, `_pdf_source.html`, and `.pdf` are produced
- [ ] Run one Sunday anchor export and verify weekly report is generated
- [ ] Run one month-end anchor export and verify monthly report is generated
- [ ] Open the final PDF and verify layout width, chart sizing, and table overflow are acceptable
- [ ] Verify staged PDF output is copied back into the canonical `output/reports/` directory

## 4. Documentation and scope

- [ ] Confirm docs still match the live runtime: Chromium/CDP-first PDF flow, canonical `components.report.*` style schema, and `kpi_reporting_rules.md`
- [ ] Confirm project naming stays consistent as `Energy Consumption Reporting System`
- [ ] Confirm CSV export is still documented as planned / not yet wired in production flow
- [ ] Confirm no stale dependency or release note still claims WeasyPrint is the active PDF engine

## 5. Release decision

- [ ] Record tested anchor dates and notable results
- [ ] Record the release candidate commit SHA
- [ ] Get explicit sign-off before tagging or packaging
