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

## 8.3 `GET /reports/preview-pdf`
- resolve period from query params
- validate request
- render or reuse the real backend-built PDF artifact for the selected timeline
- return inline `application/pdf` for browser preview

## 8.4 `GET /reports/download-zip`
- resolve period from query params
- validate request
- resolve the backend-built report package to download
- return a ZIP file for the selected report folder

## 8.5 `GET /health`
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

Initial measured findings on the current host:
- shell route generation is effectively config-only and very fast, about `0.005s` in local curl timing.
- embedded report routes are currently full shared-service renders with no request cache layer.
- representative local timings observed during the first phase-3 review were:
  - `daily view`: about `1.13s`
  - `daily pdf_source`: about `1.12s`
  - `weekly view`: about `1.26s`
  - `monthly view`: about `1.48s`
  - `monthly pdf_source`: about `1.51s`
- warm ZIP download for an already-built month package was about `0.21s`.
- when a requested month package does not exist yet, ZIP download can trigger a full on-demand render first, so cold-path cost is much higher than the warm ZIP timing.

This suggests the first useful cache discussion should focus on embedded report HTML and on-demand ZIP generation, not on the shell page itself.

Decided cache direction for the next implementation slice:
- keep caching in the shared backend service layer, not in the FastAPI route layer.
- do not spend effort caching the shell page first, because its measured cost is already negligible.
- first cache target: reusable report context for one resolved period request.
- second cache target: rendered HTML output per template surface (`view` or `pdf_source`) for that same resolved period.
- third cache target: ZIP artifact reuse based on month-folder freshness.

Recommended cache-key shape:
- `period_type`
- resolved `anchor_date`
- resolved `start_date`
- resolved `end_date`
- `template_mode` for HTML surface cache only
- a cache-version fingerprint derived from deploy/runtime-sensitive inputs such as style/config revision markers

Implemented cache/result state at the current checkpoint:
- `ReportEngineService` now owns the in-memory preview cache rather than FastAPI routes.
- HTML browser preview supports explicit cache bypass through `force_refresh=1`.
- template-only switching stays on the warm-cache path for the interactive HTML surface.
- real PDF preview now uses a dedicated `/reports/preview-pdf` route and renders or reuses the final PDF artifact instead of relying on simulated browser pagination of `pdf_source.html`.
- ZIP reuse now follows month-folder freshness rather than rebuilding blindly.
- validated local timings after implementation were about:
  - forced/cold daily preview: `1.11s`
  - warm daily preview: `0.008s` to `0.009s`

Recommended initial invalidation behavior:
- explicit browser `Refresh` should bypass preview cache and force rebuild for the selected request.
- template-only switching should stay on the warm cache path whenever the normalized period key is unchanged.
- process restart may safely clear in-memory cache.
- successful rerender should replace the current HTML/ZIP artifact entry for the same normalized key.

Recommended initial TTLs:
- in-memory preview cache: `5 minutes`
- ZIP artifact cache: no short TTL requirement, prefer freshness based on existing month-folder contents and ZIP mtime

This direction preserves the current request-driven web behavior while avoiding premature cross-process infrastructure such as Redis in the current phase.

---

## 14. Current preview/UI implementation state

Current browser-shell behavior:
- `/reports` now uses a compact, centered filter shell with a collapsible `Filters & Actions` section.
- helper copy moved into hover hints/tooltips.
- outer page scroll is hidden while iframe/report scroll remains active.
- action buttons stay on one row.
- template-only switching auto reloads preview immediately, while period/date changes still depend on `Refresh`.
- `Interactive (view.html)` still renders as embedded HTML.
- `Print Preview` now opens the real rendered PDF inside the WebUI through `/reports/preview-pdf`.

Current browser report-review state:
- periodic `view.html` Electricity Daily Detail remains split into 3 area tables (`MPC`, `ICO`, `SAKARI`), while split chunks inside each area are merged into one scrollable table per area.
- periodic detail keeps sticky `Index`, sticky `Date`, sticky header, bounded internal scrolling, and area-specific browser tones without affecting PDF output.
- periodic detail value bars and cell-background intensity are now synchronized to one rule: both read from the same global-max ratio of the current visible area table and period window.
- periodic detail now uses one shared max of the whole visible area table for the selected week/month, not per-row and not per-meter normalization.
- zero-value cells in periodic detail no longer render a misleading background fill track.
- Utility `view.html` display labels now use `MPC` instead of `DIODE` for business-facing text such as `MPC Chiller`, `MPC Air`, and `MPC Chilled Water`.
- raw meter/source IDs such as `DIODEMSB1`, `DIODEAC2`, and `DIODECH1` intentionally remain unchanged.

Current header-preview design direction:
- HTML `view.html` now uses an HTML-native two-column header preview layout.
- left column is a fixed-width brand/art area.
- right column is flexible and owns title/subtitle/generated-time text.
- current dedicated preview assets include:
  - `logo_company_White01.svg`
  - `background_image_left.svg`
  - `background_image_right.svg`
- preview header shell is now white to avoid a visible seam between the left and right columns.
- both `view.html` and the final PDF header now anchor the left artwork to the left edge of the left column.

Current PDF-family preview rule:
- `pdf_source.html` remains the backend PDF-oriented HTML source used to build the final PDF artifact.
- WebUI `Print Preview` no longer depends on simulated screen pagination of `pdf_source.html`.
- the browser now previews the real PDF artifact so page flow matches export behavior for sections such as Top 10, Utility, Sensor Cluster, and KPI.

Traceability note for the recent preview checkpoint chain:
- `067199a` `feat(web): split html header into two background columns`
- `65f828a` `fix(web): remove duplicate html header logo overlay`
- `1dc0a20` `feat(web): preview real pdf in print surface`
- `166d768` `style(web): fix periodic detail area accents`
- `2857d11` `style(web): clean periodic detail zero fills`
- `4c6a5a3` `style(web): scale periodic detail by table max`
- `f859193` `style(web): sync periodic cell heat with global fill`
- `4d06c8d` `fix(web): rename utility diode labels to mpc`

---

## 15. Success Criteria for the architecture phase

The architecture refactor is successful only when:
- current CLI flow still works
- web requests do not depend on `.env` edits
- route handlers stay thin
- period resolution is reusable and testable
- report rendering is driven by shared services rather than duplicated web logic
