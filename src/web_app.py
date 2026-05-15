# -*- coding: utf-8 -*-
"""FastAPI entry point for the Web GUI phase.

This is intentionally thin. Heavy report logic stays in ReportEngineService.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.services.report_engine_service import ReportEngineService, ReportRequestError

app = FastAPI(
    title="Energy Report Web GUI",
    version="0.1.0",
    description="Browser entry point for the energy reporting system.",
)

report_engine = ReportEngineService()


@app.get("/", include_in_schema=False)
def root_redirect() -> RedirectResponse:
    """Redirect the bare root to the report page."""
    return RedirectResponse(url="/reports")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight health payload."""
    return {
        "status": "ok",
        "service": "energy-report-web-gui",
    }


@app.get("/reports", response_class=HTMLResponse)
def render_report(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> HTMLResponse:
    """Render one report view in HTML using the shared report engine."""
    try:
        result = report_engine.render_view_report(
            period_type=period_type,
            anchor_date_text=anchor_date,
            start_date_text=start_date,
            end_date_text=end_date,
        )
        return HTMLResponse(content=result.html)
    except ReportRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to render report HTML.") from exc


@app.get("/reports/export-csv")
def export_csv_placeholder(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
) -> JSONResponse:
    """Temporary placeholder until the CSV payload contract is finalized."""
    return JSONResponse(
        status_code=501,
        content={
            "status": "not_implemented",
            "message": "CSV export route is reserved, but the CSV payload contract is not finalized yet.",
            "request": {
                "period_type": period_type,
                "anchor_date": anchor_date,
                "start_date": start_date,
                "end_date": end_date,
            },
        },
    )
