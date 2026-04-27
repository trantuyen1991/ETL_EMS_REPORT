"""Service for aggregating raw processvalue sensor rows."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import logging


logger = logging.getLogger(__name__)


class ProcessValueService:
    """Aggregate raw processvalue sensor rows into daily statistics.

    This service is responsible for transforming raw timestamped rows from
    processvalue into daily min/avg/max statistics per sensor.

    Example:
        service = ProcessValueService()
        stats = service.aggregate_daily_sensor_stats(
            rows=raw_rows,
            sensor_columns=["ich_rettemp", "ich_suptemp"],
        )
    """

    def aggregate_daily_sensor_stats(
        self,
        rows: List[Dict[str, Any]],
        sensor_columns: List[str],
    ) -> Dict[date, Dict[str, Dict[str, Optional[float]]]]:
        """Aggregate raw sensor rows into daily min/avg/max values.

        Args:
            rows: Raw processvalue rows in the shape:
                [
                    {
                        "dt": datetime(...),
                        "<sensor_column>": value,
                        ...
                    }
                ]
            sensor_columns: Sensor columns to aggregate.

        Returns:
            Dict[date, Dict[str, Dict[str, Optional[float]]]]:
                {
                    date(2024, 10, 28): {
                        "ich_rettemp": {
                            "min": 27.1,
                            "avg": 28.2,
                            "max": 29.0,
                        },
                        ...
                    }
                }

        Example:
            stats = service.aggregate_daily_sensor_stats(
                rows=raw_rows,
                sensor_columns=["ich_rettemp", "iac_airflow"],
            )
        """
        cleaned_columns = self._validate_sensor_columns(sensor_columns)

        if not cleaned_columns:
            logger.warning(
                "No valid sensor columns were provided for aggregation."
            )
            return {}

        rows_by_day: Dict[date, List[Dict[str, Any]]] = defaultdict(list)

        for row in rows:
            dt_value = self._to_date(row.get("dt"))
            if dt_value is None:
                continue
            rows_by_day[dt_value].append(row)

        logger.info(
            "Aggregating processvalue daily stats | day_count=%s sensor_count=%s",
            len(rows_by_day),
            len(cleaned_columns),
        )

        result: Dict[date, Dict[str, Dict[str, Optional[float]]]] = {}

        for dt_value in sorted(rows_by_day.keys()):
            result[dt_value] = {}

            for sensor_key in cleaned_columns:
                values = self._extract_numeric_values(
                    rows=rows_by_day[dt_value],
                    sensor_key=sensor_key,
                )
                latest_value = self._extract_latest_numeric_value(
                    rows=rows_by_day[dt_value],
                    sensor_key=sensor_key,
                )

                result[dt_value][sensor_key] = {
                    "min": self._compute_min(values),
                    "avg": self._compute_avg(values),
                    "max": self._compute_max(values),
                    "value_sum": self._compute_sum(values),
                    "sample_count": len(rows_by_day[dt_value]),
                    "non_null_count": len(values),
                    "zero_count": self._count_zero_values(values),
                    "negative_count": self._count_negative_values(values),
                    "latest": latest_value,
                }

        logger.info(
            "Aggregated processvalue daily stats successfully. day_count=%s",
            len(result),
        )
        return result

    def _validate_sensor_columns(self, sensor_columns: List[str]) -> List[str]:
        """Validate and normalize sensor columns.

        Args:
            sensor_columns: Raw sensor column list.

        Returns:
            List[str]: Cleaned unique sensor columns preserving input order.
        """
        cleaned: List[str] = []
        seen = set()

        for column in sensor_columns:
            if not isinstance(column, str):
                continue

            normalized = column.strip()
            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)
            cleaned.append(normalized)

        return cleaned

    def _to_date(self, value: Any) -> Optional[date]:
        """Convert supported datetime-like values to date.

        Args:
            value: Raw datetime-like value.

        Returns:
            Optional[date]: Parsed date value, or None when unsupported.
        """
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    def _extract_numeric_values(
        self,
        rows: List[Dict[str, Any]],
        sensor_key: str,
    ) -> List[float]:
        """Extract numeric values for one sensor from daily rows.

        Args:
            rows: Raw rows belonging to one day.
            sensor_key: Sensor column key.

        Returns:
            List[float]: Numeric values only. None and invalid types are skipped.
        """
        values: List[float] = []

        for row in rows:
            raw_value = row.get(sensor_key)

            if isinstance(raw_value, (int, float)):
                values.append(float(raw_value))

        return values

    def _compute_min(self, values: List[float]) -> Optional[float]:
        """Compute minimum value.

        Args:
            values: Numeric values.

        Returns:
            Optional[float]: Minimum value, or None if empty.
        """
        if not values:
            return None
        return round(min(values), 4)

    def _compute_avg(self, values: List[float]) -> Optional[float]:
        """Compute average value.

        Args:
            values: Numeric values.

        Returns:
            Optional[float]: Average value, or None if empty.
        """
        if not values:
            return None
        return round(sum(values) / len(values), 4)

    def _compute_max(self, values: List[float]) -> Optional[float]:
        """Compute maximum value.

        Args:
            values: Numeric values.

        Returns:
            Optional[float]: Maximum value, or None if empty.
        """
        if not values:
            return None
        return round(max(values), 4)

    def _compute_sum(self, values: List[float]) -> Optional[float]:
        """Compute raw numeric sum for downstream weighted aggregation."""
        if not values:
            return None
        return float(sum(values))

    def _extract_latest_numeric_value(
        self,
        rows: List[Dict[str, Any]],
        sensor_key: str,
    ) -> Optional[float]:
        """Return the last numeric value for one sensor within ordered rows."""
        for row in reversed(rows):
            raw_value = row.get(sensor_key)
            if isinstance(raw_value, (int, float)):
                return round(float(raw_value), 4)
        return None

    def _count_zero_values(self, values: List[float]) -> int:
        """Count exact-zero numeric values."""
        return sum(1 for value in values if float(value) == 0.0)

    def _count_negative_values(self, values: List[float]) -> int:
        """Count negative numeric values."""
        return sum(1 for value in values if float(value) < 0.0)
