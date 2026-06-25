from __future__ import annotations

from datetime import date

from src.services.energy_service import EnergyService


def test_total_energy_daily_lookup_uses_total_engy_as_plant_total() -> None:
    service = EnergyService()

    lookup = service._build_total_energy_daily_lookup_from_rows(
        total_energy_rows=[
            {
                "dt": date(2026, 6, 1),
                "Total_engy": 10390.0,
                "DIODE_engy": 6766.0,
                "ICO_engy": 3624.0,
                "SAKARI_engy": 1144.0,
            }
        ],
        report_start=date(2026, 6, 1),
        report_end=date(2026, 6, 1),
    )

    assert lookup[date(2026, 6, 1)]["plant_total_energy"] == 10390.0
    assert lookup[date(2026, 6, 1)]["diode"] == 6766.0
    assert lookup[date(2026, 6, 1)]["ico"] == 3624.0
    assert lookup[date(2026, 6, 1)]["sakari"] == 1144.0


def test_total_energy_period_summary_uses_total_engy_as_plant_total() -> None:
    service = EnergyService()

    summary = service._build_total_energy_period_summary_from_rows(
        total_energy_rows=[
            {
                "dt": date(2026, 6, 1),
                "Total_engy": 10390.0,
                "DIODE_engy": 6766.0,
                "ICO_engy": 3624.0,
                "SAKARI_engy": 1144.0,
            },
            {
                "dt": date(2026, 6, 2),
                "Total_engy": 9000.0,
                "DIODE_engy": 6000.0,
                "ICO_engy": 3000.0,
                "SAKARI_engy": 1000.0,
            },
        ]
    )

    assert summary["plant"]["total_energy"] == 19390.0
    assert summary["areas"]["diode"]["energy"] == 12766.0
    assert summary["areas"]["ico"]["energy"] == 6624.0
    assert summary["areas"]["sakari"]["energy"] == 2144.0
