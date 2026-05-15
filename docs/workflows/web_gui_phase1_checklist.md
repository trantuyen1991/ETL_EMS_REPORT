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
- [ ] decide whether `custom` is included in the first browser rollout or deferred
- [x] if `custom` is included, implement and validate the inclusive 31-day limit
- [x] define clear backend error responses for invalid requests

Current prep behavior:
- invalid browser params return backend validation errors through the web layer
- `custom` validation is coded but product rollout is still a phase decision

---

## Phase 1.2 — CSV contract
- [ ] choose one explicit meaning for `Export CSV`
- [ ] document the CSV payload contract
- [ ] define filename rules by period type
- [ ] define whether CSV is generated from raw rows, normalized rows, or report-ready tabular rows

---

## Phase 2 — FastAPI web app
- [x] create `src/web_app.py`
- [x] create a thin web route layer
- [x] add `GET /`
- [x] add `GET /reports`
- [x] add `GET /reports/export-csv`
- [x] add `GET /health`
- [x] wire Jinja2 template rendering for the report page

Current prep note:
- `/reports/export-csv` is intentionally a 501 placeholder until the CSV contract is finalized.

---

## Phase 2.1 — Web UI controls
- [x] add filter bar layout
- [x] add dynamic input switching by period type
- [x] add frontend guard rails for invalid custom ranges
- [x] add `Refresh` button flow
- [x] add `Print` button flow using `window.print()`
- [x] add `Export CSV` button flow
- [x] add print CSS to hide filter/action controls

Current implementation note:
- `/reports` now serves a shell page with a filter toolbar and embedded report iframe.
- `Export CSV` currently points to the reserved placeholder endpoint until the CSV contract is finalized.

---

## Phase 2.2 — Verification
- [ ] `daily` renders one selected day correctly
- [ ] `weekly` resolves Monday -> Sunday correctly
- [ ] `monthly` resolves first day -> last day correctly
- [ ] `custom` works correctly if included in this phase
- [ ] invalid custom ranges fail safely and clearly
- [ ] browser print hides the filter controls
- [ ] CSV download matches the selected timeline
- [ ] CLI/report flow remains intact after the web layer is added

---

## Phase 3 — Post-phase follow-up
- [ ] review request latency and ETL cost
- [ ] decide where caching belongs for browser-driven refresh
- [ ] define future JSON/API shape for ThingsBoard integration
- [ ] decide whether realtime telemetry should stay separate from report analytics

---

## Current decisions already approved
- [x] use FastAPI + Jinja2 rather than React/Vue for the first Web GUI phase
- [x] keep ThingsBoard out of the current implementation scope
- [x] treat the new phase as an execution-model refactor, not only a UI feature
- [x] preserve the current CLI/report flow
- [x] avoid per-request `.env` edits
- [x] prefer release/tag first, then a new feature branch
