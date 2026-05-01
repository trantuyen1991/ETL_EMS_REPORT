from __future__ import annotations

from src.services.report_builder_service import ReportBuilderService


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
