"""Repository for reading raw utility sensor data from processvalue."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import logging

from src.db.mysql_client import MySQLClient


logger = logging.getLogger(__name__)


class ProcessValueRepository:
    """Read raw sensor rows from the processvalue table.

    This repository only fetches raw timestamped rows and does not apply
    aggregation, formatting, or business calculations.

    Args:
        mysql_client: Shared MySQL client instance.

    Example:
        repo = ProcessValueRepository(mysql_client)
        rows = repo.fetch_sensor_rows(
            start_dt=datetime(2025, 5, 19, 0, 0, 0),
            end_dt_exclusive=datetime(2025, 5, 26, 0, 0, 0),
            sensor_columns=["ich_rettemp", "ich_suptemp"],
        )
    """

    TABLE_NAME = "ems_db.processvalue"
    TIMESTAMP_COLUMN = "Time_Stamp"

    def __init__(self, mysql_client: MySQLClient) -> None:
        """Initialize repository.

        Args:
            mysql_client: Shared MySQL client instance.
        """
        self.mysql_client = mysql_client

    def fetch_sensor_rows(
        self,
        start_dt: datetime,
        end_dt_exclusive: datetime,
        sensor_columns: List[str],
    ) -> List[Dict[str, Any]]:
        """Fetch raw sensor rows for a timestamp range.

        Args:
            start_dt: Inclusive start datetime.
            end_dt_exclusive: Exclusive end datetime.
            sensor_columns: Sensor column names to select from processvalue.

        Returns:
            List[Dict[str, Any]]: Raw rows in the shape:
                [
                    {
                        "dt": datetime(...),
                        "<sensor_column>": value,
                        ...
                    }
                ]

        Example:
            rows = repo.fetch_sensor_rows(
                start_dt=datetime(2025, 10, 20, 0, 0, 0),
                end_dt_exclusive=datetime(2025, 10, 27, 0, 0, 0),
                sensor_columns=["ich_rettemp", "iac_airflow"],
            )
        """
        cleaned_columns = self._validate_sensor_columns(sensor_columns)

        if not cleaned_columns:
            logger.warning(
                "No valid sensor columns were provided for processvalue query."
            )
            return []

        select_sql = self._build_select_sql(cleaned_columns)

        sql = f"""
            SELECT {select_sql}
            FROM {self.TABLE_NAME}
            WHERE {self.TIMESTAMP_COLUMN} >= %s
              AND {self.TIMESTAMP_COLUMN} < %s
            ORDER BY {self.TIMESTAMP_COLUMN} ASC
        """

        params = (start_dt, end_dt_exclusive)

        logger.info(
            "Fetching processvalue sensor rows | start_dt=%s end_dt_exclusive=%s columns=%s",
            start_dt,
            end_dt_exclusive,
            cleaned_columns,
        )

        try:
            db_rows = self.mysql_client.fetch_all(sql, params)
            result = [self._map_db_row(row, cleaned_columns) for row in db_rows]

            logger.info(
                "Fetched processvalue sensor rows successfully. row_count=%s",
                len(result),
            )
            return result

        except Exception:
            logger.exception(
                "Failed to fetch processvalue sensor rows. start_dt=%s end_dt_exclusive=%s",
                start_dt,
                end_dt_exclusive,
            )
            raise

    def _validate_sensor_columns(self, sensor_columns: List[str]) -> List[str]:
        """Validate and normalize requested sensor columns.

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

    def _build_select_sql(self, sensor_columns: List[str]) -> str:
        """Build SELECT column SQL for processvalue query.

        Args:
            sensor_columns: Cleaned sensor columns.

        Returns:
            str: SQL-safe select clause using backtick-quoted columns.
        """
        quoted_columns = [f"`{self.TIMESTAMP_COLUMN}`"]
        quoted_columns.extend(f"`{column}`" for column in sensor_columns)
        return ", ".join(quoted_columns)

    def _map_db_row(
        self,
        row: Dict[str, Any],
        sensor_columns: List[str],
    ) -> Dict[str, Any]:
        """Map database row keys to repository output format.

        Args:
            row: Raw database row.
            sensor_columns: Requested sensor columns.

        Returns:
            Dict[str, Any]: Normalized row with `dt` key.
        """
        mapped: Dict[str, Any] = {
            "dt": row.get(self.TIMESTAMP_COLUMN),
        }

        for column in sensor_columns:
            mapped[column] = row.get(column)

        return mapped