from __future__ import annotations

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
    }


def test_daily_utility_trend_subtitle_uses_today_wording() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    charts = service._build_v3_utility_charts(
        utility_object={
            "current": {
                "metadata": {
                    "water": {"display_name": "RO Water", "unit": "m³"},
                }
            },
            "comparison": {
                "water": {"current": 120.0, "previous": 100.0},
            },
        },
        period={"type": "daily"},
    )

    assert charts["period_type_trend"]["subtitle"] == "Today total by utility group"


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
    assert weekly_charts["deviation_vs_yesterday"]["subtitle"] == "This Week versus last week"
    assert weekly_charts["period_type_trend"]["subtitle"] == "Daily totals for this week by utility group"
    assert weekly_charts["period_mix"]["title"] == "This Week mix"

    assert monthly_charts["comparison_bar"]["subtitle"] == "This Month vs last month total by load type"
    assert monthly_charts["comparison_bar"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["comparison_bar"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["comparison_split"]["wide"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["comparison_split"]["wide"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["deviation_vs_yesterday"]["subtitle"] == "This Month versus last month"
    assert monthly_charts["period_type_trend"]["subtitle"] == "Daily totals for this month by utility group"
    assert monthly_charts["period_mix"]["title"] == "This Month mix"


def test_utility_templates_use_last_period_fallback_copy() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/utility.html").read_text(encoding="utf-8")

    expected_note = 'labels.previous_period | lower if labels.previous_period else "last period"'

    assert expected_note in view_template
    assert expected_note in pdf_template
    assert 'previous period' not in view_template
    assert 'previous period' not in pdf_template


def test_daily_view_utility_template_marks_comparison_cards_for_compact_layout() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/utility.html").read_text(encoding="utf-8")

    assert 'utility-chart-card-compare-compact' in view_template


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
        period_badge="This Week",
    )

    series = option["series"][0]

    assert series["radius"] == ["48%", "72%"]
    assert series["center"] == ["42%", "54%"]
    assert series["label"]["fontSize"] == 7
