# -*- coding: utf-8 -*-
"""
Centralized data source configuration for V2.

Defines all logical datasets used in the reporting pipeline.

Example:
    sources = get_data_sources(database="bms_db")
    diode_source = sources["diode_energy"]
"""

from typing import Dict

from src.db.queries import DataSourceConfig


def get_data_sources(database: str) -> Dict[str, DataSourceConfig]:
    """Return all configured data sources.

    Args:
        database: MySQL database/schema name for the configured sources.

    Returns:
        Dict[str, DataSourceConfig]: Mapping of logical dataset names to configs.

    Example:
        sources = get_data_sources(database="bms_db")
        all_energy = sources["all_energy"]
    """
    return {
        "all_energy": DataSourceConfig(
            database=database,
            object_name="all_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "diode_energy": DataSourceConfig(
            database=database,
            object_name="diode_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "ico_energy": DataSourceConfig(
            database=database,
            object_name="ico_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "sakari_energy": DataSourceConfig(
            database=database,
            object_name="sakari_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "utility_usage": DataSourceConfig(
            database=database,
            object_name="utility_usage",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "total_energy": DataSourceConfig(
            database=database,
            object_name="total_energy",
            object_type="view",
            date_column="dt",
            excluded_columns=("dt",),
        ),
        "energy_kpi": DataSourceConfig(
            database=database,
            object_name="energy_kpi",
            object_type="table",
            date_column=None,
            excluded_columns=(),
        ),
        "workshop_timeline": DataSourceConfig(
            database=database,
            object_name="workshop_timeline",
            object_type="table",
            date_column="work_date",
            excluded_columns=(),
        ),
    }
