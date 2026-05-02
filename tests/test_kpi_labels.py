from __future__ import annotations

from pathlib import Path

from src.services.report_builder_service import ReportBuilderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_minimal_kpi_object() -> dict:
    return {
        "current": {
            "summary": {
                "plant": {"total_energy": 100.0, "total_prod": 10.0, "total_kpi": 10.0},
                "areas": {
                    "ico": {"energy": 30.0, "prod": 3.0, "kpi": 10.0},
                    "diode": {"energy": 40.0, "prod": 4.0, "kpi": 10.0},
                    "sakari": {"energy": 30.0, "prod": 3.0, "kpi": 10.0},
                },
            },
            "daily_rows": [],
            "coverage": {},
        },
        "previous": {
            "summary": {
                "plant": {"total_energy": 90.0, "total_prod": 9.0, "total_kpi": 10.0},
                "areas": {
                    "ico": {"energy": 27.0, "prod": 3.0, "kpi": 9.0},
                    "diode": {"energy": 36.0, "prod": 4.0, "kpi": 9.0},
                    "sakari": {"energy": 27.0, "prod": 3.0, "kpi": 9.0},
                },
            },
            "daily_rows": [],
        },
        "comparison": {
            "plant": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
            "areas": {
                "ico": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
                "diode": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
                "sakari": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
            },
        },
    }


def test_kpi_section_empty_summary_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    section = service._build_v3_kpi_section(None)

    assert section["summary_matrix"]["title"] == "KPI Summary Matrix"


def test_kpi_summary_matrix_empty_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    matrix = service._build_v3_kpi_summary_matrix(None)

    assert matrix["title"] == "KPI Summary Matrix"


def test_kpi_summary_matrix_populated_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    matrix = service._build_v3_kpi_summary_matrix(_build_minimal_kpi_object(), period_type="weekly")

    assert matrix["title"] == "KPI Summary Matrix"


def _build_zero_kpi_object() -> dict:
    return {
        "current": {
            "summary": {
                "plant": {"total_energy": 0.0, "total_prod": 0.0, "total_kpi": 0.0},
                "areas": {
                    "ico": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "diode": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "sakari": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                },
            },
            "daily_rows": [],
            "coverage": {},
        },
        "previous": {
            "summary": {
                "plant": {"total_energy": 0.0, "total_prod": 0.0, "total_kpi": 0.0},
                "areas": {
                    "ico": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "diode": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "sakari": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                },
            },
            "daily_rows": [],
        },
        "comparison": {
            "plant": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
            "areas": {
                "ico": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
                "diode": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
                "sakari": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
            },
        },
    }


def test_kpi_waterfall_option_uses_compact_daily_axis_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_kpi_waterfall_option(
        previous_kpi=10.0,
        energy_impact=0.0,
        production_impact=0.0,
        current_kpi=10.0,
    )

    assert option["xAxis"]["data"] == ["Yesterday", "Energy", "Prod.", "Today"]


def test_kpi_variance_option_hides_zero_value_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_kpi_variance_option(
        [
            {
                "name": "ICO",
                "value": 0.0,
                "current": 10.0,
                "previous": 10.0,
                "unit": "%",
            }
        ]
    )

    point = option["series"][0]["data"][0]

    assert point["label"]["show"] is False
    assert option["grid"]["left"] == 84
    assert option["grid"]["right"] == 18


def test_daily_kpi_charts_use_empty_state_messages_for_zero_only_data() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    dashboard = service._build_v3_kpi_daily_dashboard(
        _build_zero_kpi_object(),
        current_label="Today",
        previous_label="Yesterday",
    )

    assert dashboard["charts"]["compare_bar"]["empty_message"] == "No KPI values recorded for this day."
    assert dashboard["charts"]["waterfall"]["empty_message"] == "No KPI movement recorded for this day."
    assert dashboard["charts"]["variance"]["empty_message"] == "No KPI deviation detected for this day."


def test_daily_kpi_view_template_renders_empty_state_blocks() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/kpi.html").read_text(encoding="utf-8")

    assert "sections.kpi.charts.daily_dashboard.charts.compare_bar.empty_message" in view_template
    assert "sections.kpi.charts.daily_dashboard.charts.waterfall.empty_message" in view_template
    assert "sections.kpi.charts.daily_dashboard.charts.variance.empty_message" in view_template
    assert "kpi-daily-empty-state" in view_template
