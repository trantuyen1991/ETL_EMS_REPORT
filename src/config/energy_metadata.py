# -*- coding: utf-8 -*-
"""
Energy metadata configuration for electricity business rules.

This module defines:
- main feeder mapping by area
- top10 exclusion rules
- official KPI energy source keys
- unknown load display settings

Important:
- Official total energy must come from KPI summary, not from summing all meters
- Feeder totals are used for cross-check and analysis
- Unknown load is treated as a normal analysis meter in daily detail and top10
"""

from __future__ import annotations

from typing import Any, Dict


def get_energy_area_metadata() -> Dict[str, Dict[str, Any]]:
    """Return electricity metadata by area.

    Returns:
        Dict[str, Dict[str, Any]]: Area-level electricity business metadata.

    Example:
        metadata = get_energy_area_metadata()
        diode_meta = metadata["diode"]
    """
    return {
        "diode": {
            "display_name": "DIODE",
            "main_feeders": ["MSB1", "MSB2"],
            "exclude_from_top10": ["MSB1", "MSB2"],
            "official_kpi_energy_key": "DIODE_engy",
            "unknown_load_key": "unknown_load",
            "unknown_load_display_name": "Unknown Load",
        },
        "ico": {
            "display_name": "ICO",
            "main_feeders": ["MSB1", "MSB2"],
            "exclude_from_top10": ["MSB1", "MSB2", "DBADH"],
            "official_kpi_energy_key": "ICO_engy",
            "unknown_load_key": "unknown_load",
            "unknown_load_display_name": "Unknown Load",
        },
        "sakari": {
            "display_name": "SAKARI",
            "main_feeders": ["DBADH"],
            "exclude_from_top10": ["DBADH"],
            "official_kpi_energy_key": "SAKARI_engy",
            "unknown_load_key": "unknown_load",
            "unknown_load_display_name": "Unknown Load",
        },
    }


def get_energy_plant_metadata() -> Dict[str, Any]:
    """Return plant-level electricity metadata.

    Returns:
        Dict[str, Any]: Plant-level electricity business metadata.

    Example:
        metadata = get_energy_plant_metadata()
        total_key = metadata["official_kpi_energy_key"]
    """
    return {
        "official_kpi_energy_key": "Total_engy",
    }