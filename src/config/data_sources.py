# -*- coding: utf-8 -*-
"""
Centralized data source configuration for V2.

Defines all logical datasets used in the reporting pipeline.

Example:
    sources = get_data_sources()
    diode_source = sources["diode_energy"]
"""

from typing import Dict

from src.db.queries import DataSourceConfig


def get_data_sources() -> Dict[str, DataSourceConfig]:
    """Return all configured data sources.

    Args:
        None

    Returns:
        Dict[str, DataSourceConfig]: Mapping of logical dataset names to configs.

    Example:
        sources = get_data_sources()
        all_energy = sources["all_energy"]
    """
    return {
        "all_energy": DataSourceConfig(
            database="ems_db",
            object_name="all_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "diode_energy": DataSourceConfig(
            database="ems_db",
            object_name="diode_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "ico_energy": DataSourceConfig(
            database="ems_db",
            object_name="ico_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "sakari_energy": DataSourceConfig(
            database="ems_db",
            object_name="sakari_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "utility_usage": DataSourceConfig(
            database="ems_db",
            object_name="utility_usage",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "energy_kpi": DataSourceConfig(
            database="ems_db",
            object_name="energy_kpi",
            object_type="table",
            date_column=None,
            excluded_columns=(),
        ),
    }