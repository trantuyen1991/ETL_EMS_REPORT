# -*- coding: utf-8 -*-
"""
Repository adapter for period-aware report services.

This module adapts the existing EnergyDataRepository to the new
ResolvedPeriod-based contract used by V2 services.

Args:
    None

Returns:
    None

Example:
    base_repo = EnergyDataRepository(client, source_config)
    repo = MySqlEnergyReportRepository(base_repo)
"""

from __future__ import annotations

from typing import Optional

from src.db.queries import EnergyDataRepository
from src.models.period_models import ResolvedPeriod


class MySqlEnergyReportRepository:
    """Adapter over EnergyDataRepository using ResolvedPeriod."""

    def __init__(self, repository: EnergyDataRepository) -> None:
        """Initialize repository adapter.

        Args:
            repository: Existing energy data repository instance.

        Returns:
            None

        Example:
            repo = MySqlEnergyReportRepository(base_repo)
        """
        self._repository = repository

    def get_meter_columns(self) -> list[str]:
        """Return all valid meter columns.

        Args:
            None

        Returns:
            list[str]: Meter column names.

        Example:
            columns = repo.get_meter_columns()
        """
        return self._repository.get_meter_columns()

    def get_available_date_range(self) -> dict[str, object]:
        """Return available source date range information.

        Args:
            None

        Returns:
            dict[str, object]: Source min/max dates and row count.

        Example:
            info = repo.get_available_date_range()
        """
        return self._repository.get_available_date_range()

    def count_rows(self, period: ResolvedPeriod) -> int:
        """Return row count for the given period.

        Args:
            period: Canonical resolved report period.

        Returns:
            int: Row count for the period.

        Example:
            total = repo.count_rows(period)
        """
        return self._repository.count_rows_in_range(
            period.start_date,
            period.end_date,
        )

    def fetch_daily_rows(
        self,
        period: ResolvedPeriod,
        selected_columns: Optional[list[str]] = None,
    ) -> list[dict[str, object]]:
        """Return daily detail rows for the given period.

        Args:
            period: Canonical resolved report period.
            selected_columns: Optional subset of meter columns.

        Returns:
            list[dict[str, object]]: Daily detail rows.

        Example:
            rows = repo.fetch_daily_rows(period)
        """
        return self._repository.get_daily_detail_rows(
            start_date=period.start_date,
            end_date=period.end_date,
            selected_columns=selected_columns,
        )

    def fetch_meter_totals(
        self,
        period: ResolvedPeriod,
        selected_columns: Optional[list[str]] = None,
        sort_desc: bool = True,
    ) -> list[dict[str, object]]:
        """Return total value per meter for the given period.

        Args:
            period: Canonical resolved report period.
            selected_columns: Optional subset of meter columns.
            sort_desc: Whether to sort totals in descending order.

        Returns:
            list[dict[str, object]]: Meter totals.

        Example:
            totals = repo.fetch_meter_totals(period)
        """
        return self._repository.get_meter_totals(
            start_date=period.start_date,
            end_date=period.end_date,
            selected_columns=selected_columns,
            sort_desc=sort_desc,
        )

    def fetch_top_n_meters(
        self,
        period: ResolvedPeriod,
        top_n: int = 10,
        selected_columns: Optional[list[str]] = None,
    ) -> list[dict[str, object]]:
        """Return top-N meters for the given period.

        Args:
            period: Canonical resolved report period.
            top_n: Number of top meters to return.
            selected_columns: Optional subset of meter columns.

        Returns:
            list[dict[str, object]]: Top-N meter totals.

        Example:
            top = repo.fetch_top_n_meters(period, top_n=10)
        """
        return self._repository.get_top_n_meters(
            start_date=period.start_date,
            end_date=period.end_date,
            top_n=top_n,
            selected_columns=selected_columns,
        )