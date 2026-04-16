# -*- coding: utf-8 -*-
"""
Utility service for aggregating utility usage data for reporting.

This module prepares utility data from the utility_usage source.

Important:
- Utility columns may have different physical units
- The service does not compute one grand total across different utilities
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from src.config.utility_metadata import get_utility_metadata
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UtilityService:
    """Service for utility usage aggregation."""

    def build_utility_report_object(
        self,
        rows: List[Dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> Dict[str, Any]:
        """Build full utility object for report usage.

        Args:
            rows: Raw rows fetched from utility source.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            dict: Utility report object with metadata, summary, and timeseries.

        Example:
            result = service.build_utility_report_object(rows, start, end)
        """
        filtered_rows = self._filter_rows_in_period(rows, report_start, report_end)
        metadata = get_utility_metadata()
        utility_columns = list(metadata.keys())

        timeseries = self._build_timeseries(
            rows=filtered_rows,
            utility_columns=utility_columns,
        )

        summary = self._build_summary(
            timeseries=timeseries,
            metadata=metadata,
        )

        return {
            "metadata": metadata,
            "summary": summary,
            "timeseries": timeseries,
        }

    def _filter_rows_in_period(
        self,
        rows: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        """Filter rows within report period."""
        result: List[Dict[str, Any]] = []

        for row in rows:
            dt = self._to_date(row.get("dt"))
            if dt is not None and start <= dt <= end:
                result.append(row)

        return result

    def _build_timeseries(
        self,
        rows: List[Dict[str, Any]],
        utility_columns: List[str],
    ) -> List[Dict[str, Any]]:
        """Build daily timeseries preserving each utility column."""
        timeseries: List[Dict[str, Any]] = []

        for row in sorted(rows, key=lambda item: self._to_date(item.get("dt"))):
            dt = self._to_date(row.get("dt"))
            if dt is None:
                continue

            timeseries_row: Dict[str, Any] = {"dt": dt}

            for column in utility_columns:
                timeseries_row[column] = self._safe_number(row.get(column))

            timeseries.append(timeseries_row)

        return timeseries

    def _build_summary(
        self,
        timeseries: List[Dict[str, Any]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Build per-utility summary for the report period."""
        summary: Dict[str, Dict[str, Any]] = {}

        for column, column_meta in metadata.items():
            total = 0.0

            for row in timeseries:
                total += self._safe_number(row.get(column))

            summary[column] = {
                "display_name": column_meta["display_name"],
                "category": column_meta["category"],
                "unit": column_meta["unit"],
                "description": column_meta["description"],
                "total": round(total, 4),
            }

        return summary

    def _to_date(self, value: Any) -> date | None:
        """Convert a date/datetime-like value to a date."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    def _safe_number(self, value: Any) -> float:
        """Convert input value to float safely."""
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except Exception:
            return 0.0