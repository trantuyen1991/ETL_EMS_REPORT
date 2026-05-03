from __future__ import annotations

from datetime import date
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService
from src.services.utility_service import UtilityService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_daily_sensor_monitoring_context_builds_health_snapshot_and_top_issues() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={},
        report_start=date(2025, 6, 25),
        report_end=date(2025, 6, 25),
    )

    assert context["health_snapshot"]
    assert [item["key"] for item in context["health_snapshot"]] == ["active", "missing", "critical", "warning"]
    assert context["health_snapshot"][0]["value_display"].endswith(f"/{context['sensor_count']}")
    assert context["missing_sensor_count"] == context["sensor_count"] - context["active_sensor_count"]
    assert context["top_issues_preview"]
    assert len(context["top_issues_preview"]) <= 5
    assert context["top_issues_preview"][0]["flag_summary"] == "Missing data"

    group_keys = [group["key"] for group in context["groups"]]
    assert group_keys[-2:] == ["domestic_water", "sakari_water"]

    sakari_group = next(group for group in context["groups"] if group["key"] == "sakari_water")
    domestic_group = next(group for group in context["groups"] if group["key"] == "domestic_water")

    assert len(sakari_group["sensors"]) == 1
    assert sakari_group["sensors"][0]["key"] == "sak_waterflow"
    assert len(domestic_group["sensors"]) == 1
    assert domestic_group["sensors"][0]["key"] == "dom_waterflow"


def test_daily_pdf_utility_template_contains_sensor_health_and_top_issues_blocks() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    assert "Sensor health snapshot" in pdf_template
    assert "Top issues today" in pdf_template
    assert "sensor_monitoring_view.health_snapshot" in pdf_template
    assert "sensor_monitoring_view.top_issues_preview" in pdf_template


def test_daily_pdf_utility_template_splits_sensor_groups_for_page_5_preview() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    assert "sensor_group_preview = sensor_monitoring_view.groups[:3]" in pdf_template
    assert "sensor_group_remaining = sensor_monitoring_view.groups[3:]" in pdf_template
    assert "utility-sensor-group-grid-preview" in pdf_template
    assert "utility-sensor-group-grid-remaining" in pdf_template


def test_period_sensor_trend_builder_marks_lone_tail_chart_for_full_width_pdf_layout() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    charts = service._build_v3_period_sensor_trend_charts(
        {
            "trend_mode": "period",
            "daily_rows": [
                {
                    "date": date(2025, 6, 23),
                    "metrics": {
                        "water_1": {"avg": 10.0},
                        "water_2": {"avg": 20.0},
                        "water_3": {"avg": 30.0},
                        "water_4": {"avg": 40.0},
                        "steam_1": {"avg": 50.0},
                    },
                },
                {
                    "date": date(2025, 6, 24),
                    "metrics": {
                        "water_1": {"avg": 11.0},
                        "water_2": {"avg": 21.0},
                        "water_3": {"avg": 31.0},
                        "water_4": {"avg": 41.0},
                        "steam_1": {"avg": 51.0},
                    },
                },
            ],
            "metric_columns": [
                {"key": "water_1", "display_name": "Water 1", "unit": "m³/h"},
                {"key": "water_2", "display_name": "Water 2", "unit": "m³/h"},
                {"key": "water_3", "display_name": "Water 3", "unit": "m³/h"},
                {"key": "water_4", "display_name": "Water 4", "unit": "m³/h"},
                {"key": "steam_1", "display_name": "Steam 1", "unit": "kg/h"},
            ],
        }
    )

    assert len(charts) == 2
    assert charts[0]["is_full_width"] is True
    assert charts[1].get("is_tail_single") is True


def test_period_sensor_pdf_template_supports_tail_single_trend_card() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert "is-tail-single" in pdf_template
    assert ".utility-sensor-trend-card.is-tail-single" in pdf_css
