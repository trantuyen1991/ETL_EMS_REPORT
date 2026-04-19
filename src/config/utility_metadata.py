# -*- coding: utf-8 -*-
"""
Utility metadata configuration.

This module defines display metadata for each utility column used in the
utility_usage source.

Important:
- Utility columns may have different physical units
- They must not be summed into one grand total unless explicitly converted
  into a common unit outside this layer
"""

from typing import Any, Dict, List

def get_utility_metadata() -> Dict[str, Dict[str, Any]]:
    """Return metadata for utility columns.

    Returns:
        Dict[str, Dict[str, Any]]: Utility metadata by column name.

    Example:
        metadata = get_utility_metadata()
        dom_water = metadata["DomWater"]
    """
    return {
        "DomWater": {
            "display_name": "Domestic Water",
            "category": "water",
            "unit": "m³",
            "description": "Domestic water usage",
        },
        "IcochilledWater": {
            "display_name": "ICO Chilled Water",
            "category": "chilled_water",
            "unit": "m³",
            "description": "Chilled water usage for ICO area",
        },
        "DiodechilledWater": {
            "display_name": "Diode Chilled Water",
            "category": "chilled_water",
            "unit": "m³",
            "description": "Chilled water usage for Diode area",
        },
        "IcoAir": {
            "display_name": "ICO Air",
            "category": "compressed_air",
            "unit": "m³",
            "description": "Compressed air usage for ICO area",
        },
        "DiodeAir": {
            "display_name": "Diode Air",
            "category": "compressed_air",
            "unit": "m³",
            "description": "Compressed air usage for Diode area",
        },
        "Steam": {
            "display_name": "Steam",
            "category": "steam",
            "unit": "m³",
            "description": "Steam usage",
        },
        "SakariWater": {
            "display_name": "Sakari Water",
            "category": "water",
            "unit": "m³",
            "description": "Water usage for Sakari area",
        },
    }

UTILITY_SENSOR_GROUP_ORDER: List[str] = [
    "ico_chiller",
    "diode_chiller",
    "ico_air",
    "diode_air",
    "boiler",
    "domestic_water",
]


UTILITY_SENSOR_GROUP_LABELS: Dict[str, str] = {
    "ico_chiller": "ICO Chiller",
    "diode_chiller": "DIODE Chiller",
    "ico_air": "ICO Air",
    "diode_air": "DIODE Air",
    "boiler": "Boiler",
    "domestic_water": "Domestic Water",
}


UTILITY_SENSOR_METADATA: Dict[str, Dict[str, Any]] = {
    "ich_rettemp": {
        "display_name": "ICO Chiller Return Temp",
        "unit": "°C",
        "group": "ico_chiller",
        "description": "Return water temperature of ICO chiller.",
        "source_column": "ich_rettemp",
        "stats": ["min", "avg", "max"],
    },
    "ich_suptemp": {
        "display_name": "ICO Chiller Supply Temp",
        "unit": "°C",
        "group": "ico_chiller",
        "description": "Supply water temperature of ICO chiller.",
        "source_column": "ich_suptemp",
        "stats": ["min", "avg", "max"],
    },
    "ich_supflow": {
        "display_name": "ICO Chiller Supply Flow",
        "unit": "kg/h",
        "group": "ico_chiller",
        "description": "Supply water flow of ICO chiller.",
        "source_column": "ich_supflow",
        "stats": ["min", "avg", "max"],
    },
    "ich_suppress": {
        "display_name": "ICO Chiller Supply Pressure",
        "unit": "bar",
        "group": "ico_chiller",
        "description": "Supply water pressure of ICO chiller.",
        "source_column": "ich_suppress",
        "stats": ["min", "avg", "max"],
    },

    "dch_rettemp": {
        "display_name": "DIODE Chiller Return Temp",
        "unit": "°C",
        "group": "diode_chiller",
        "description": "Return water temperature of DIODE chiller.",
        "source_column": "dch_rettemp",
        "stats": ["min", "avg", "max"],
    },
    "dch_suptemp": {
        "display_name": "DIODE Chiller Supply Temp",
        "unit": "°C",
        "group": "diode_chiller",
        "description": "Supply water temperature of DIODE chiller.",
        "source_column": "dch_suptemp",
        "stats": ["min", "avg", "max"],
    },
    "dch_supflow": {
        "display_name": "DIODE Chiller Supply Flow",
        "unit": "kg/h",
        "group": "diode_chiller",
        "description": "Supply water flow of DIODE chiller.",
        "source_column": "dch_supflow",
        "stats": ["min", "avg", "max"],
    },
    "dch_suppress": {
        "display_name": "DIODE Chiller Supply Pressure",
        "unit": "bar",
        "group": "diode_chiller",
        "description": "Supply water pressure of DIODE chiller.",
        "source_column": "dch_suppress",
        "stats": ["min", "avg", "max"],
    },

    "iac_press": {
        "display_name": "ICO Air Pressure",
        "unit": "bar",
        "group": "ico_air",
        "description": "Compressed air pressure in ICO area.",
        "source_column": "iac_press",
        "stats": ["min", "avg", "max"],
    },
    "iac_airflow": {
        "display_name": "ICO Air Flow",
        "unit": "m³/h",
        "group": "ico_air",
        "description": "Compressed air flow in ICO area.",
        "source_column": "iac_airflow",
        "stats": ["min", "avg", "max"],
    },

    "dac_press": {
        "display_name": "DIODE Air Pressure",
        "unit": "bar",
        "group": "diode_air",
        "description": "Compressed air pressure in DIODE area.",
        "source_column": "dac_press",
        "stats": ["min", "avg", "max"],
    },
    "dac_airflow": {
        "display_name": "DIODE Air Flow",
        "unit": "m³/h",
        "group": "diode_air",
        "description": "Compressed air flow in DIODE area.",
        "source_column": "dac_airflow",
        "stats": ["min", "avg", "max"],
    },

    "boi_steamflow": {
        "display_name": "Boiler Steam Flow",
        "unit": "m³/h",
        "group": "boiler",
        "description": "Steam flow of boiler system.",
        "source_column": "boi_steamflow",
        "stats": ["min", "avg", "max"],
    },
    "boi_steampress": {
        "display_name": "Boiler Steam Pressure",
        "unit": "bar",
        "group": "boiler",
        "description": "Steam pressure of boiler system.",
        "source_column": "boi_steampress",
        "stats": ["min", "avg", "max"],
    },

    "dom_waterflow": {
        "display_name": "Domestic Water Flow",
        "unit": "m³/h",
        "group": "domestic_water",
        "description": "Domestic water flow.",
        "source_column": "dom_waterflow",
        "stats": ["min", "avg", "max"],
    },
}


def get_utility_sensor_metadata() -> Dict[str, Dict[str, Any]]:
    """Return utility sensor metadata configuration.

    Returns:
        Dict[str, Dict[str, Any]]: Utility sensor metadata indexed by sensor key.
    """
    return UTILITY_SENSOR_METADATA


def get_utility_sensor_group_order() -> List[str]:
    """Return utility sensor group display order.

    Returns:
        List[str]: Ordered utility sensor group keys.
    """
    return UTILITY_SENSOR_GROUP_ORDER


def get_utility_sensor_group_labels() -> Dict[str, str]:
    """Return display labels for utility sensor groups.

    Returns:
        Dict[str, str]: Group label mapping.
    """
    return UTILITY_SENSOR_GROUP_LABELS