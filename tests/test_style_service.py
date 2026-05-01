from __future__ import annotations

from pathlib import Path

from src.services.style_service import ReportStyleService


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
