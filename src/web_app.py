# -*- coding: utf-8 -*-
"""FastAPI entry point for the Web GUI phase.

This keeps routes thin while the shared report logic stays in ReportEngineService.
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from src.services.report_engine_service import ReportEngineService, ReportRequestError
from src.services.template_service import TemplateRenderingService

app = FastAPI(
    title="Energy Report Web GUI",
    version="0.1.0",
    description="Browser entry point for the energy reporting system.",
)

report_engine = ReportEngineService()
web_renderer = TemplateRenderingService("src/templates")


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
def render_report_page(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    month: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    _embed: bool = Query(default=False),
) -> HTMLResponse:
    """Render either the report shell or the embedded report body."""
    if _embed:
        try:
            result = report_engine.render_view_report(
                period_type=period_type,
                anchor_date_text=anchor_date,
                start_date_text=start_date,
                end_date_text=end_date,
            )
            return HTMLResponse(content=result.html)
        except ReportRequestError as exc:
            return HTMLResponse(
                content=_build_report_error_html(str(exc)),
                status_code=400,
            )
        except Exception:
            return HTMLResponse(
                content=_build_report_error_html("Failed to render report HTML."),
                status_code=500,
            )

    normalized_period_type = str(period_type or "monthly").strip().lower() or "monthly"
    normalized_anchor_date = str(anchor_date or "").strip()
    normalized_month = str(month or "").strip() or _derive_month_value(normalized_anchor_date)
    normalized_start_date = str(start_date or "").strip()
    normalized_end_date = str(end_date or "").strip()

    iframe_query = {
        "_embed": "1",
        "period_type": normalized_period_type,
    }
    if normalized_anchor_date:
        iframe_query["anchor_date"] = normalized_anchor_date
    if normalized_start_date:
        iframe_query["start_date"] = normalized_start_date
    if normalized_end_date:
        iframe_query["end_date"] = normalized_end_date

    csv_query = {
        "period_type": normalized_period_type,
    }
    if normalized_anchor_date:
        csv_query["anchor_date"] = normalized_anchor_date
    if normalized_start_date:
        csv_query["start_date"] = normalized_start_date
    if normalized_end_date:
        csv_query["end_date"] = normalized_end_date

    shell_html = web_renderer.render(
        "web/report_shell.html",
        {
            "page_title": "Energy Report Web GUI",
            "period_type": normalized_period_type,
            "anchor_date": normalized_anchor_date,
            "month_value": normalized_month,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
            "report_iframe_src": f"/reports?{urlencode(iframe_query)}",
            "csv_export_url": f"/reports/export-csv?{urlencode(csv_query)}",
        },
    )
    return HTMLResponse(content=shell_html)


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


def _derive_month_value(anchor_date: str) -> str:
    """Derive YYYY-MM month value from one YYYY-MM-DD date string."""
    text = str(anchor_date or "").strip()
    if len(text) >= 7:
        return text[:7]
    return ""


def _build_report_error_html(message: str) -> str:
    """Return a lightweight HTML fragment for iframe-visible errors."""
    safe_message = str(message or "Unknown report error.").strip() or "Unknown report error."
    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Report Error</title>
  <style>
    body {{
      margin: 0;
      padding: 24px;
      font-family: Inter, Arial, sans-serif;
      background: #f8fafc;
      color: #0f172a;
    }}
    .report-error-card {{
      max-width: 720px;
      margin: 24px auto;
      background: #ffffff;
      border: 1px solid #fecaca;
      border-radius: 16px;
      padding: 20px 22px;
      box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
    }}
    .report-error-card h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      color: #b91c1c;
    }}
    .report-error-card p {{
      margin: 0;
      line-height: 1.6;
      color: #334155;
    }}
  </style>
</head>
<body>
  <div class=\"report-error-card\">
    <h1>Report request error</h1>
    <p>{safe_message}</p>
  </div>
</body>
</html>
""".strip()
