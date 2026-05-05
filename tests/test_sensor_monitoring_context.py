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
    assert "{% set is_card_only_period = period.type in ['weekly', 'monthly'] %}" in pdf_template
    assert '{% if sensor_monitoring_view.anomaly_rows and (flags.is_daily_report or not is_card_only_period) %}' in pdf_template
    assert 'utility-sensor-metric-note-detail' in pdf_template
    assert '<th class="col-sensor">Sensor</th>' in pdf_template
    assert '<th class="col-group">Group</th>' in pdf_template
    assert '{% else %}\n                                    <th class="col-group">Group</th>\n                                    <th class="col-sensor">Sensor</th>' in pdf_template


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


def test_period_sensor_rollup_merges_domestic_and_sakari_water_cards() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={},
        report_start=date(2025, 6, 23),
        report_end=date(2025, 6, 29),
    )

    rollup = context["period_rollup"]
    overview_keys = [card["key"] for card in rollup["overview_cards"]]
    group_keys = [group["key"] for group in rollup["groups"]]
    water_card = next(card for card in rollup["overview_cards"] if card["key"] == "domestic_water")
    water_group = next(group for group in rollup["groups"] if group["key"] == "domestic_water")

    assert rollup["enabled"] is True
    assert "sakari_water" not in overview_keys
    assert "sakari_water" not in group_keys
    assert water_card["label"] == "Domestic + Sakari Water"
    assert water_card["sensor_count"] == 2
    assert "critical_count" in water_card
    assert "warning_count" in water_card
    assert water_card["critical_count"] >= 0
    assert water_card["warning_count"] >= 0
    assert water_group["label"] == "Domestic + Sakari Water"
    assert water_group["sensor_count"] == 2
    assert [sensor["key"] for sensor in water_group["sensors"]] == ["dom_waterflow", "sak_waterflow"]
    assert [sensor["short_display_name"] for sensor in water_group["sensors"]] == ["Domestic Flow", "Sakari Flow"]

    anomaly_by_key = {row["sensor_key"]: row for row in rollup["anomaly_rows"]}
    assert anomaly_by_key["dom_waterflow"]["display_name"] == "Flow"
    assert anomaly_by_key["sak_waterflow"]["display_name"] == "Flow"
    assert anomaly_by_key["dch_coolingcap"]["display_name"] == "Cooling Capacity"
    assert anomaly_by_key["boi_steampress"]["display_name"] == "Steam Pressure"


def test_period_sensor_monitoring_context_builds_full_period_cluster_trends() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={
            date(2025, 5, 1): {
                "dom_waterflow": {"avg": 100.0, "non_null_count": 1, "sample_count": 1, "min": 100.0, "max": 100.0, "latest": 100.0},
                "sak_waterflow": {"avg": 200.0, "non_null_count": 1, "sample_count": 1, "min": 200.0, "max": 200.0, "latest": 200.0},
            },
            date(2025, 5, 2): {
                "dom_waterflow": {"avg": 110.0, "non_null_count": 1, "sample_count": 1, "min": 110.0, "max": 110.0, "latest": 110.0},
                "sak_waterflow": {"avg": 210.0, "non_null_count": 1, "sample_count": 1, "min": 210.0, "max": 210.0, "latest": 210.0},
            },
        },
        report_start=date(2025, 5, 1),
        report_end=date(2025, 5, 2),
    )

    trend_clusters = context["period_trend_clusters"]
    water_cluster = next(cluster for cluster in trend_clusters if cluster["cluster_key"] == "domestic_water")
    flow_chart = next(chart for chart in water_cluster["charts"] if chart["measurement_type"] == "flow")

    assert water_cluster["cluster_label"] == "Domestic + Sakari Water"
    assert water_cluster["sensor_count"] == 2
    assert water_cluster["chart_count"] == 1
    assert flow_chart["title"] == "Flow trend"
    assert [series["label"] for series in flow_chart["series"]] == ["Domestic Flow", "Sakari Flow"]
    assert [point["ts"] for point in flow_chart["series"][0]["points"]] == ["2025-05-01", "2025-05-02"]
    assert [point["value"] for point in flow_chart["series"][1]["points"]] == [200.0, 210.0]


def test_period_sensor_rendered_cluster_charts_use_date_axis_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    rendered_clusters = service._build_v3_period_sensor_trend_clusters(
        {
            "trend_mode": "aggregate_only",
            "period_trend_clusters": [
                {
                    "cluster_key": "domestic_water",
                    "cluster_label": "Domestic + Sakari Water",
                    "accent_color": "#2563eb",
                    "accent_tint": "rgba(37, 99, 235, 0.08)",
                    "sensor_count": 2,
                    "active_sensor_count": 2,
                    "alert_count": 0,
                    "charts": [
                        {
                            "chart_key": "domestic_water_flow",
                            "title": "Flow trend",
                            "measurement_type": "flow",
                            "unit": "m³/h",
                            "series": [
                                {
                                    "sensor_key": "dom_waterflow",
                                    "label": "Domestic Flow",
                                    "points": [
                                        {"ts": "2025-05-01", "value": 100.0},
                                        {"ts": "2025-05-02", "value": 110.0},
                                    ],
                                },
                                {
                                    "sensor_key": "sak_waterflow",
                                    "label": "Sakari Flow",
                                    "points": [
                                        {"ts": "2025-05-01", "value": 200.0},
                                        {"ts": "2025-05-02", "value": 210.0},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    )

    assert rendered_clusters[0]["charts"][0]["option"]["xAxis"]["data"] == ["05/01", "05/02"]


def test_period_sensor_detail_tables_cover_all_sensor_groups() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={},
        report_start=date(2025, 6, 23),
        report_end=date(2025, 6, 29),
    )

    tables = context["period_detail_tables"]
    assert [table["key"] for table in tables] == [
        "ico_chiller",
        "diode_chiller",
        "air_split",
        "boiler_water_split",
    ]

    ico_table = tables[0]
    assert [group["label"] for group in ico_table["column_groups"]] == ["ICO Chiller"]
    assert [column["display_name"] for column in ico_table["column_groups"][0]["columns"]] == [
        "Return Temp",
        "Supply Temp",
        "Supply Flow",
        "Supply Pressure",
        "Cooling Capacity",
    ]

    air_table = tables[2]
    assert [group["label"] for group in air_table["column_groups"]] == ["ICO Air", "DIODE Air"]
    assert [column["display_name"] for column in air_table["column_groups"][0]["columns"]] == ["Pressure", "Flow"]
    assert [column["display_name"] for column in air_table["column_groups"][1]["columns"]] == ["Pressure", "Flow"]
    assert air_table["column_groups"][1]["group_class"] == "is-split-group"
    assert air_table["column_groups"][1]["columns"][0]["header_class"] == "is-group-start"

    boiler_water_table = tables[3]
    assert [group["label"] for group in boiler_water_table["column_groups"]] == ["Boiler", "Domestic + Sakari Water"]
    assert [column["display_name"] for column in boiler_water_table["column_groups"][1]["columns"]] == ["Domestic Flow", "Sakari Flow"]
    assert len(boiler_water_table["rows"]) == 7


def test_period_sensor_detail_tables_emit_visual_meta_for_max_avg_and_weekend_rows() -> None:
    service = UtilityService()

    context = service.build_sensor_monitoring_context(
        daily_stats={
            date(2025, 6, 28): {
                "iac_press": {"max": 8.0, "avg": 4.0},
                "iac_airflow": {"max": 15.0, "avg": 10.0},
                "dac_press": {"max": 3.0, "avg": 0.0},
                "dac_airflow": {"max": 12.0, "avg": 6.0},
            },
            date(2025, 6, 29): {
                "iac_press": {"max": 10.0, "avg": 5.0},
                "iac_airflow": {"max": 20.0, "avg": 12.0},
                "dac_airflow": {"max": 14.0, "avg": 7.0},
            },
        },
        report_start=date(2025, 6, 28),
        report_end=date(2025, 6, 29),
    )

    air_table = next(table for table in context["period_detail_tables"] if table["key"] == "air_split")
    first_row = air_table["rows"][0]
    second_row = air_table["rows"][1]

    assert first_row["row_class"] == "is-weekend"
    assert second_row["row_class"] == "is-weekend"

    ico_pressure_day1 = first_row["column_groups"][0]["cells"][0]
    ico_pressure_day2 = second_row["column_groups"][0]["cells"][0]
    diode_pressure_day1 = first_row["column_groups"][1]["cells"][0]
    diode_pressure_day2 = second_row["column_groups"][1]["cells"][0]

    assert ico_pressure_day1["max_meta"]["line_class"] == "sensor-line-heat-3"
    assert ico_pressure_day2["max_meta"]["line_class"] == "sensor-line-heat-4"
    assert "is-peak" in ico_pressure_day2["max_meta"]["state_class"]
    assert diode_pressure_day1["avg_meta"]["state_class"] == "is-zero"
    assert diode_pressure_day2["max_meta"]["state_class"] == "is-missing"
    assert diode_pressure_day1["cell_class"] == "is-group-start"
    assert "--sensor-line-fill:" in ico_pressure_day1["avg_meta"]["style"]


def test_period_sensor_templates_keep_cluster_trends_below_detail_table() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    report_pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    view_table_pos = view_template.index('utility-sensor-period-detail-stack')
    view_cluster_pos = view_template.index('Sensor trend by cluster')
    pdf_table_pos = pdf_template.index('utility-sensor-period-detail-stack')
    pdf_cluster_pos = pdf_template.index('Sensor trend by cluster')

    assert view_table_pos < view_cluster_pos
    assert pdf_table_pos < pdf_cluster_pos
    assert 'sensor_monitoring.period_detail_tables' in view_template
    assert 'sensor_monitoring.period_detail_tables' in pdf_template
    assert 'utility-sensor-period-detail-legend-chip is-max' in view_template
    assert 'utility-sensor-period-detail-legend-chip is-avg' in pdf_template
    assert 'cell.max_meta.line_class' in view_template
    assert 'row.row_class' in pdf_template
    assert 'utility-sensor-section-label-title">Overview cards<' in pdf_template
    assert 'utility-sensor-section-label-title">Sensor avg cards<' in pdf_template
    assert 'utility-sensor-section-label-title">Daily Max / Avg detail<' in pdf_template
    assert 'utility-sensor-period-detail-pages' in pdf_template
    assert 'utility-sensor-period-detail-page pdf-keep-together' in pdf_template
    assert 'page_size = 2' in pdf_template
    assert '{% if is_card_only_period %}' in pdf_template
    assert '.utility-sensor-period-detail-card' in report_css
    assert '.utility-sensor-period-group-head' in report_css
    assert '.utility-sensor-line-badge' in report_css
    assert '.utility-sensor-period-detail-table tbody tr.is-weekend td' in report_css
    assert '.utility-sensor-period-detail-card' in report_pdf_css
    assert '.utility-sensor-period-group-head' in report_pdf_css
    assert '.utility-sensor-line-badge' in report_pdf_css
    assert '.utility-sensor-period-detail-table tbody tr.is-weekend td' in report_pdf_css
    assert '.utility-sensor-period-detail-pages {' in report_pdf_css
    assert '.utility-sensor-period-detail-page {' in report_pdf_css
    assert '.report-period-weekly .utility-sensor-group-head,' in report_pdf_css
    assert '.report-period-monthly .utility-sensor-group-head {' in report_pdf_css
    assert 'margin-bottom: 4px !important;' in report_pdf_css
    assert 'sensor_monitoring.period_trend_clusters_render or []' in view_template
    assert 'sensor_monitoring.period_trend_clusters_render or []' in pdf_template


def test_period_report_builder_hides_duplicate_summary_trend_cards() -> None:
    builder_source = (PROJECT_ROOT / "src/services/report_builder_service.py").read_text(encoding="utf-8")

    assert 'sensor_monitoring["period_trend_charts_render"] = []' in builder_source
    assert '"period_detail_tables": []' in builder_source
