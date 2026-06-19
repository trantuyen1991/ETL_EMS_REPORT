from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_daily_utility_comparison_legend_uses_today_yesterday() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    charts = service._build_v3_utility_charts(
        utility_object={
            "current": {
                "metadata": {
                    "water": {"display_name": "RO Water", "unit": "m³"},
                    "steam": {"display_name": "Plant Steam", "unit": "kg"},
                    "air": {"display_name": "Compressed Air", "unit": "Nm³"},
                }
            },
            "comparison": {
                "water": {"current": 120.0, "previous": 100.0},
                "steam": {"current": 80.0, "previous": 70.0},
                "air": {"current": 60.0, "previous": 55.0},
            },
        },
        period={"type": "daily"},
    )

    wide_series = charts["comparison_split"]["wide"]["option"]["series"]
    narrow_series = charts["comparison_split"]["narrow"]["option"]["series"]

    assert wide_series[0]["name"] == "Today"
    assert wide_series[1]["name"] == "Yesterday"
    assert narrow_series[0]["name"] == "Today"
    assert narrow_series[1]["name"] == "Yesterday"


def _build_utility_period_object() -> dict:
    return {
        "current": {
            "metadata": {
                "water": {"display_name": "RO Water", "unit": "m³", "category": "water"},
                "steam": {"display_name": "Plant Steam", "unit": "kg", "category": "steam"},
                "air": {"display_name": "Compressed Air", "unit": "Nm³", "category": "compressed_air"},
            },
            "timeseries": [
                {"dt": "2025-05-12", "water": 100.0, "steam": 80.0, "air": 60.0},
                {"dt": "2025-05-13", "water": 120.0, "steam": 70.0, "air": 55.0},
            ],
        },
        "comparison": {
            "water": {"current": 120.0, "previous": 100.0},
            "steam": {"current": 80.0, "previous": 70.0},
            "air": {"current": 60.0, "previous": 55.0},
        },
    }


def _build_utility_energy_object() -> dict:
    return {
        "current": {
            "daily_tables": [
                {
                    "area_key": "plant",
                    "rows": [
                        {
                            "date": "2025-05-12",
                            "cells": [
                                {"key": "AIR-M1", "meter_role": "meter", "raw_value": 120.0},
                                {"key": "CHW-M1", "meter_role": "meter", "raw_value": 80.0},
                                {"key": "STM-M1", "meter_role": "meter", "raw_value": 50.0},
                            ],
                        },
                        {
                            "date": "2025-05-13",
                            "cells": [
                                {"key": "AIR-M1", "meter_role": "meter", "raw_value": 118.0},
                                {"key": "CHW-M1", "meter_role": "meter", "raw_value": 82.0},
                                {"key": "STM-M1", "meter_role": "meter", "raw_value": 48.0},
                            ],
                        },
                    ],
                }
            ]
        },
        "previous": {
            "daily_tables": [
                {
                    "area_key": "plant",
                    "rows": [
                        {
                            "date": "2025-05-05",
                            "cells": [
                                {"key": "AIR-M1", "meter_role": "meter", "raw_value": 110.0},
                                {"key": "CHW-M1", "meter_role": "meter", "raw_value": 78.0},
                                {"key": "STM-M1", "meter_role": "meter", "raw_value": 44.0},
                            ],
                        }
                    ],
                }
            ]
        },
    }


def _build_utility_energy_period_object() -> dict:
    utility_object = _build_utility_period_object()
    utility_object["current"]["metadata"].update({
        "chw": {
            "display_name": "Chilled Water",
            "unit": "RT",
            "category": "chilled_water",
            "energy_area": "plant",
            "energy_meters": ["CHW-M1"],
        },
        "steam": {
            "display_name": "Plant Steam",
            "unit": "kg",
            "category": "steam",
            "energy_area": "plant",
            "energy_meters": ["STM-M1"],
        },
        "air": {
            "display_name": "Compressed Air",
            "unit": "Nm³",
            "category": "compressed_air",
            "energy_area": "plant",
            "energy_meters": ["AIR-M1"],
        },
    })
    utility_object["comparison"].update({
        "chw": {"current": 92.0, "previous": 88.0},
    })
    return utility_object


def test_daily_utility_trend_subtitle_uses_today_wording() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    charts = service._build_v3_utility_charts(
        utility_object={
            "current": {
                "metadata": {
                    "water": {"display_name": "RO Water", "unit": "m³", "category": "water"},
                },
                "timeseries": [
                    {"dt": "2025-05-18", "water": 120.0},
                ],
            },
            "comparison": {
                "water": {"current": 120.0, "previous": 100.0},
            },
        },
        period={"type": "daily"},
    )

    assert charts["period_type_trend"]["subtitle"] == "Today total by utility group"
    legend = charts["period_type_trend"]["option"]["legend"]
    assert legend["bottom"] == 0
    assert legend["left"] == "center"


def test_periodic_utility_charts_use_period_aware_wording() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    weekly_charts = service._build_v3_utility_charts(
        utility_object=_build_utility_period_object(),
        period={"type": "weekly"},
    )
    monthly_charts = service._build_v3_utility_charts(
        utility_object=_build_utility_period_object(),
        period={"type": "monthly"},
    )

    assert weekly_charts["comparison_bar"]["subtitle"] == "This Week vs last week total by load type"
    assert weekly_charts["comparison_bar"]["option"]["series"][0]["name"] == "This Week"
    assert weekly_charts["comparison_bar"]["option"]["series"][1]["name"] == "Last Week"
    assert weekly_charts["comparison_split"]["wide"]["option"]["series"][0]["name"] == "This Week"
    assert weekly_charts["comparison_split"]["wide"]["option"]["series"][1]["name"] == "Last Week"
    assert weekly_charts["deviation_vs_yesterday"]["title"] == "Deviation vs Last Week"
    assert weekly_charts["deviation_vs_yesterday"]["subtitle"] == "This Week versus last week"
    assert weekly_charts["period_type_trend"]["subtitle"] == "Daily totals for this week by utility group"
    assert weekly_charts["period_mix"]["title"] == "This Week mix"
    assert weekly_charts["period_insight_split"]["wide"]["title"] == "Utility daily total heatmap"
    assert weekly_charts["period_insight_split"]["wide"]["option"]["xAxis"]["data"][0] == "May 12 (Mon)"
    assert weekly_charts["period_insight_split"]["narrow"] == {}

    assert monthly_charts["comparison_bar"]["subtitle"] == "This Month vs last month total by load type"
    assert monthly_charts["comparison_bar"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["comparison_bar"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["comparison_split"]["wide"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["comparison_split"]["wide"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["deviation_vs_yesterday"]["title"] == "Deviation vs Last Month"
    assert monthly_charts["deviation_vs_yesterday"]["subtitle"] == "This Month versus last month"
    assert monthly_charts["period_type_trend"]["subtitle"] == "Daily totals for this month by utility group"
    assert monthly_charts["period_mix"]["title"] == "This Month mix"
    assert monthly_charts["period_insight_split"]["wide"] == {}
    assert monthly_charts["period_insight_split"]["narrow"] == {}


def test_utility_detail_rows_use_per_column_heat_and_family_tints() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    utility_object = {
        "current": {
            "metadata": {
                "domestic_water": {"display_name": "Domestic Water", "unit": "m³", "category": "water"},
                "ico_air": {"display_name": "ICO Air", "unit": "Nm³", "category": "compressed_air"},
                "diode_chilled_water": {"display_name": "Diode Chilled Water", "unit": "RT", "category": "chilled_water"},
                "steam": {"display_name": "Steam", "unit": "kg", "category": "steam"},
            },
            "timeseries": [
                {"dt": date(2025, 5, 12), "domestic_water": 10.0, "ico_air": 100.0, "diode_chilled_water": 0.0, "steam": None},
                {"dt": date(2025, 5, 13), "domestic_water": 20.0, "ico_air": 50.0, "diode_chilled_water": 25.0, "steam": None},
            ],
        }
    }

    columns = service._build_daily_columns(utility_object)
    rows = service._build_daily_rows(utility_object)

    assert columns[0]["family_class"] == "utility-detail-family-water"
    assert columns[0]["unit_display"] == "m³"
    assert "--utility-detail-header-text: #005496;" in columns[0]["header_style"]
    assert columns[1]["family_class"] == "utility-detail-family-compressed-air"
    assert columns[1]["unit_display"] == "Nm³"
    assert columns[2]["family_class"] == "utility-detail-family-chilled-water"
    assert columns[2]["unit_display"] == "RT"
    assert columns[3]["family_class"] == "utility-detail-family-steam"
    assert columns[3]["unit_display"] == "kg"

    first_row = rows[0]["daily_values"]
    second_row = rows[1]["daily_values"]

    assert first_row[0]["heat_class"] == "detail-heat-2"
    assert first_row[0]["family_class"] == "utility-detail-family-water"
    assert second_row[0]["state_class"] == "value-max"
    assert "--utility-detail-cell-accent: #005496;" in second_row[0]["cell_style"]
    assert first_row[1]["state_class"] == "value-max"
    assert "--utility-detail-cell-accent: #6f9a6d;" in first_row[1]["cell_style"]
    assert first_row[2]["state_class"] == "value-zero"
    assert second_row[2]["state_class"] == "value-max"
    assert first_row[3]["state_class"] == "value-missing"


def test_utility_templates_use_last_period_fallback_copy() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    expected_note = 'labels.previous_period | lower if labels.previous_period else "last period"'

    assert expected_note in view_template
    assert expected_note in pdf_template
    assert 'previous period' not in view_template
    assert 'previous period' not in pdf_template


def test_utility_detail_templates_use_family_headers_and_heat_cells() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert 'class="utility-detail-col-head {{ column.family_class }}"' in view_template
    assert 'class="utility-detail-col-head {{ column.family_class }}"' in pdf_template
    assert '<span class="utility-detail-col-name">{{ column.display_name }}</span>' in view_template
    assert '<span class="utility-detail-col-name">{{ column.display_name }}</span>' in pdf_template
    assert '<span class="utility-detail-col-unit">{{ column.unit_display }}</span>' in view_template
    assert '<span class="utility-detail-col-unit">{{ column.unit_display }}</span>' in pdf_template
    assert 'class="col-value utility-detail-value-cell {{ cell.family_class }} {{ cell.heat_class }} {{ cell.state_class }}"' in view_template
    assert 'class="col-value utility-detail-value-cell {{ cell.family_class }} {{ cell.heat_class }} {{ cell.state_class }}"' in pdf_template
    assert '{% if cell.cell_style %} style="{{ cell.cell_style }}"{% endif %}' in view_template
    assert '{% if cell.cell_style %} style="{{ cell.cell_style }}"{% endif %}' in pdf_template
    assert '.utility-detail-table .utility-detail-col-head {' in report_css
    assert '.utility-detail-table .utility-detail-value-cell {' in report_css
    assert '.utility-detail-table .utility-detail-value-cell.value-zero {' in report_css
    assert '.utility-detail-table .utility-detail-value-cell.value-missing {' in report_css
    assert '.utility-detail-table .utility-detail-value-cell.value-max {' in report_css
    assert '.utility-detail-table .utility-detail-col-unit {' in report_css
    assert '.utility-detail-table .utility-detail-col-head {' in pdf_css
    assert '.utility-detail-table .utility-detail-value-cell {' in pdf_css
    assert '.utility-detail-table .utility-detail-value-cell.value-zero {' in pdf_css
    assert '.utility-detail-table .utility-detail-value-cell.value-missing {' in pdf_css
    assert '.utility-detail-table .utility-detail-value-cell.value-max {' in pdf_css
    assert '.utility-detail-table .utility-detail-col-unit {' in pdf_css


def test_daily_view_utility_template_marks_comparison_cards_for_compact_layout() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")

    assert 'utility-chart-card-compare-compact' in view_template
    assert 'utility-period-insight-grid' in view_template
    assert 'utility-period-insight-heatmap-chart' in view_template
    assert 'utility-period-mix-chart' in view_template
    utility_blocks_macro = (PROJECT_ROOT / 'src/templates/report/macros/utility_blocks.html').read_text(encoding='utf-8')
    assert "block.visual_variant == 'mix-card'" in utility_blocks_macro
    assert 'utility-energy-distribution-card.is-mix-style .utility-energy-distribution-chart' in report_css


def test_daily_view_sensor_monitoring_uses_metric_table_layout() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    sensor_macro = (PROJECT_ROOT / "src/templates/report/macros/sensor_monitoring.html").read_text(encoding="utf-8")

    assert '{% if flags.is_daily_report %}' in view_template
    assert 'utility-sensor-metric-table' in view_template
    assert 'utility-sensor-metric-row' in view_template
    assert 'utility-sensor-group-icon' in view_template
    assert 'sensor_ui.group_icon(group.key)' in view_template
    assert 'sensor_ui.metric_icon(sensor)' in view_template
    assert 'sensor_ui.status_icon(sensor)' in view_template
    assert 'sensor_monitoring_view.overview_cards' in view_template
    assert 'is-mobile-daily-overview' in view_template
    assert 'is-daily-overview-card' in view_template
    assert 'is-reference-card' in view_template
    assert 'utility-sensor-overview-primary-row' in view_template
    assert 'utility-sensor-group-card {% if flags.is_daily_report %}is-daily-metric-card{% else %}is-reference-metric-card{% endif %}' in view_template
    assert 'sensor.short_display_name or sensor.display_name' in view_template
    assert "{% if sensor.has_alert and (sensor.flag_summary or sensor.flag_detail_summary) %}" in view_template
    assert '<span class="utility-sensor-metric-note-main">{{ sensor.flag_summary or \'Alert\' }}</span>' in view_template
    assert '<div class="utility-sensor-metric-value col-avg">' in view_template
    assert 'utility-sensor-metric-value col-avg {% if flags.is_daily_report and sensor.has_alert %}has-alert-message' not in view_template
    assert 'utility-sensor-metric-submeta' not in view_template
    assert 'has-alert-message' not in report_css
    assert '.report-family-daily .utility-sensor-metric-note-detail' in report_css
    assert '.report-family-daily .utility-sensor-metric-table' in report_css
    assert '.report-family-daily .utility-sensor-group-card.is-daily-metric-card::before' in report_css
    assert '.report-family-daily .utility-sensor-group-card.group-key-sakari_water' in report_css
    assert '.report-family-daily .utility-sensor-overview-title {' in report_css
    assert '.report-family-daily .utility-sensor-overview-grid.is-mobile-daily-overview' in report_css
    assert 'font-size: 13px;' in report_css
    assert 'font-weight: 900;' in report_css
    assert 'line-height: 1.3;' in report_css
    assert 'text-transform: uppercase;' in report_css
    assert 'letter-spacing: 0.02em;' in report_css
    assert 'color: var(--sensor-accent, #183153);' in report_css
    assert '.report-family-daily .utility-sensor-metric-status-main' in report_css
    assert '.report-family-periodic .utility-sensor-overview-card.is-reference-card' in report_css
    assert 'border-top: 4px solid var(--sensor-accent, #64748b);' in report_css
    assert '.report-family-periodic .utility-sensor-overview-title {' in report_css
    assert 'font-size: 13px;' in report_css
    assert 'font-weight: 900;' in report_css
    assert 'line-height: 1.3;' in report_css
    assert 'text-transform: uppercase;' in report_css
    assert 'letter-spacing: 0.02em;' in report_css
    assert 'color: var(--sensor-accent, #183153);' in report_css
    assert '.report-family-periodic .utility-sensor-group-card.is-reference-metric-card' in report_css
    assert '.report-family-periodic .utility-sensor-group-heading-copy {' in report_css
    assert 'align-items: center;' in report_css
    assert '.report-family-periodic .utility-sensor-group-title {' in report_css
    assert 'font-size: 13px;' in report_css
    assert 'font-weight: 900;' in report_css
    assert 'color: var(--sensor-accent, #183153);' in report_css
    assert '.utility-sensor-group-icon svg *,' in report_css
    assert '.report-family-periodic .utility-sensor-anomaly-table thead th' in report_css
    assert 'macro metric_icon(sensor)' in sensor_macro
    assert 'macro status_icon(sensor)' in sensor_macro


def test_daily_pdf_sensor_monitoring_uses_metric_table_layout() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert 'utility-sensor-metric-table utility-sensor-metric-table-pdf' in pdf_template
    assert 'utility-sensor-group-card {% if flags.is_daily_report %}is-daily-metric-card{% endif %} group-key-{{ group.key }}' in pdf_template
    assert 'utility-sensor-group-card {% if flags.is_daily_report %}is-daily-metric-card{% else %}is-reference-metric-card{% endif %} group-key-{{ group.key }}' in pdf_template
    assert 'utility-sensor-overview-card is-reference-card' in pdf_template
    assert 'sensor_ui.group_icon(group.key)' in pdf_template
    assert 'sensor_ui.metric_icon(sensor)' in pdf_template
    assert 'sensor_ui.status_icon(sensor)' in pdf_template
    assert '{{ sensor.short_display_name or sensor.display_name }}{% if sensor.unit %} ({{ sensor.unit }}){% endif %}' in pdf_template
    assert 'utility-sensor-metric-submeta' not in pdf_template
    assert '.report-period-daily .utility-sensor-group-grid' in pdf_css
    assert '.report-period-daily .utility-sensor-group-card.group-key-sakari_water' in pdf_css
    assert 'grid-column: auto !important;' in pdf_css
    assert '.report-family-daily .utility-sensor-overview-title {' in pdf_css
    assert 'font-size: 9.2px !important;' in pdf_css
    assert 'font-weight: 900 !important;' in pdf_css
    assert 'line-height: 1.15 !important;' in pdf_css
    assert 'text-transform: uppercase !important;' in pdf_css
    assert 'letter-spacing: 0.02em !important;' in pdf_css
    assert 'color: var(--sensor-accent, #1e3a8a) !important;' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-table-head' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-note {' in pdf_css
    assert 'color: #22a06b !important;' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-note.is-warning {' in pdf_css
    assert 'color: #f59e0b !important;' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-note.is-critical {' in pdf_css
    assert 'color: #ef4444 !important;' in pdf_css
    assert '.report-family-periodic .utility-sensor-overview-card.is-reference-card' in pdf_css
    assert 'border-top: 4px solid var(--sensor-accent, #64748b) !important;' in pdf_css
    assert '.report-family-periodic .utility-sensor-overview-title {' in pdf_css
    assert 'font-size: 9.2px !important;' in pdf_css
    assert 'font-weight: 900 !important;' in pdf_css
    assert 'line-height: 1.15 !important;' in pdf_css
    assert 'text-transform: uppercase !important;' in pdf_css
    assert 'letter-spacing: 0.02em !important;' in pdf_css
    assert 'color: var(--sensor-accent, #1e3a8a) !important;' in pdf_css
    assert '.report-family-periodic .utility-sensor-group-card.is-reference-metric-card' in pdf_css
    assert '.report-family-periodic .utility-sensor-group-heading-copy {' in pdf_css
    assert 'align-items: center !important;' in pdf_css
    assert '.report-family-periodic .utility-sensor-group-title {' in pdf_css
    assert 'font-size: 9.2px !important;' in pdf_css
    assert 'font-weight: 900 !important;' in pdf_css
    assert 'color: var(--sensor-accent, #1e3a8a) !important;' in pdf_css
    assert '.utility-sensor-group-icon svg *,' in pdf_css
    assert '.report-family-periodic .utility-sensor-anomaly-table .col-reason' in pdf_css
    assert 'display: grid !important;' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-table-body' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-title-row' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-value' in pdf_css
    assert '.report-period-daily .utility-sensor-metric-status-main' in pdf_css
    assert '.report-period-daily .utility-sensor-anomaly-table .col-group' in pdf_css
    assert '.report-period-daily .utility-sensor-anomaly-table .col-reason' in pdf_css
    assert 'page-break-before: auto !important;' in pdf_css


def test_utility_deviation_chart_uses_compact_delta_value_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    option = service._build_v3_utility_deviation_option([
        {"display_name": "DIODE Air", "unit": "m³", "current": 9750.0, "previous": 1000.0},
    ])

    label = option["series"][0]["data"][0]["label"]["formatter"]

    assert "8.8k m³" in label
    assert "8,750.00" not in label


def test_utility_pdf_deviation_chart_uses_shorter_value_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_utility_deviation_option([
        {"display_name": "RO Water", "unit": "m³", "current": 120.0, "previous": 100.0},
        {"display_name": "Plant Steam", "unit": "kg", "current": 60.0, "previous": 90.0},
    ])

    labels = [item["label"]["formatter"] for item in option["series"][0]["data"]]

    assert labels[0].endswith("%")
    assert "(" not in labels[0]
    assert labels[1].endswith("%")
    assert "(" not in labels[1]


def test_utility_pdf_distribution_chart_uses_compact_donut_geometry() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_utility_energy_distribution_option(
        items=[
            {"name": "Air", "value": 60.0, "itemStyle": {"color": "#00aa88"}},
            {"name": "Steam", "value": 40.0, "itemStyle": {"color": "#8844cc"}},
        ],
        total_value=100.0,
        period_badge="This Month",
        period_type="monthly",
    )

    series = option["series"][0]

    assert series["radius"] == ["40%", "76%"]
    assert series["center"] == ["49%", "54%"]
    assert series["label"]["fontSize"] == 7


def test_weekly_utility_energy_distribution_uses_mix_style_layout() -> None:
    service = ReportBuilderService()
    service._style_config = json.loads((PROJECT_ROOT / "config/report_style.json").read_text(encoding="utf-8"))["reportStyle"]
    service._render_mode = "html"

    context = service._build_v3_utility_energy_context(
        utility_object=_build_utility_energy_period_object(),
        energy_object=_build_utility_energy_object(),
        period={"type": "weekly"},
    )

    distribution = context["charts"]["distribution"]
    block = next(item for item in context["layout"]["blocks"] if item["kind"] == "distribution")
    series = distribution["option"]["series"][0]

    assert context["charts"]["trend"]["title"] == "Utility Energy Trend (This Week)"
    assert distribution["visual_variant"] == "mix-card"
    assert block["visual_variant"] == "mix-card"
    assert "is-mix-style" in block["card_classes"]
    assert distribution["option"]["legend"]["left"] == "center"
    assert distribution["option"]["legend"]["bottom"] == 0
    assert distribution["option"]["title"][1]["text"] == "Total"
    assert distribution["option"]["title"][0]["top"] == "34%"
    assert distribution["option"]["title"][1]["top"] == "48%"
    assert series["radius"] == ["42%", "78%"]
    assert series["center"] == ["50%", "45%"]
    assert series["startAngle"] == 180
    assert series["label"]["formatter"] == "{b}\n{d}%"


def test_weekly_utility_deviation_chart_centers_zero_and_inverts_label_direction() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    option = service._build_v3_utility_deviation_option(
        [
            {"display_name": "ICO Air", "unit": "m³", "current": 100.0, "previous": 50.0},
            {"display_name": "Steam", "unit": "m³", "current": 25.0, "previous": 50.0},
        ],
        period_type="weekly",
    )

    items = option["series"][0]["data"]
    positive_item = items[0]
    negative_item = items[1]

    assert option["xAxis"]["min"] == -option["xAxis"]["max"]
    assert option["xAxis"]["max"] > 100.0
    assert positive_item["value"] == 100.0
    assert positive_item["label"]["position"] == "left"
    assert negative_item["value"] == -50.0
    assert negative_item["label"]["position"] == "right"


def test_utility_periodic_layout_css_matches_weekly_delta_width_and_height_targets() -> None:
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert 'grid-template-columns: minmax(0, 6fr) minmax(0, 4fr);' in report_css
    assert '.utility-periodic-chart-grid .utility-comparison-chart-daily {' in report_css
    assert 'height: var(--report-components-report-section-utility-chart-period-trend-height-view, 326px);' in report_css
    assert '.report-period-weekly .utility-energy-trend-chart {' in report_css
    assert 'height: var(--report-components-report-section-utility-chart-energy-trend-weekly-height-view, 354px);' in report_css
    assert '.report-period-weekly .utility-energy-distribution-card.is-mix-style .utility-energy-distribution-chart {' in report_css
    assert 'height: var(--report-components-report-section-utility-chart-energy-distribution-weekly-height-view, 317px);' in report_css
    assert '.utility-period-insight-grid .utility-chart-card {' in report_css
    assert 'height: var(--report-components-report-section-utility-chart-period-insight-mix-height-view, 252px);' in report_css
    assert 'grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;' in pdf_css
    assert '.report-period-weekly .utility-energy-trend-chart {' in pdf_css
    assert 'height: var(--report-components-report-section-utility-chart-energy-trend-weekly-height-pdf, 253px) !important;' in pdf_css
    assert '.report-period-weekly .utility-energy-distribution-card.is-mix-style .utility-energy-distribution-chart {' in pdf_css
    assert 'height: var(--report-components-report-section-utility-chart-energy-distribution-weekly-height-pdf, 239px) !important;' in pdf_css
    assert 'height: var(--report-components-report-section-utility-chart-period-trend-height-pdf, 228px) !important;' in pdf_css
    assert 'height: var(--report-components-report-section-utility-chart-period-insight-mix-height-pdf, 184px) !important;' in pdf_css


def test_monthly_utility_distribution_chart_stacks_full_width_on_mobile() -> None:
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    media_900_start = report_css.index("@media (max-width: 900px)")
    media_700_start = report_css.index("@media (max-width: 700px)")
    media_900_css = report_css[media_900_start:media_700_start]

    assert (
        '.utility-energy-chart-grid[data-layout-variant="monthly"] .utility-chart-block-energy-distribution {\n'
        "                grid-column: 1 / -1;\n"
        "                width: 100%;\n"
        "                max-width: 100%;"
    ) in media_900_css
    assert (
        '.utility-energy-chart-grid[data-layout-variant="monthly"] .utility-energy-distribution-layout {\n'
        "                display: flex;\n"
        "                flex-direction: column;"
    ) in media_900_css
    assert (
        '.utility-energy-chart-grid[data-layout-variant="monthly"] .utility-chart-block-energy-deviation,\n'
        '            .utility-energy-chart-grid[data-layout-variant="monthly"] .utility-chart-block-energy-distribution {\n'
        "                grid-column: 1 / -1;"
    ) in report_css
    assert (
        ".utility-chart-block-energy-distribution,\n"
        "            .utility-energy-distribution-card {\n"
        "                width: 100%;\n"
        "                max-width: 100%;"
    ) in report_css


def test_utility_pdf_deviation_chart_uses_compact_axis_spacing() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_utility_deviation_option([
        {"display_name": "Sakari Water", "unit": "m³", "current": 696.0, "previous": 37.0},
        {"display_name": "Steam", "unit": "m³", "current": 0.0, "previous": 0.0},
        {"display_name": "ICO Air", "unit": "m³", "current": 1.0, "previous": 23073.0},
    ])

    assert option["grid"]["bottom"] == 36
    assert option["xAxis"]["axisLabel"]["show"] is False
    assert option["yAxis"]["axisLabel"]["fontSize"] == 8
    assert option["series"][0]["barWidth"] == 10


def test_utility_deviation_chart_moves_near_zero_labels_away_from_center() -> None:
    service = ReportBuilderService()
    service._style_config = {
        "components": {
            "report": {
                "section": {
                    "utility": {
                        "chart": {
                            "deviation": {
                                "valueLabel": {
                                    "positivePosition": "left",
                                    "negativePosition": "right",
                                    "nearZeroPositivePosition": "right",
                                    "nearZeroNegativePosition": "left",
                                    "nearZeroThreshold": 4,
                                    "nearZeroDistance": 10,
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    service._render_mode = "pdf"

    option = service._build_v3_utility_deviation_option([
        {"display_name": "Near Zero Up", "unit": "%", "current": 103.35, "previous": 100.0},
        {"display_name": "Near Zero Down", "unit": "%", "current": 98.25, "previous": 100.0},
        {"display_name": "Large Drop", "unit": "%", "current": 76.63, "previous": 100.0},
    ])

    up_point = option["series"][0]["data"][0]
    down_point = option["series"][0]["data"][1]
    large_drop_point = option["series"][0]["data"][2]

    assert up_point["label"]["position"] == "right"
    assert up_point["label"]["distance"] == 10
    assert down_point["label"]["position"] == "left"
    assert down_point["label"]["distance"] == 10
    assert large_drop_point["label"]["position"] == "right"
    assert large_drop_point["label"]["distance"] == 3


def test_daily_sensor_dual_axis_chart_uses_style_config_tokens() -> None:
    service = ReportBuilderService()
    service._render_mode = "html"
    service._style_config = {
        "components": {
            "report": {
                "section": {
                    "utility": {
                        "chart": {
                            "sensorCluster": {
                                "height": {"view": "310px", "pdf": "150px"},
                                "dualAxis": {
                                    "legend": {"top": 4, "right": 10, "itemGap": 18},
                                    "grid": {"left": 44, "right": 18, "top": 32, "bottom": 26, "containLabel": False},
                                    "leftAxis": {"nameGap": 16, "labelMargin": 11, "nameTextPadding": [20, 0, 0, 0]},
                                    "rightAxis": {"offset": 3, "nameGap": 5, "labelMargin": 2, "nameTextPadding": [0, 2, 0, 0]},
                                    "xAxis": {"axisLabel": {"fontSize": 11, "margin": 6, "interval": 0}},
                                    "axisLine": {"show": True},
                                    "splitLine": {"primaryOnly": False},
                                    "series": {"lineWidth": 3.4, "areaOpacity": 0.15, "symbolSize": 7, "showSymbol": True},
                                    "markPoint": {"symbolSize": 12, "label": {"fontSize": 11, "distance": 10, "padding": [3, 6], "borderRadius": 5, "backgroundColor": "rgba(255,255,255,0.88)"}},
                                },
                            }
                        }
                    }
                }
            }
        }
    }

    option = service._build_v3_sensor_intraday_option(
        {
            "series": [
                {
                    "sensor_key": "flow_1",
                    "label": "Flow",
                    "color": "#005496",
                    "points": [
                        {"ts": "2025-06-25 08:00", "value": 10.0},
                        {"ts": "2025-06-25 09:00", "value": 12.0},
                    ],
                },
                {
                    "sensor_key": "pressure_1",
                    "label": "Pressure",
                    "color": "#6f9a6d",
                    "points": [
                        {"ts": "2025-06-25 08:00", "value": 3.0},
                        {"ts": "2025-06-25 09:00", "value": 2.0},
                    ],
                },
            ]
        },
        y_axes=[
            {"name": "m³/h", "series_keys": ["flow_1"]},
            {"name": "bar", "series_keys": ["pressure_1"]},
        ],
    )

    assert option["legend"]["top"] == 4
    assert option["legend"]["right"] == 10
    assert option["legend"]["itemGap"] == 18
    assert option["grid"] == {"left": 44, "right": 18, "top": 32, "bottom": 26, "containLabel": False}
    assert option["yAxis"][0]["nameGap"] == 16
    assert option["yAxis"][0]["axisLabel"]["margin"] == 11
    assert option["yAxis"][0]["nameTextStyle"]["padding"] == [20, 0, 0, 0]
    assert option["yAxis"][1]["offset"] == 3
    assert option["yAxis"][1]["nameGap"] == 5
    assert option["yAxis"][1]["axisLabel"]["margin"] == 2
    assert option["yAxis"][1]["splitLine"]["show"] is True
    assert option["xAxis"]["axisLabel"]["fontSize"] == 11
    assert option["xAxis"]["axisLabel"]["margin"] == 6
    assert option["xAxis"]["axisLabel"]["interval"] == 0
    assert option["series"][0]["showSymbol"] is True
    assert option["series"][0]["symbolSize"] == 7
    assert option["series"][0]["lineStyle"]["width"] == 3.4
    assert option["series"][0]["markPoint"]["symbolSize"] == 12
    assert option["series"][0]["markPoint"]["data"][0]["label"]["fontSize"] == 11
    assert option["series"][0]["markPoint"]["data"][0]["label"]["distance"] == 10


def test_report_style_json_contains_sensor_dual_axis_controls_and_height_tokens() -> None:
    style_cfg = json.loads((PROJECT_ROOT / "config/report_style.json").read_text(encoding="utf-8"))
    utility_chart_cfg = style_cfg["reportStyle"]["components"]["report"]["section"]["utility"]["chart"]
    sensor_cluster = utility_chart_cfg["sensorCluster"]
    dual_axis = sensor_cluster["dualAxis"]
    deviation_value_label = utility_chart_cfg["deviation"]["valueLabel"]
    period_insight_heatmap = utility_chart_cfg["periodInsightHeatmap"]
    period_insight_mix = utility_chart_cfg["periodInsightMix"]
    energy_distribution = utility_chart_cfg["energyDistribution"]

    assert sensor_cluster["height"]["view"] == "280px"
    assert sensor_cluster["height"]["pdf"] == "140px"
    assert sensor_cluster["height"]["periodicDualAxis"]["view"] == "308px"
    assert sensor_cluster["height"]["periodicDualAxis"]["pdf"] == "140px"
    assert sensor_cluster["height"]["periodicPage1Summary"]["view"] == "280px"
    assert sensor_cluster["height"]["periodicPage1DualAxis"]["view"] == "308px"
    assert sensor_cluster["height"]["periodicPage2Summary"]["pdf"] == "140px"
    assert sensor_cluster["height"]["periodicPage2DualAxis"]["pdf"] == "140px"
    assert "legend" in sensor_cluster["periodicChillerSummary"]
    assert "grid" in sensor_cluster["periodicChillerSummary"]
    assert "bottom" in sensor_cluster["periodicChillerSummary"]["grid"]
    assert "page1" in sensor_cluster["periodicPages"]
    assert "page2" in sensor_cluster["periodicPages"]
    assert "summary" in sensor_cluster["periodicPages"]["page1"]
    assert "dualAxis" in sensor_cluster["periodicPages"]["page1"]
    assert "legend" in sensor_cluster["periodicPages"]["page1"]["summary"]
    assert "grid" in sensor_cluster["periodicPages"]["page1"]["dualAxis"]
    assert "xAxis" in sensor_cluster["periodicPages"]["page2"]["summary"]
    assert "legend" in sensor_cluster["periodicPages"]["page2"]["dualAxis"]
    assert all(key in dual_axis["grid"] for key in ("left", "right", "top", "bottom", "containLabel"))
    assert "bottom" in dual_axis["legend"]
    assert dual_axis["leftAxis"]["nameGap"] == 12
    assert dual_axis["rightAxis"]["nameGap"] == 12
    assert dual_axis["series"]["lineWidth"] == 2.2
    assert dual_axis["markPoint"]["label"]["fontSize"] == 9
    assert dual_axis["periodicChillerDualAxis"]["leftAxis"]["scale"]["targetTickCount"] == 4
    assert dual_axis["periodicChillerDualAxis"]["rightAxis"]["scale"]["maxDecimals"] == 1
    assert utility_chart_cfg["typeTrend"]["legend"]["bottom"] == "center"
    assert period_insight_heatmap["height"]["view"] == "252px"
    assert period_insight_mix["height"]["view"] == "276px"
    assert period_insight_mix["pie"]["radius"] == ["42%", "78%"]
    assert period_insight_mix["pie"]["sliceBorderRadius"] == 8
    assert energy_distribution["height"]["view"] == "276px"
    assert energy_distribution["legend"]["bottom"] == "center"
    assert energy_distribution["pie"]["center"] == ["50%", "45%"]
    assert deviation_value_label["nearZeroPositivePosition"] == "right"
    assert deviation_value_label["nearZeroNegativePosition"] == "left"
    assert deviation_value_label["nearZeroThreshold"] == 4
    assert deviation_value_label["nearZeroDistance"] == 10
