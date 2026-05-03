from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService
from src.services.utility_service import UtilityService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_daily_sensor_monitoring_context_merges_water_in_overview_and_detail_groups() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={},
        report_start=date(2025, 6, 25),
        report_end=date(2025, 6, 25),
    )

    assert context["health_snapshot"]
    assert context["top_issues_preview"]
    assert context["missing_sensor_count"] == context["sensor_count"] - context["active_sensor_count"]

    group_keys = [group["key"] for group in context["groups"]]
    assert group_keys[-1] == "domestic_water"
    assert "sakari_water" not in group_keys

    overview_cards = context["overview_cards"]
    overview_keys = [card["key"] for card in overview_cards]
    assert overview_keys[-1] == "domestic_water"
    assert "sakari_water" not in overview_keys

    water_card = overview_cards[-1]
    assert water_card["label"] == "Domestic + Sakari Water"
    assert water_card["sensor_count"] == 2
    assert water_card["active_sensor_count"] == 0
    assert water_card["anomaly_count"] == 2

    domestic_group = next(group for group in context["groups"] if group["key"] == "domestic_water")

    assert domestic_group["label"] == "Domestic + Sakari Water"
    assert domestic_group["sensor_count"] == 2
    assert [sensor["key"] for sensor in domestic_group["sensors"]] == ["dom_waterflow", "sak_waterflow"]
    assert [sensor["short_display_name"] for sensor in domestic_group["sensors"]] == ["Domestic Flow", "Sakari Flow"]

    anomaly_rows = context["anomaly_rows"]
    water_anomaly = next(row for row in anomaly_rows if row["sensor_key"] == "sak_waterflow")
    assert water_anomaly["group_label"] == "Sakari Water"
    assert water_anomaly["display_name"] == "Sakari Flow"

    ico_air_group = next(group for group in context["groups"] if group["key"] == "ico_air")
    assert [sensor["short_display_name"] for sensor in ico_air_group["sensors"]] == ["Flow", "Pressure"]


def test_daily_pdf_utility_template_removes_insight_blocks_and_brings_metric_cards_up() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    assert "Sensor health snapshot" not in pdf_template
    assert "Top issues today" not in pdf_template
    assert "sensor_monitoring_view.health_snapshot" not in pdf_template
    assert "sensor_monitoring_view.top_issues_preview" not in pdf_template


def test_daily_sensor_monitoring_trend_clusters_merge_domestic_and_sakari_water() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={},
        report_start=date(2025, 5, 31),
        report_end=date(2025, 5, 31),
        raw_rows=[
            {
                "dt": datetime(2025, 5, 31, 0, 0),
                "dom_waterflow": 1.0,
                "sak_waterflow": 2.0,
            },
            {
                "dt": datetime(2025, 5, 31, 1, 0),
                "dom_waterflow": 1.5,
                "sak_waterflow": 2.5,
            },
        ],
    )

    trend_clusters = context["trend_clusters"]
    water_cluster = next(cluster for cluster in trend_clusters if cluster["cluster_key"] == "domestic_water")

    assert water_cluster["cluster_label"] == "Domestic + Sakari Water"
    assert water_cluster["sensor_count"] == 2
    assert water_cluster["chart_count"] == 1
    flow_chart = water_cluster["charts"][0]
    assert flow_chart["title"] == "Flow trend"
    assert [series["label"] for series in flow_chart["series"]] == ["Domestic Flow", "Sakari Flow"]


def test_daily_pdf_utility_template_keeps_all_daily_sensor_cards_with_overview_before_anomaly_scan() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    assert "sensor_group_preview = sensor_monitoring_view.groups if flags.is_daily_report else []" in pdf_template
    assert "sensor_group_remaining = [] if flags.is_daily_report else sensor_monitoring_view.groups" in pdf_template
    assert 'utility-sensor-group-preview-block{% if not flags.is_daily_report %} pdf-keep-together{% endif %}' in pdf_template
    assert 'utility-sensor-anomaly-block{% if flags.is_daily_report %} page-break-before{% endif %}' in pdf_template
    assert '<th class="col-group">Group</th>' in pdf_template
    assert '<th class="col-sensor">Sensor</th>' in pdf_template


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
