# Web GUI Phase 1 Checklist

## Purpose
Track the approved preparation and implementation path for the FastAPI Web GUI phase.

---

## Phase 0 — Release / branch preparation
- [x] confirm the current report-stable baseline commit to tag
- [x] create a release tag for the report-stable baseline
- [x] create a dedicated feature branch for Web GUI work
- [x] record branch/tag names in project docs if they become official

Current official names:
- baseline tag: `v0.9-report-stable`
- Web GUI branch: `feature/web-gui-phase1`

---

## Phase 1 — Shared execution-model refactor
- [x] isolate reusable period-resolution logic from the current main flow
- [x] define the canonical resolved-period contract (`period_type`, `anchor_date`, `start_date`, `end_date`)
- [x] extract a shared pipeline/service entry point for report execution
- [x] ensure the shared pipeline can be called without editing `.env`
- [x] keep current CLI/scheduled flow working through the extracted shared path
- [x] define where HTML render output should be returned in-memory versus written to disk
- [x] decide whether browser refresh should reuse the full batch pipeline or a lighter report-only execution path

Implemented prep slice:
- `src/services/report_engine_service.py` now owns the shared batch + browser execution path.
- `src.main` remains the systemd/service-timer entrypoint, but now delegates to `ReportEngineService`.
- browser `/reports` uses a lighter HTML-only render path instead of full PDF/export batch execution.

---

## Phase 1.1 — Browser period rules
- [x] implement backend validation rules for `daily`
- [x] implement backend validation rules for `weekly`
- [x] implement backend validation rules for `monthly`
- [x] decide whether `custom` is included in the first browser rollout or deferred
- [x] if `custom` is included, implement and validate the inclusive 31-day limit
- [x] define clear backend error responses for invalid requests

Current product decision:
- `custom` is deferred from the phase-1 browser release.
- validation code may remain in the backend for future use, but phase-1 UI should focus on `daily`, `weekly`, and `monthly` only.

---

## Phase 1.2 — CSV contract
- [ ] choose one explicit meaning for `Export CSV`
- [ ] document the CSV payload contract
- [ ] define filename rules by period type
- [ ] define whether CSV is generated from raw rows, normalized rows, or report-ready tabular rows

Current product decision:
- CSV is not part of the active phase-1 UI until the payload contract is explicitly approved.
- the placeholder route may remain reserved internally, but the browser toolbar should not expose an Export CSV action for now.

---

## Phase 2 — FastAPI web app
- [x] create `src/web_app.py`
- [x] create a thin web route layer
- [x] add `GET /`
- [x] add `GET /reports`
- [x] add `GET /reports/download-zip`
- [x] add `GET /reports/export-csv`
- [x] add `GET /health`
- [x] wire Jinja2 template rendering for the report page

Current prep note:
- `/reports/download-zip` now packages the existing backend-built month folder for the selected timeline.
- `/reports/export-csv` remains an internal 501 placeholder until the CSV contract is finalized.

---

## Phase 2.1 — Web UI controls
- [x] add filter bar layout
- [x] add dynamic input switching by period type
- [x] add frontend guard rails for invalid custom ranges
- [x] add `Refresh` button flow
- [x] add template switch between `view.html` and `pdf_source.html`
- [x] replace browser-print action with backend package download action
- [x] remove `Export CSV` from the active phase-1 toolbar
- [x] add print CSS to hide filter/action controls
- [x] auto reload preview when only `template_mode` changes
- [x] compact the shell with a collapsible `Filters & Actions` disclosure
- [x] keep action buttons on one row
- [x] hide outer-page scroll while preserving iframe/report scroll

Current implementation note:
- `/reports` now serves a shell page with a filter toolbar and embedded report iframe.
- phase-1 toolbar is now limited to `daily`, `weekly`, `monthly`, a template-mode switch, `Refresh`, and `Download Report ZIP`.
- the current shell uses a centered, compact filter surface with hover hints/tooltips and disclosure-style controls by default.

---

## Phase 2.2 — Verification
- [x] `daily` renders one selected day correctly
- [x] `weekly` resolves Monday -> Sunday correctly
- [x] `monthly` resolves first day -> last day correctly
- [x] `view.html` surface renders through the browser route
- [x] `pdf_source.html` surface renders through the browser route
- [x] ZIP download returns the selected month package
- [x] CLI/report flow remains intact after the web layer is added

---

## Phase 3 — Post-phase follow-up
- [x] review request latency and ETL cost
- [x] decide where caching belongs for browser-driven refresh
- [x] implement service-layer preview cache and ZIP freshness reuse
- [x] validate warm-cache behavior over real HTTP
- [ ] define future JSON/API shape for ThingsBoard integration
- [ ] decide whether realtime telemetry should stay separate from report analytics

Current phase-3 findings:
- shell route `/reports` is lightweight when it only renders the toolbar shell, about `0.005s` in local curl timing.
- embedded report renders currently re-bootstrap config + DB runtime on each request and are not cached.
- observed local route timings on the current host were approximately:
  - `daily view`: `1.13s`
  - `daily pdf_source`: `1.12s`
  - `weekly view`: `1.26s`
  - `monthly view`: `1.48s`
  - `monthly pdf_source`: `1.51s`
- warm ZIP download for an already-built month package was about `0.21s`.
- cold ZIP generation can be much more expensive because the route now renders the requested report package on demand before zipping when the month folder does not exist yet.

Chosen cache strategy for the current Web GUI phase:
- do not add a cache layer to `/health` or to the lightweight shell rendering path.
- place cache inside the shared service layer (`ReportEngineService`), not in FastAPI route handlers.
- use two primary cache units for browser preview:
  - `report context cache` keyed by normalized period input (`period_type`, `anchor_date`, `start_date`, `end_date`) plus a cache-version fingerprint.
  - `rendered HTML cache` keyed by the same normalized period key plus `template_mode` (`view` or `pdf_source`).
- use one artifact cache rule for ZIP download:
  - if the month package ZIP already exists and is newer than the month folder contents, serve it directly.
  - if the month folder exists but the ZIP is stale, rebuild only the ZIP.
  - if the month folder does not exist yet, render the requested package on demand, then zip it.
- the `Refresh` button is now implemented as an explicit cache-bypass action through `force_refresh=1`.
- template-only switching does not bypass cache, so the UI can reuse a warm context/HTML path immediately.
- initial safe TTL for preview caches remains `5 minutes` in-process.
- validated local result after implementation:
  - forced/cold daily preview: about `1.11s`
  - warm daily preview: about `0.008s` to `0.009s`
- cache invalidation should at minimum react to:
  - explicit refresh bypass
  - process restart/deploy restart
  - style/config version changes included in the cache fingerprint
  - successful on-demand rerender replacing the corresponding HTML/ZIP artifacts

---

## Current decisions already approved
- [x] use FastAPI + Jinja2 rather than React/Vue for the first Web GUI phase
- [x] keep ThingsBoard out of the current implementation scope
- [x] treat the new phase as an execution-model refactor, not only a UI feature
- [x] preserve the current CLI/report flow
- [x] avoid per-request `.env` edits
- [x] prefer release/tag first, then a new feature branch
- [x] freeze actual print PDF header while allowing browser previews to evolve separately
- [x] use the new two-column header treatment for `view.html` and for `pdf_source.html` preview
- [x] keep `pdf_source.html` preview changes screen-only by separating `pdf-header-screen-only` from `pdf-header-print-only`
