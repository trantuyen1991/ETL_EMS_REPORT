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

    current_daily_tables = [
        {
            "area_key": "diode",
            "rows": [
                {"meter_name": "D1", "total_energy_display": "25"},
                {"meter_name": "D2", "total_energy_display": "15"},
            ],
        },
        {
            "area_key": "ico",
            "rows": [
                {"meter_name": "I1", "total_energy_display": "20"},
                {"meter_name": "I2", "total_energy_display": "15"},
            ],
        },
        {
            "area_key": "sakari",
            "rows": [
                {"meter_name": "S1", "total_energy_display": "14"},
                {"meter_name": "S2", "total_energy_display": "11"},
            ],
        },
    ]
    previous_daily_tables = [
        {
            "area_key": "diode",
            "rows": [
                {"meter_name": "D1", "total_energy_display": "22"},
                {"meter_name": "D2", "total_energy_display": "16"},
            ],
        },
        {
            "area_key": "ico",
            "rows": [
                {"meter_name": "I1", "total_energy_display": "18"},
                {"meter_name": "I2", "total_energy_display": "12"},
            ],
        },
        {
            "area_key": "sakari",
            "rows": [
                {"meter_name": "S1", "total_energy_display": "12"},
                {"meter_name": "S2", "total_energy_display": "10"},
            ],
        },
    ]

    return {
        "current": {
            "summary": {
                "diode": {"total_energy": 40.0},
                "ico": {"total_energy": 35.0},
                "sakari": {"total_energy": 25.0},
                "plant": {"total_energy": 100.0},
            },
            "daily_summary_rows": current_rows,
            "daily_tables": current_daily_tables,
        },
        "previous": {
            "summary": {
                "diode": {"total_energy": 38.0},
                "ico": {"total_energy": 30.0},
                "sakari": {"total_energy": 22.0},
                "plant": {"total_energy": 90.0},
            },
            "daily_summary_rows": previous_rows,
            "daily_tables": previous_daily_tables,
        },
        "comparison": {
            "summary": {
                "diode": {"current": 40.0, "previous": 38.0, "delta": 2.0, "delta_pct": 2.0 / 38.0, "meter_count": 2},
                "ico": {"current": 35.0, "previous": 30.0, "delta": 5.0, "delta_pct": 5.0 / 30.0, "meter_count": 2},
                "sakari": {"current": 25.0, "previous": 22.0, "delta": 3.0, "delta_pct": 3.0 / 22.0, "meter_count": 2},
            },
            "top10_meters": [],
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
    assert weekly_charts["period_area_delta"]["subtitle"] == "This Week vs last week change by total and workshop"

    assert monthly_charts["daily_trend"]["subtitle"] == "This Month vs last month"
    assert monthly_charts["daily_trend"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["daily_trend"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["area_comparison"]["subtitle"] == "This Month vs last month total by workshop"
    assert monthly_charts["area_comparison"]["option"]["series"][0]["name"] == "This Month"
    assert monthly_charts["area_comparison"]["option"]["series"][1]["name"] == "Last Month"
    assert monthly_charts["period_area_delta"]["subtitle"] == "This Month vs last month change by total and workshop"


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


def test_daily_pdf_electric_template_skips_empty_top10_block() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/electricity.html").read_text(encoding="utf-8")

    assert '{% if sections.electricity.top10.grouped_rows %}' in pdf_template


def test_daily_view_electric_template_marks_area_chart_for_compact_layout() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/electricity.html").read_text(encoding="utf-8")

    assert 'electricity-chart-card-area-compact' in view_template


def test_weekly_pdf_electric_detail_highlight_disables_border_artifact() -> None:
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert '.electricity-periodic-detail-table .value-max' in pdf_css
    assert 'border-bottom: none !important;' in pdf_css


def test_weekly_pdf_electric_detail_template_has_meter_colgroup() -> None:
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/electricity.html").read_text(encoding="utf-8")

    assert '<col class="col-meter">' in pdf_template
    assert '<th class="col-meter">{{ column.display_name }}</th>' in pdf_template
    assert '<td class="col-meter col-value {{ cell.cell_class }} {{ cell.heat_class }} {% if cell.is_row_max %}value-max{% endif %}">' in pdf_template


def test_weekly_pdf_electric_detail_uses_daily_like_palette_and_tighter_date_width() -> None:
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")

    assert '.electricity-periodic-detail-table .col-date' in pdf_css
    assert 'width: 82px !important;' in pdf_css
    assert '.electricity-periodic-detail-table .col-value' in pdf_css
    assert 'color: var(--report-color-text-primary, #0f172a) !important;' in pdf_css
    assert '.electricity-periodic-detail-table .heat-4' in pdf_css
    assert 'background: linear-gradient(90deg, var(--detail-strong-bg, #deecff) 0%, rgba(255, 255, 255, 0.98) 74%) !important;' in pdf_css
    assert '.electricity-periodic-detail-table .col-value.value-max' in pdf_css
    assert 'background: linear-gradient(90deg, var(--detail-strong-bg, #deecff) 0%, rgba(255, 255, 255, 0.94) 58%) !important;' in pdf_css
    assert 'color: var(--detail-accent-color, #1d4ed8) !important;' in pdf_css


def test_periodic_electric_area_top10_subtitles_use_period_aware_wording() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    weekly_section = service._build_v3_electricity_section(
        energy_object=_build_periodic_energy_object(date(2025, 4, 14), date(2025, 4, 7)),
        period_type="weekly",
    )
    monthly_section = service._build_v3_electricity_section(
        energy_object=_build_periodic_energy_object(date(2025, 5, 1), date(2025, 4, 1)),
        period_type="monthly",
    )

    weekly_subtitles = [table["subtitle"] for table in weekly_section["top10"]["area_tables"]]
    monthly_subtitles = [table["subtitle"] for table in monthly_section["top10"]["area_tables"]]

    assert weekly_subtitles == [
        "Sorted by this week consumption within this area.",
        "Sorted by this week consumption within this area.",
        "Sorted by this week consumption within this area.",
    ]
    assert monthly_subtitles == [
        "Sorted by this month consumption within this area.",
        "Sorted by this month consumption within this area.",
        "Sorted by this month consumption within this area.",
    ]
