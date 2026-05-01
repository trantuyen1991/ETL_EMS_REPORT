from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_periodic_energy_object(current_start: date, previous_start: date) -> dict:
    current_rows = [
        {"date": current_start + timedelta(days=index), "total_energy_display": str(100 + (index * 10))}
        for index in range(3)
    ]
    previous_rows = [
        {"date": previous_start + timedelta(days=index), "total_energy_display": str(90 + (index * 10))}
        for index in range(3)
    ]

    return {
        "current": {
            "summary": {
                "diode": {"total_energy": 40.0},
                "ico": {"total_energy": 35.0},
                "sakari": {"total_energy": 25.0},
            },
            "daily_summary_rows": current_rows,
        },
        "previous": {
            "summary": {
                "diode": {"total_energy": 38.0},
                "ico": {"total_energy": 30.0},
                "sakari": {"total_energy": 22.0},
            },
            "daily_summary_rows": previous_rows,
        },
    }


def test_daily_electric_area_comparison_chart_uses_today_yesterday_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    charts = service._build_v3_electricity_charts(
        energy_object={
            "current": {
                "summary": {
                    "diode": {"total_energy": 10.0},
                    "ico": {"total_energy": 20.0},
                    "sakari": {"total_energy": 30.0},
                },
                "daily_summary_rows": [{"date": date(2025, 6, 25), "total_energy_display": "60.0"}],
            },
            "previous": {
                "summary": {
                    "diode": {"total_energy": 8.0},
                    "ico": {"total_energy": 18.0},
                    "sakari": {"total_energy": 28.0},
                },
                "daily_summary_rows": [{"date": date(2025, 6, 24), "total_energy_display": "54.0"}],
            },
        },
        period_type="daily",
    )

    area_chart = charts["area_comparison"]

    assert area_chart["subtitle"] == "Today vs yesterday total by workshop"
    assert area_chart["option"]["series"][0]["name"] == "Today"
    assert area_chart["option"]["series"][1]["name"] == "Yesterday"


def test_periodic_electric_charts_use_period_aware_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    weekly_charts = service._build_v3_electricity_charts(
        energy_object=_build_periodic_energy_object(date(2025, 4, 14), date(2025, 4, 7)),
        period_type="weekly",
    )
    monthly_charts = service._build_v3_electricity_charts(
        energy_object=_build_periodic_energy_object(date(2025, 5, 1), date(2025, 4, 1)),
        period_type="monthly",
    )

    assert weekly_charts["daily_trend"]["subtitle"] == "This Week vs last week"
    assert weekly_charts["daily_trend"]["option"]["series"][0]["name"] == "This Week"
    assert weekly_charts["daily_trend"]["option"]["series"][1]["name"] == "Last Week"
    assert weekly_charts["area_comparison"]["subtitle"] == "This Week vs last week total by workshop"
    assert weekly_charts["area_comparison"]["option"]["series"][0]["name"] == "This Week"
    assert weekly_charts["area_comparison"]["option"]["series"][1]["name"] == "Last Week"

    assert monthly_charts["daily_trend"]["subtitle"] == "This Month vs last month"
    assert monthly_charts["daily_trend"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["daily_trend"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["area_comparison"]["subtitle"] == "This Month vs last month total by workshop"
    assert monthly_charts["area_comparison"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["area_comparison"]["option"]["series"][1]["name"] == "Last Month"


def test_period_block_uses_last_week_and_last_month_labels() -> None:
    service = ReportBuilderService()

    weekly_block = service._build_v3_period_block(period={"type": "weekly"})
    monthly_block = service._build_v3_period_block(period={"type": "monthly"})

    assert weekly_block["labels"]["current_period"] == "This Week"
    assert weekly_block["labels"]["previous_period"] == "Last Week"
    assert monthly_block["labels"]["current_period"] == "This Month"
    assert monthly_block["labels"]["previous_period"] == "Last Month"


def test_electric_templates_use_period_aware_wording_for_top10_note_and_headers() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/electricity.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/electricity.html").read_text(encoding="utf-8")

    expected_note = 'Top 10 meters are sorted by {{ labels.current_period | lower }} consumption.'
    expected_header = '<th>{{ labels.current_period }}</th>'

    assert expected_note in view_template
    assert expected_note in pdf_template
    assert expected_header in view_template
    assert expected_header in pdf_template
    assert 'if flags.is_daily_report else "Current"' not in view_template
    assert 'if flags.is_daily_report else "Current"' not in pdf_template
    assert 'if flags.is_daily_report else "current-period"' not in view_template
    assert 'if flags.is_daily_report else "current-period"' not in pdf_template
