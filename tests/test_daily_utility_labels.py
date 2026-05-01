from __future__ import annotations

from src.services.report_builder_service import ReportBuilderService


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
