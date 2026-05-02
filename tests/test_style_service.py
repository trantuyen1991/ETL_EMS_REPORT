from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from src.services.style_service import DEFAULT_REPORT_STYLE, ReportStyleService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_build_render_context_from_live_style_config() -> None:
    service = ReportStyleService(PROJECT_ROOT / "config" / "report_style.json")

    context = service.build_render_context()

    assert "report_style" in context
    assert "report_style_css" in context
    assert "chart_theme" in context
    assert context["chart_theme_name"]
    assert context["report_style_config_path"].endswith("config/report_style.json")
    assert context["report_style_css"].startswith(":root {")
    assert "--report-components-report-title-header-title-font-size:" in context["report_style_css"]


def test_missing_style_config_falls_back_to_defaults_with_warning(tmp_path: Path) -> None:
    service = ReportStyleService(tmp_path / "missing_report_style.json")

    context = service.build_render_context()

    assert context["report_style"]
    assert context["report_style_warnings"]
    assert "Falling back to defaults" in context["report_style_warnings"][0]


def test_chart_card_background_is_the_canonical_chart_background_token(tmp_path: Path) -> None:
    style_payload = deepcopy(DEFAULT_REPORT_STYLE)
    style_payload["components"]["chartCard"]["background"] = "#f4f8fc"
    style_payload["color"]["surface"]["chartShell"] = "#fff1f2"
    style_payload["color"]["chart"]["background"] = "rgba(0,0,0,0)"
    style_payload["echartsTheme"]["backgroundColor"] = "#111827"

    config_path = tmp_path / "report_style.json"
    config_path.write_text(
        json.dumps({"reportStyle": style_payload}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    service = ReportStyleService(config_path)
    context = service.build_render_context()

    assert context["report_style"]["components"]["chartCard"]["background"] == "#f4f8fc"
    assert context["report_style"]["color"]["surface"]["chartShell"] == "#f4f8fc"
    assert context["report_style"]["color"]["chart"]["background"] == "#f4f8fc"
    assert context["chart_theme"]["backgroundColor"] == "#f4f8fc"
    assert "--report-components-chart-card-background: #f4f8fc;" in context["report_style_css"]


def test_chart_assets_no_longer_use_legacy_surface_chart_shell_token() -> None:
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    report_pdf_base_css = (PROJECT_ROOT / "src/templates/assets/report_pdf_base.css").read_text(encoding="utf-8")

    assert "surface-chart-shell" not in report_css
    assert "surface-chart-shell" not in report_pdf_base_css
