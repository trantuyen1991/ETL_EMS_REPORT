# Web GUI API Direction

## Purpose

Define the approved JSON/API direction that can later support ThingsBoard or other machine-facing consumers without coupling them to HTML templates.

This document is intentionally about **direction and contract shape**, with the first endpoint now partially implemented.

Current implementation status:
- `GET /api/v1/report/snapshot` is now available in the local Web GUI app
- it currently reuses the shared resolved-period contract for `daily`, `weekly`, and `monthly`
- it exposes normalized `meta`, `period`, `availability`, `summary`, `sections`, and `artifacts` blocks
- chart payloads are exposed through a controlled renderer-agnostic schema instead of raw ECharts `option` blobs
- `GET /api/v1/report/artifacts` remains a future companion endpoint

---

## Core Decisions

### 1. Keep realtime telemetry separate from report analytics

Approved direction:
- **report analytics** stays as a resolved-period snapshot API
- **realtime telemetry** stays as a separate future API family

Reason:
- report analytics uses finalized period logic, coverage rules, and business-ready totals
- realtime telemetry has different freshness, storage, and failure semantics
- mixing both in one payload would blur truth sources and complicate ThingsBoard widgets

Practical rule:
- do not mix live point values with finalized KPI/report totals in the same endpoint response
- if a future dashboard needs both, it should join them at the consumer layer

---

### 2. Prefer one canonical report snapshot endpoint first

Recommended first machine-facing API:
- `GET /api/v1/report/snapshot`

Reason:
- ThingsBoard and similar consumers usually want one stable JSON payload per selected period
- one canonical snapshot is easier to version, cache, and validate than many small ad-hoc endpoints
- the existing backend already builds one shared report context per resolved period

Optional future companion endpoints may be added later, but they should derive from the same shared snapshot contract.

---

### 3. Keep the period contract identical to the current Web GUI/service layer

The API should reuse the normalized request contract already approved in the Web GUI:
- `period_type`
- `anchor_date`
- resolved `start_date`
- resolved `end_date`

Allowed public period types for the first API direction:
- `daily`
- `weekly`
- `monthly`

`custom` may remain backend-capable internally, but should not become a public machine-facing contract until its product rules are explicitly approved.

---

### 4. Return controlled chart schemas, not raw ECharts option blobs

Approved rule:
- JSON responses should expose chart data in a controlled schema
- do **not** expose unrestricted raw ECharts option blobs as the API contract

Reason:
- keeps the API stable across renderer changes
- avoids leaking view-specific presentation details into the backend contract
- aligns with the existing project rule that chart config should stay symbolic/controlled

---

### 5. Keep artifact references separate from the analytics payload body

The snapshot payload may include artifact metadata, but it should not embed large HTML/PDF bodies.

Recommended artifact references:
- preview URL
- PDF preview URL
- ZIP download URL
- optional generated-at timestamps

---

## Recommended Phase-1 Machine-Facing Endpoints

### A. Report snapshot

`GET /api/v1/report/snapshot?period_type=monthly&anchor_date=2026-03-31`

Purpose:
- return one normalized analytics snapshot for the selected resolved period
- suitable for ThingsBoard, internal dashboards, or future SPA consumers

### B. Artifact manifest

`GET /api/v1/report/artifacts?period_type=monthly&anchor_date=2026-03-31`

Purpose:
- return URLs and freshness metadata for backend-built artifacts
- keeps artifact delivery separate from the main analytics JSON when a client only needs files

Current status:
- not implemented yet
- the current snapshot endpoint already includes basic artifact URLs under `artifacts`

### C. Realtime telemetry family, future and separate

Examples for later, not current scope:
- `GET /api/v1/telemetry/latest?...`
- `GET /api/v1/telemetry/series?...`

Rule:
- telemetry endpoints must remain separate from report-snapshot endpoints

---

## Recommended Snapshot Shape

```json
{
  "meta": {
    "api_version": "v1",
    "generated_at": "2026-05-23T15:30:00Z",
    "source": "report_engine_service",
    "cache": {
      "hit": true,
      "fingerprint": "style:abc123|config:def456"
    }
  },
  "period": {
    "period_type": "monthly",
    "anchor_date": "2026-03-31",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31",
    "label": "March 2026"
  },
  "availability": {
    "has_report": true,
    "coverage_status": "partial",
    "warnings": []
  },
  "summary": {
    "electricity_total": {
      "value": 12345.67,
      "unit": "kWh",
      "display": "12,345.67"
    },
    "utility_total": {
      "value": 987.65,
      "unit": "m3",
      "display": "987.65"
    },
    "kpi_status": {
      "coverage": "month",
      "display": "Month coverage"
    }
  },
  "sections": {
    "electricity": {
      "cards": [],
      "tables": [],
      "charts": []
    },
    "utility": {
      "cards": [],
      "tables": [],
      "charts": []
    },
    "kpi": {
      "cards": [],
      "tables": [],
      "charts": []
    }
  },
  "artifacts": {
    "interactive_url": "/reports?_embed=1&period_type=monthly&anchor_date=2026-03-31&template_mode=view",
    "pdf_preview_url": "/reports/preview-pdf?period_type=monthly&anchor_date=2026-03-31",
    "zip_download_url": "/reports/download-zip?period_type=monthly&anchor_date=2026-03-31"
  }
}
```

---

## Recommended Controlled Chart Schema

Each chart object should use a renderer-agnostic schema such as:

```json
{
  "chart_key": "electricity_period_trend",
  "chart_type": "line",
  "title": "Electricity trend",
  "subtitle": "Current period versus previous period",
  "unit": "kWh",
  "x_axis": {
    "label": "Date",
    "values": ["2026-03-01", "2026-03-02"]
  },
  "series": [
    {
      "key": "current",
      "label": "Current",
      "style": "line",
      "axis": "primary",
      "values": [100, 120]
    },
    {
      "key": "previous",
      "label": "Previous",
      "style": "line",
      "axis": "primary",
      "values": [95, 110]
    }
  ],
  "legend": ["Current", "Previous"],
  "notes": []
}
```

Do not expose:
- raw ECharts formatter functions
- raw renderer callbacks
- browser-only tooltip/hover logic as the backend contract

---

## ThingsBoard Mapping Guidance

Recommended mapping for future ThingsBoard integration:
- one datasource call should fetch the report snapshot for the selected resolved period
- cards/widgets should bind to `summary` and `sections.*.cards`
- charts should bind to `sections.*.charts`
- tables should bind to `sections.*.tables`
- artifact actions can bind to the `artifacts` object

Important:
- ThingsBoard should consume JSON, not scrape `view.html`
- HTML remains for humans; JSON becomes the machine-facing contract

---

## What Stays Out of Scope For This Direction

Still out of scope here:
- implementing a public auth model
- building websocket/live-stream telemetry
- exposing raw SQL/resultset payloads as the main contract
- exposing CSV as a substitute for the report snapshot API
- merging live telemetry and finalized report analytics into one mixed endpoint

---

## Recommended Next Implementation Slice

When this direction becomes active implementation work, the safest next order is:

1. improve and stabilize the snapshot DTO field contract as machine consumers become concrete
2. expose `GET /api/v1/report/artifacts`
3. validate and document consumer expectations on `daily`, `weekly`, and `monthly`
4. only after that, design any separate telemetry endpoints
