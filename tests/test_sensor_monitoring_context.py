from __future__ import annotations

from datetime import date
from pathlib import Path

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
