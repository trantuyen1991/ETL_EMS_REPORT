from __future__ import annotations

from src.services.kpi_service import KPIService


def test_kpi_summary_calculates_period_ratio_from_selected_energy_and_production() -> None:
    service = KPIService()

    summary = service.build_kpi_summary(
        selected_rows=[
            {
                "Total_prod": 10.0,
                "Total_engy": 100.0,
                "Total_kpi": 10.0,
                "ICO_prod": 5.0,
                "ICO_engy": 50.0,
                "ICO_kpi": 10.0,
                "DIODE_prod": 5.0,
                "DIODE_engy": 100.0,
                "DIODE_kpi": 20.0,
                "SAKARI_prod": 0.0,
                "SAKARI_engy": 0.0,
                "SAKARI_kpi": 0.0,
            },
            {
                "Total_prod": 10.0,
                "Total_engy": 300.0,
                "Total_kpi": 30.0,
                "ICO_prod": 5.0,
                "ICO_engy": 150.0,
                "ICO_kpi": 30.0,
                "DIODE_prod": 5.0,
                "DIODE_engy": 150.0,
                "DIODE_kpi": 30.0,
                "SAKARI_prod": 0.0,
                "SAKARI_engy": 0.0,
                "SAKARI_kpi": 0.0,
            },
        ],
        coverage_days=2,
        report_total_days=2,
        is_full_coverage=True,
        uncovered_ranges=[],
        coverage_note="full",
        messages=[],
    )

    assert summary["plant"]["total_energy"] == 400.0
    assert summary["plant"]["total_prod"] == 20.0
    assert summary["plant"]["total_kpi"] == 20.0
    assert summary["areas"]["ico"]["kpi"] == 20.0
    assert summary["areas"]["diode"]["kpi"] == 25.0
    assert summary["areas"]["sakari"]["kpi"] is None
