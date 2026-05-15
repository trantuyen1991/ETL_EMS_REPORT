# Web GUI Architecture Plan

## 1. Purpose

This document defines the approved architecture direction for the next project phase: a browser-based report system built on top of the current ETL/report stack.

The goal is to add a practical Web GUI without breaking the stable CLI and scheduled export flow that already exists.

---

## 2. Product Goal

Target user experience for phase 1:

1. Open a browser URL on the Ubuntu host.
2. Select a report period.
3. Choose which rendered surface to inspect.
4. Click `Refresh`.
5. Backend resolves the selected period.
6. Browser shows the updated report.
7. User can download the backend-built report package as a ZIP file.

Phase-1 browser scope no longer includes direct CSV export or `custom` period release.
---

## 3. Scope Boundaries

## 3.1 In Scope
- FastAPI web app
- Jinja2-rendered report page
- period filter bar for `daily`, `weekly`, and `monthly`
- template switch between the `view` surface and the `pdf_source` surface
- backend validation of browser inputs
- backend-built ZIP download for the selected report package
- preservation of current CLI/report flow

## 3.2 Out of Scope for the first implementation phase
- ThingsBoard widgets
- a frontend SPA framework such as React or Vue
- editing `.env` per request
- moving heavy ETL logic into route handlers
- broad report-layout redesign unrelated to web delivery
- public release of `custom` period in the phase-1 browser toolbar
- CSV export in the phase-1 browser toolbar

---

## 4. Git Strategy

Approved strategy:

1. tag the current report-stable baseline
2. create a dedicated feature branch for Web GUI work
3. keep the report-stable baseline easy to restore and compare against

Recommended branch shape:
- baseline tag from the current stable report branch
- feature branch for Web GUI and shared execution-model refactor

Reason:
- the next phase is an architecture change, not just a UI addition
- current report rendering is already stable enough to deserve a named release point

---

## 5. Architecture Direction

## 5.1 Current execution model
The current system is primarily:
- config-driven
- batch/scheduled oriented
- file-output oriented

## 5.2 Next execution model
The Web GUI phase requires a second execution path that is:
- request-driven
- parameter-driven
- able to resolve periods without editing runtime config files
- reusable by both browser routes and the existing CLI flow

This means the next phase is an execution-model refactor, not just template wrapping.

---

## 6. Service Extraction Strategy

Preferred extraction order:

1. `resolve_period(...)`
2. `run_report_pipeline(...)`
3. `render_report_html(...)`
4. `export_report_csv(...)`
5. web route integration

Rules:
- each extraction step should preserve current CLI behavior
- each step should be verified before the next step begins
- shared business/report logic must remain outside route handlers

---

## 7. Web Layer Responsibilities

The web layer should stay thin.

It should only:
- accept request params
- validate input
- resolve period input into explicit runtime parameters
- call the shared report-engine service
- render the page or return a file response

The web layer should not:
- perform heavy ETL orchestration inline
- edit `.env`
- duplicate report business logic already owned by backend services

---

## 8. Planned Route Surface

## 8.1 `GET /`
- redirect to `/reports`

## 8.2 `GET /reports`
- resolve period from query params
- validate request
- allow template-mode selection (`view` or `pdf_source`)
- run shared report pipeline
- render the report page

## 8.3 `GET /reports/download-zip`
- resolve period from query params
- validate request
- resolve the backend-built report package to download
- return a ZIP file for the selected report folder

## 8.4 `GET /health`
- return a simple health JSON payload

---

## 9. Period Input Rules

## 9.1 Daily
- one date input
- resolved to one day

## 9.2 Weekly
- one date input
- backend resolves Monday -> Sunday for the selected date

## 9.3 Monthly
- one month input
- backend resolves first day -> last day of the month

## 9.4 Custom
- `start_date` + `end_date`
- inclusive range
- maximum 31 days
- backend support may remain for future use
- phase-1 browser release defers `custom` from the active toolbar

---

## 10. Validation Rules

Validation must exist in both frontend and backend.

Backend is authoritative.

Mandatory backend checks:
- allowed `period_type` only
- valid date format
- `end_date >= start_date`
- custom range `<= 31` days inclusive
- do not run ETL when validation fails
- return clear user-facing errors

---

## 11. Download / print package direction

Phase-1 action rule:
- the toolbar should favor downloading a backend-built ZIP package over invoking direct browser print
- the ZIP may contain the rendered report folder for the selected timeline, for example one month folder such as `2026_03`
- naming should make it clear that the action downloads a package rather than invoking native print

Important rule:
- if the UI label says `Print`, but the behavior actually downloads a ZIP package, the action will be misleading
- prefer a label such as `Download Report ZIP` or `Download Print Package`

---

## 12. CSV Export Contract Warning

`Export CSV` remains unresolved.

The project still needs to choose one explicit meaning for the exported payload:
- raw DB rows
- normalized ETL rows
- report-ready tabular rows

Until that choice is approved, CSV should stay out of the phase-1 browser toolbar and must not be presented as a finished user action.

---

## 13. Suggested Phase Split

## Phase 0
- tag stable report baseline
- create Web GUI feature branch
- freeze current release checkpoint docs

## Phase 1
- extract shared execution services
- preserve CLI behavior
- validate daily/weekly/monthly path end-to-end

## Phase 2
- add FastAPI app
- add `/reports`
- add filter bar
- add template-mode switch
- add backend ZIP download action
- keep CSV outside the active toolbar until its contract is approved

## Phase 3
- performance tuning
- cache strategy
- improved error handling
- prepare JSON/API direction for future ThingsBoard integration

---

## 14. Success Criteria for the architecture phase

The architecture refactor is successful only when:
- current CLI flow still works
- web requests do not depend on `.env` edits
- route handlers stay thin
- period resolution is reusable and testable
- report rendering is driven by shared services rather than duplicated web logic
