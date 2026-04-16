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

from typing import Dict, Any


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
            "unit": None,
            "description": "Domestic water usage",
        },
        "IcochilledWater": {
            "display_name": "ICO Chilled Water",
            "category": "chilled_water",
            "unit": None,
            "description": "Chilled water usage for ICO area",
        },
        "DiodechilledWater": {
            "display_name": "Diode Chilled Water",
            "category": "chilled_water",
            "unit": None,
            "description": "Chilled water usage for Diode area",
        },
        "IcoAir": {
            "display_name": "ICO Air",
            "category": "compressed_air",
            "unit": None,
            "description": "Compressed air usage for ICO area",
        },
        "DiodeAir": {
            "display_name": "Diode Air",
            "category": "compressed_air",
            "unit": None,
            "description": "Compressed air usage for Diode area",
        },
        "Steam": {
            "display_name": "Steam",
            "category": "steam",
            "unit": None,
            "description": "Steam usage",
        },
        "SakariWater": {
            "display_name": "Sakari Water",
            "category": "water",
            "unit": None,
            "description": "Water usage for Sakari area",
        },
    }