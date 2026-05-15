# Web GUI Phase 1 Checklist

## Purpose
Track the approved preparation and implementation path for the FastAPI Web GUI phase.

---

## Phase 0 — Release / branch preparation
- [ ] confirm the current report-stable baseline commit to tag
- [ ] create a release tag for the report-stable baseline
- [ ] create a dedicated feature branch for Web GUI work
- [ ] record branch/tag names in project docs if they become official

---

## Phase 1 — Shared execution-model refactor
- [ ] isolate reusable period-resolution logic from the current main flow
- [ ] define the canonical resolved-period contract (`period_type`, `anchor_date`, `start_date`, `end_date`)
- [ ] extract a shared pipeline/service entry point for report execution
- [ ] ensure the shared pipeline can be called without editing `.env`
- [ ] keep current CLI/scheduled flow working through the extracted shared path
- [ ] define where HTML render output should be returned in-memory versus written to disk
- [ ] decide whether browser refresh should reuse the full batch pipeline or a lighter report-only execution path

---

## Phase 1.1 — Browser period rules
- [ ] implement backend validation rules for `daily`
- [ ] implement backend validation rules for `weekly`
- [ ] implement backend validation rules for `monthly`
- [ ] decide whether `custom` is included in the first browser rollout or deferred
- [ ] if `custom` is included, implement and validate the inclusive 31-day limit
- [ ] define clear backend error responses for invalid requests

---

## Phase 1.2 — CSV contract
- [ ] choose one explicit meaning for `Export CSV`
- [ ] document the CSV payload contract
- [ ] define filename rules by period type
- [ ] define whether CSV is generated from raw rows, normalized rows, or report-ready tabular rows

---

## Phase 2 — FastAPI web app
- [ ] create `src/web_app.py`
- [ ] create a thin web route layer
- [ ] add `GET /`
- [ ] add `GET /reports`
- [ ] add `GET /reports/export-csv`
- [ ] add `GET /health`
- [ ] wire Jinja2 template rendering for the report page

---

## Phase 2.1 — Web UI controls
- [ ] add filter bar layout
- [ ] add dynamic input switching by period type
- [ ] add frontend guard rails for invalid custom ranges
- [ ] add `Refresh` button flow
- [ ] add `Print` button flow using `window.print()`
- [ ] add `Export CSV` button flow
- [ ] add print CSS to hide filter/action controls

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
