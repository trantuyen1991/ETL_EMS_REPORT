from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from src import web_app


def test_help_pdf_preview_and_download_use_release_artifact(tmp_path: Path, monkeypatch) -> None:
    help_pdf = tmp_path / "report_reader_guide_latest.pdf"
    help_pdf.write_bytes(b"%PDF-help\n")

    monkeypatch.setattr(web_app, "HELP_PDF_PATH", help_pdf)

    preview_response = web_app.preview_help_pdf()
    download_response = web_app.download_help_pdf()

    assert isinstance(preview_response, FileResponse)
    assert preview_response.path == help_pdf
    assert preview_response.media_type == "application/pdf"
    assert dict(preview_response.headers)["content-disposition"] == (
        'inline; filename="energy_report_reader_guide.pdf"'
    )
    assert isinstance(download_response, FileResponse)
    assert download_response.path == help_pdf
    assert download_response.filename == "energy_report_reader_guide.pdf"


def test_help_pdf_routes_report_missing_artifact(tmp_path: Path, monkeypatch) -> None:
    missing_pdf = tmp_path / "missing_help.pdf"
    monkeypatch.setattr(web_app, "HELP_PDF_PATH", missing_pdf)

    preview_response = web_app.preview_help_pdf()
    download_response = web_app.download_help_pdf()

    assert isinstance(preview_response, HTMLResponse)
    assert preview_response.status_code == 404
    assert b"Help PDF is not available" in preview_response.body
    assert isinstance(download_response, JSONResponse)
    assert download_response.status_code == 404
    assert b"Help PDF is not available" in download_response.body


def test_report_shell_exposes_help_pdf_action() -> None:
    shell_template = Path("src/templates/web/report_shell.html").read_text(encoding="utf-8")

    assert 'id="view-help-link"' in shell_template
    assert 'href="/help"' in shell_template
    assert "Help PDF" in shell_template


def test_help_shell_embeds_pdf_preview_and_download_action() -> None:
    help_template = Path("src/templates/web/help_shell.html").read_text(encoding="utf-8")

    assert 'src="{{ help_pdf_url }}"' in help_template
    assert 'href="{{ help_download_url }}"' in help_template
    assert "Download PDF" in help_template
