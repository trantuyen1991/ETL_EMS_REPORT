# -*- coding: utf-8 -*-
"""FastAPI entry point for the Web GUI phase.

This keeps routes thin while the shared report logic stays in ReportEngineService.
"""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

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


@app.get("/api/v1/report/snapshot")
def get_report_snapshot(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    force_refresh: bool = Query(default=False),
) -> JSONResponse:
    """Return one machine-facing report snapshot for the selected period."""
    try:
        normalized_period_type = _normalize_phase1_period_type(period_type)
        snapshot = report_engine.build_report_snapshot(
            period_type=normalized_period_type,
            anchor_date_text=anchor_date,
            force_refresh=force_refresh,
        )
        return JSONResponse(content=snapshot)
    except ReportRequestError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "bad_request",
                "message": str(exc),
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to build report snapshot.",
            },
        )


@app.get("/api/v1/report/artifacts")
def get_report_artifacts(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
) -> JSONResponse:
    """Return one machine-facing artifact manifest for the selected period."""
    try:
        normalized_period_type = _normalize_phase1_period_type(period_type)
        manifest = report_engine.build_report_artifact_manifest(
            period_type=normalized_period_type,
            anchor_date_text=anchor_date,
        )
        return JSONResponse(content=manifest)
    except ReportRequestError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "bad_request",
                "message": str(exc),
            },
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to build report artifact manifest.",
            },
        )


@app.get("/reports", response_class=HTMLResponse)
def render_report_page(
    period_type: str | None = Query(default=None),
    template_mode: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    month: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    force_refresh: bool = Query(default=False),
    _embed: bool = Query(default=False),
) -> HTMLResponse:
    """Render either the report shell or the embedded report body."""
    if _embed:
        try:
            normalized_period_type = _normalize_phase1_period_type(period_type)
            normalized_template_mode = _normalize_template_mode(template_mode)
            result = report_engine.render_report_surface(
                template_mode=normalized_template_mode,
                period_type=normalized_period_type,
                anchor_date_text=anchor_date,
                start_date_text=start_date,
                end_date_text=end_date,
                force_refresh=force_refresh,
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

    normalized_period_type = _normalize_phase1_period_type(period_type)
    normalized_template_mode = _normalize_template_mode(template_mode)
    normalized_anchor_date = str(anchor_date or "").strip()
    normalized_month = str(month or "").strip() or _derive_month_value(normalized_anchor_date)
    normalized_start_date = str(start_date or "").strip()
    normalized_end_date = str(end_date or "").strip()

    if normalized_period_type == "monthly" and not normalized_anchor_date and normalized_month:
        normalized_anchor_date = f"{normalized_month}-01"

    shell_error_message = ""
    show_report_iframe = True

    try:
        config = report_engine.load_runtime_config()
        resolved_period = report_engine.resolve_request_period_from_config(
            config,
            period_type=normalized_period_type,
            anchor_date_text=normalized_anchor_date,
            start_date_text=normalized_start_date,
            end_date_text=normalized_end_date,
        )
        normalized_period_type = resolved_period.period_type
        if normalized_period_type == "monthly":
            normalized_anchor_date = resolved_period.anchor_date.isoformat() if resolved_period.anchor_date else ""
            normalized_month = resolved_period.start_date.strftime("%Y-%m")
        elif normalized_period_type in {"daily", "weekly"}:
            normalized_anchor_date = resolved_period.anchor_date.isoformat() if resolved_period.anchor_date else ""
            normalized_month = _derive_month_value(normalized_anchor_date)
            normalized_start_date = ""
            normalized_end_date = ""
    except ReportRequestError as exc:
        shell_error_message = str(exc)
        show_report_iframe = False

    preview_query = {
        "period_type": normalized_period_type,
        "template_mode": normalized_template_mode,
    }
    if force_refresh:
        preview_query["force_refresh"] = "1"
    if normalized_anchor_date:
        preview_query["anchor_date"] = normalized_anchor_date

    if normalized_template_mode == "pdf_source":
        report_preview_src = f"/reports/preview-pdf?{urlencode(preview_query)}"
    else:
        embed_query = dict(preview_query)
        embed_query["_embed"] = "1"
        report_preview_src = f"/reports?{urlencode(embed_query)}"

    download_query = {
        "period_type": normalized_period_type,
    }
    if normalized_anchor_date:
        download_query["anchor_date"] = normalized_anchor_date
    if normalized_month:
        download_query["month"] = normalized_month

    shell_html = web_renderer.render(
        "web/report_shell.html",
        {
            "page_title": "Energy Report Web GUI",
            "period_type": normalized_period_type,
            "template_mode": normalized_template_mode,
            "anchor_date": normalized_anchor_date,
            "month_value": normalized_month,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
            "report_iframe_src": report_preview_src,
            "download_zip_url": f"/reports/download-zip?{urlencode(download_query)}",
            "shell_error_message": shell_error_message,
            "show_report_iframe": show_report_iframe,
        },
    )
    return HTMLResponse(content=shell_html)


@app.get("/reports/preview-pdf", response_model=None)
def preview_report_pdf(
    period_type: str | None = Query(default=None),
    template_mode: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    month: str | None = Query(default=None),
    force_refresh: bool = Query(default=False),
):
    """Return one real rendered PDF for in-browser preview."""
    try:
        normalized_period_type = _normalize_phase1_period_type(period_type)
        _normalize_template_mode(template_mode)
        normalized_anchor_date = str(anchor_date or "").strip()
        normalized_month = str(month or "").strip()
        if normalized_period_type == "monthly" and not normalized_anchor_date and normalized_month:
            normalized_anchor_date = f"{normalized_month}-01"

        pdf_path = report_engine.build_report_pdf_preview(
            period_type=normalized_period_type,
            anchor_date_text=normalized_anchor_date,
            force_refresh=force_refresh,
        )
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{pdf_path.name}"',
            },
        )
    except ReportRequestError as exc:
        return HTMLResponse(
            content=_build_report_error_html(str(exc)),
            status_code=400,
        )
    except FileNotFoundError as exc:
        return HTMLResponse(
            content=_build_report_error_html(str(exc)),
            status_code=404,
        )
    except Exception:
        return HTMLResponse(
            content=_build_report_error_html("Failed to render preview PDF."),
            status_code=500,
        )


@app.get("/reports/download-zip", response_model=None)
def download_report_zip(
    period_type: str | None = Query(default=None),
    anchor_date: str | None = Query(default=None),
    month: str | None = Query(default=None),
):
    """Download one backend-built month package as a ZIP file."""
    try:
        normalized_period_type = _normalize_phase1_period_type(period_type)
        normalized_anchor_date = str(anchor_date or "").strip()
        normalized_month = str(month or "").strip()
        if normalized_period_type == "monthly" and not normalized_anchor_date and normalized_month:
            normalized_anchor_date = f"{normalized_month}-01"

        zip_path = report_engine.build_report_package_zip(
            period_type=normalized_period_type,
            anchor_date_text=normalized_anchor_date,
        )
        return FileResponse(
            path=zip_path,
            filename=zip_path.name,
            media_type="application/zip",
        )
    except ReportRequestError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "status": "bad_request",
                "message": str(exc),
            },
        )
    except FileNotFoundError as exc:
        return JSONResponse(
            status_code=404,
            content={
                "status": "not_found",
                "message": str(exc),
            },
        )


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


def _normalize_phase1_period_type(period_type: str | None) -> str:
    """Allow only the phase-1 browser periods."""
    normalized = str(period_type or "monthly").strip().lower() or "monthly"
    if normalized not in {"daily", "weekly", "monthly"}:
        raise ReportRequestError(
            "phase-1 browser period_type must be one of: daily, weekly, monthly. custom is deferred."
        )
    return normalized


def _normalize_template_mode(template_mode: str | None) -> str:
    """Normalize the browser template selector."""
    normalized = str(template_mode or "view").strip().lower() or "view"
    if normalized not in {"view", "pdf_source"}:
        raise ReportRequestError("template_mode must be one of: view, pdf_source.")
    return normalized


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
