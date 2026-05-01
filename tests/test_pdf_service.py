from __future__ import annotations

from pathlib import Path

from src.services.pdf_service import PDFService


def test_export_prefers_cdp_when_it_succeeds(tmp_path: Path, monkeypatch) -> None:
    service = PDFService({"config": {"pdf": {}}})
    html_path = tmp_path / "report.html"
    output_pdf = tmp_path / "report.pdf"
    html_path.write_text("<html></html>", encoding="utf-8")

    calls = {"cdp": 0, "legacy": 0}

    monkeypatch.setattr(service, "_find_browser", lambda: "chromium")

    def fake_cdp(browser: str, html_path: Path, output_pdf: Path) -> None:
        calls["cdp"] += 1
        output_pdf.write_bytes(b"%PDF-cdp\n")

    def fake_legacy(browser: str, html_path: Path, output_pdf: Path) -> None:
        calls["legacy"] += 1
        output_pdf.write_bytes(b"%PDF-legacy\n")

    monkeypatch.setattr(service, "_export_via_cdp", fake_cdp)
    monkeypatch.setattr(service, "_export_via_legacy_cli", fake_legacy)

    service.export(html_path, output_pdf)

    assert calls == {"cdp": 1, "legacy": 0}
    assert output_pdf.read_bytes() == b"%PDF-cdp\n"


def test_export_falls_back_to_legacy_cli_when_cdp_fails(tmp_path: Path, monkeypatch) -> None:
    service = PDFService({"config": {"pdf": {}}})
    html_path = tmp_path / "report.html"
    output_pdf = tmp_path / "report.pdf"
    html_path.write_text("<html></html>", encoding="utf-8")

    calls = {"cdp": 0, "legacy": 0}

    monkeypatch.setattr(service, "_find_browser", lambda: "chromium")

    def fake_cdp(browser: str, html_path: Path, output_pdf: Path) -> None:
        calls["cdp"] += 1
        raise RuntimeError("cdp failed")

    def fake_legacy(browser: str, html_path: Path, output_pdf: Path) -> None:
        calls["legacy"] += 1
        output_pdf.write_bytes(b"%PDF-legacy\n")

    monkeypatch.setattr(service, "_export_via_cdp", fake_cdp)
    monkeypatch.setattr(service, "_export_via_legacy_cli", fake_legacy)

    service.export(html_path, output_pdf)

    assert calls == {"cdp": 1, "legacy": 1}
    assert output_pdf.read_bytes() == b"%PDF-legacy\n"
