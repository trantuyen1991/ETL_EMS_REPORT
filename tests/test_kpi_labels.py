from __future__ import annotations

import json
from pathlib import Path

from src.services.report_builder_service import ReportBuilderService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_minimal_kpi_object() -> dict:
    return {
        "current": {
            "summary": {
                "plant": {"total_energy": 100.0, "total_prod": 10.0, "total_kpi": 10.0},
                "areas": {
                    "ico": {"energy": 30.0, "prod": 3.0, "kpi": 10.0},
                    "diode": {"energy": 40.0, "prod": 4.0, "kpi": 10.0},
                    "sakari": {"energy": 30.0, "prod": 3.0, "kpi": 10.0},
                },
            },
            "daily_rows": [],
            "coverage": {},
        },
        "previous": {
            "summary": {
                "plant": {"total_energy": 90.0, "total_prod": 9.0, "total_kpi": 10.0},
                "areas": {
                    "ico": {"energy": 27.0, "prod": 3.0, "kpi": 9.0},
                    "diode": {"energy": 36.0, "prod": 4.0, "kpi": 9.0},
                    "sakari": {"energy": 27.0, "prod": 3.0, "kpi": 9.0},
                },
            },
            "daily_rows": [],
        },
        "comparison": {
            "plant": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
            "areas": {
                "ico": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
                "diode": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
                "sakari": {"current": 10.0, "previous": 9.0, "delta": 1.0, "delta_pct": 1.0 / 9.0},
            },
        },
    }


def test_kpi_section_empty_summary_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    section = service._build_v3_kpi_section(None)

    assert section["summary_matrix"]["title"] == "KPI Summary Matrix"


def test_kpi_summary_matrix_empty_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    matrix = service._build_v3_kpi_summary_matrix(None)

    assert matrix["title"] == "KPI Summary Matrix"


def test_kpi_summary_matrix_populated_title_uses_neutral_wording() -> None:
    service = ReportBuilderService()

    matrix = service._build_v3_kpi_summary_matrix(_build_minimal_kpi_object(), period_type="weekly")

    assert matrix["title"] == "KPI Summary Matrix"


def _build_weekly_kpi_object() -> dict:
    return {
        "current": {
            "summary": {
                "plant": {"total_energy": 700.0, "total_prod": 70.0, "total_kpi": 10.0},
                "areas": {
                    "ico": {"energy": 210.0, "prod": 21.0, "kpi": 10.0},
                    "diode": {"energy": 280.0, "prod": 28.0, "kpi": 10.0},
                    "sakari": {"energy": 210.0, "prod": 21.0, "kpi": 10.0},
                },
            },
            "daily_rows": [
                {"dt": "2025-05-12", "kpi": 9.8, "ico_kpi": 9.5, "diode_kpi": 10.2, "sakari_kpi": 9.7},
                {"dt": "2025-05-13", "kpi": 10.1, "ico_kpi": 9.7, "diode_kpi": 10.4, "sakari_kpi": 10.0},
                {"dt": "2025-05-14", "kpi": 10.3, "ico_kpi": 9.9, "diode_kpi": 10.6, "sakari_kpi": 10.1},
            ],
            "coverage": {},
        },
        "previous": {
            "summary": {
                "plant": {"total_energy": 680.0, "total_prod": 70.0, "total_kpi": 9.7},
                "areas": {
                    "ico": {"energy": 204.0, "prod": 21.0, "kpi": 9.7},
                    "diode": {"energy": 272.0, "prod": 28.0, "kpi": 9.8},
                    "sakari": {"energy": 204.0, "prod": 21.0, "kpi": 9.6},
                },
            },
            "daily_rows": [],
        },
        "comparison": {
            "plant": {"current": 10.0, "previous": 9.7, "delta": 0.3, "delta_pct": 0.3 / 9.7},
            "areas": {
                "ico": {"current": 10.0, "previous": 9.7, "delta": 0.3, "delta_pct": 0.3 / 9.7},
                "diode": {"current": 10.0, "previous": 9.8, "delta": 0.2, "delta_pct": 0.2 / 9.8},
                "sakari": {"current": 10.0, "previous": 9.6, "delta": 0.4, "delta_pct": 0.4 / 9.6},
            },
        },
    }


def _build_zero_kpi_object() -> dict:
    return {
        "current": {
            "summary": {
                "plant": {"total_energy": 0.0, "total_prod": 0.0, "total_kpi": 0.0},
                "areas": {
                    "ico": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "diode": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "sakari": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                },
            },
            "daily_rows": [],
            "coverage": {},
        },
        "previous": {
            "summary": {
                "plant": {"total_energy": 0.0, "total_prod": 0.0, "total_kpi": 0.0},
                "areas": {
                    "ico": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "diode": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                    "sakari": {"energy": 0.0, "prod": 0.0, "kpi": 0.0},
                },
            },
            "daily_rows": [],
        },
        "comparison": {
            "plant": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
            "areas": {
                "ico": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
                "diode": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
                "sakari": {"current": 0.0, "previous": 0.0, "delta": 0.0, "delta_pct": None},
            },
        },
    }


def test_kpi_waterfall_option_uses_compact_daily_axis_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_kpi_waterfall_option(
        previous_kpi=10.0,
        energy_impact=0.0,
        production_impact=0.0,
        current_kpi=10.0,
    )

    assert option["xAxis"]["data"] == ["Yesterday", "Energy", "Prod.", "Today"]


def test_kpi_variance_option_hides_zero_value_labels() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    option = service._build_v3_kpi_variance_option(
        [
            {
                "name": "ICO",
                "value": 0.0,
                "current": 10.0,
                "previous": 10.0,
                "unit": "%",
            }
        ]
    )

    point = option["series"][0]["data"][0]

    assert point["label"]["show"] is False
    assert option["grid"]["left"] == 84
    assert option["grid"]["right"] == 18


def test_report_style_json_sets_kpi_variance_label_positions_like_utility() -> None:
    style_cfg = json.loads((PROJECT_ROOT / "config/report_style.json").read_text(encoding="utf-8"))
    variance_cfg = style_cfg["reportStyle"]["components"]["report"]["section"]["kpi"]["chart"]["variance"]

    assert variance_cfg["valueLabel"]["positivePosition"] == "left"
    assert variance_cfg["valueLabel"]["negativePosition"] == "right"
    assert variance_cfg["valueLabel"]["nearZeroPositivePosition"] == "right"
    assert variance_cfg["valueLabel"]["nearZeroNegativePosition"] == "left"
    assert variance_cfg["valueLabel"]["nearZeroThreshold"] == 4
    assert variance_cfg["valueLabel"]["nearZeroDistance"] == 12


def test_kpi_variance_option_uses_configured_axis_tokens() -> None:
    service = ReportBuilderService()
    service._render_mode = "view"
    service._style_config = {
        "components": {
            "report": {
                "section": {
                    "kpi": {
                        "chart": {
                            "variance": {
                                "xAxis": {
                                    "axisLabel": {
                                        "show": False,
                                        "fontSize": 12,
                                        "margin": 3,
                                    },
                                    "splitLine": {
                                        "show": False,
                                    },
                                },
                                "yAxis": {
                                    "axisLabel": {
                                        "fontSize": 13,
                                        "lineHeight": 15,
                                        "fontWeight": 500,
                                    }
                                },
                            }
                        }
                    }
                }
            }
        }
    }

    option = service._build_v3_kpi_variance_option(
        [
            {
                "name": "ICO",
                "value": 1.25,
                "current": 10.25,
                "previous": 10.12,
                "unit": "%",
            }
        ]
    )

    assert option["xAxis"]["axisLabel"]["show"] is False
    assert option["xAxis"]["axisLabel"]["fontSize"] == 12
    assert option["xAxis"]["axisLabel"]["margin"] == 3
    assert option["xAxis"]["splitLine"]["show"] is False
    assert option["yAxis"]["axisLabel"]["fontSize"] == 13
    assert option["yAxis"]["axisLabel"]["lineHeight"] == 15
    assert option["yAxis"]["axisLabel"]["fontWeight"] == 500


def test_kpi_variance_option_moves_near_zero_labels_away_from_center_and_uses_pdf_contrast_tokens() -> None:
    service = ReportBuilderService()
    service._render_mode = "pdf"
    service._style_config = {
        "components": {
            "report": {
                "section": {
                    "kpi": {
                        "chart": {
                            "variance": {
                                "valueLabel": {
                                    "positivePosition": "left",
                                    "negativePosition": "right",
                                    "nearZeroPositivePosition": "right",
                                    "nearZeroNegativePosition": "left",
                                    "nearZeroThreshold": 4,
                                    "nearZeroDistance": 12,
                                },
                                "pdf": {
                                    "xAxis": {
                                        "axisLabel": {"color": "#4b6074"},
                                        "splitLine": {"color": "#d6e0e9"},
                                    },
                                    "yAxis": {
                                        "axisLabel": {"color": "#223548"},
                                    },
                                },
                            }
                        }
                    }
                }
            }
        }
    }

    option = service._build_v3_kpi_variance_option(
        [
            {
                "name": "DIODE",
                "value": 3.35,
                "current": 10.335,
                "previous": 10.0,
                "unit": "%",
            },
            {
                "name": "Total",
                "value": -1.75,
                "current": 9.825,
                "previous": 10.0,
                "unit": "%",
            },
            {
                "name": "ICO",
                "value": -23.37,
                "current": 7.663,
                "previous": 10.0,
                "unit": "%",
            },
        ]
    )

    diode_point = option["series"][0]["data"][0]
    total_point = option["series"][0]["data"][1]
    ico_point = option["series"][0]["data"][2]

    assert diode_point["label"]["position"] == "right"
    assert diode_point["label"]["distance"] == 12
    assert total_point["label"]["position"] == "left"
    assert total_point["label"]["distance"] == 12
    assert ico_point["label"]["position"] == "right"
    assert option["xAxis"]["axisLabel"]["color"] == "#4b6074"
    assert option["xAxis"]["splitLine"]["lineStyle"]["color"] == "#d6e0e9"
    assert option["yAxis"]["axisLabel"]["color"] == "#223548"


def test_daily_kpi_charts_use_empty_state_messages_for_zero_only_data() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "pdf"

    dashboard = service._build_v3_kpi_daily_dashboard(
        _build_zero_kpi_object(),
        current_label="Today",
        previous_label="Yesterday",
    )

    assert dashboard["charts"]["compare_bar"]["empty_message"] == "No KPI values recorded for this day."
    assert dashboard["charts"]["waterfall"]["empty_message"] == "No KPI movement recorded for this day."
    assert dashboard["charts"]["variance"]["empty_message"] == "No KPI deviation detected for this day."


def test_daily_kpi_view_template_renders_empty_state_blocks() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/kpi.html").read_text(encoding="utf-8")

    assert "sections.kpi.charts.daily_dashboard.charts.compare_bar.empty_message" in view_template
    assert "sections.kpi.charts.daily_dashboard.charts.waterfall.empty_message" in view_template
    assert "sections.kpi.charts.daily_dashboard.charts.variance.empty_message" in view_template
    assert "kpi-daily-empty-state" in view_template


def test_daily_kpi_view_uses_empty_state_label_treatment() -> None:
    css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")

    assert '.kpi-daily-empty-state::before' in css
    assert 'LOW ACTIVITY DAY' in css


def test_weekly_kpi_dashboard_adds_period_trend_chart() -> None:
    service = ReportBuilderService()
    service._style_config = {}
    service._render_mode = "html"

    dashboard = service._build_v3_kpi_charts(_build_weekly_kpi_object(), period_type="weekly")["daily_dashboard"]
    period_trend = dashboard["charts"]["period_trend"]

    assert period_trend["title"] == "Energy KPI daily trend"
    assert period_trend["subtitle"] == "Daily KPI for this week by Total and workshop"
    assert period_trend["option"]["xAxis"]["data"][0] == "May 12 (Mon)"
    assert [series["name"] for series in period_trend["option"]["series"]] == ["Total", "DIODE", "ICO", "SAKARI"]
    assert period_trend["option"]["legend"]["left"] == "center"


def test_weekly_kpi_templates_promote_variance_beside_period_trend() -> None:
    view_template = (PROJECT_ROOT / "src/templates/report/view/sections/kpi.html").read_text(encoding="utf-8")
    pdf_template = (PROJECT_ROOT / "src/templates/report/pdf/sections/kpi.html").read_text(encoding="utf-8")

    assert "kpi-periodic-insight-grid" in view_template
    assert "kpi-period-trend-chart" in view_template
    assert "period.type == 'weekly'" in view_template
    assert "kpi-periodic-variance-chart" in view_template
    assert "kpi-periodic-insight-grid" in pdf_template
    assert "kpi-period-trend-chart" in pdf_template
    assert "kpi-periodic-variance-chart" in pdf_template


def test_weekly_kpi_css_and_config_define_periodic_trend_row() -> None:
    report_css = (PROJECT_ROOT / "src/templates/assets/report.css").read_text(encoding="utf-8")
    pdf_css = (PROJECT_ROOT / "src/templates/assets/report_pdf.css").read_text(encoding="utf-8")
    style_cfg = json.loads((PROJECT_ROOT / "config/report_style.json").read_text(encoding="utf-8"))
    kpi_chart_cfg = style_cfg["reportStyle"]["components"]["report"]["section"]["kpi"]["chart"]

    assert '.kpi-periodic-insight-grid {' in report_css
    assert 'grid-template-columns: minmax(0, 6fr) minmax(0, 4fr);' in report_css
    assert 'height: var(--report-components-report-section-kpi-chart-period-trend-height-view, 288px);' in report_css
    assert '.kpi-periodic-insight-grid {' in pdf_css
    assert 'grid-template-columns: minmax(0, 6fr) minmax(0, 4fr) !important;' in pdf_css
    assert 'height: var(--report-components-report-section-kpi-chart-period-variance-height-pdf, 196px) !important;' in pdf_css
    assert kpi_chart_cfg["periodTrend"]["legend"]["bottom"] == "center"
    assert kpi_chart_cfg["periodTrend"]["height"]["view"] == "288px"
    assert kpi_chart_cfg["variance"]["height"]["view"] == "288px"
