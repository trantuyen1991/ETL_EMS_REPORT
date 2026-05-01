from __future__ import annotations

from datetime import date
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def test_daily_electric_templates_use_today_wording_for_top10_note() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/electricity.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/electricity.html").read_text(encoding="utf-8")

    expected_note = 'Top 10 meters are sorted by {{ "today" if flags.is_daily_report else "current-period" }} consumption.'

    assert expected_note in view_template
    assert expected_note in pdf_template
