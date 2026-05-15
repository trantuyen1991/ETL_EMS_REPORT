"""Repository for reading raw utility sensor data from processvalue."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import logging
import re

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

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    TABLE_NAME = "processvalue"
    TIMESTAMP_COLUMN = "Time_Stamp"

    def __init__(
        self,
        mysql_client: MySQLClient,
        database: str | None = None,
        source_timezone: str = "UTC",
        target_timezone: str = "Asia/Ho_Chi_Minh",
    ) -> None:
        """Initialize repository.

        Args:
            mysql_client: Shared MySQL client instance.
            database: Optional database/schema override. Defaults to the
                database configured on the shared MySQL client.
            source_timezone: Timezone used by stored processvalue timestamps.
            target_timezone: Timezone expected by the report layer.
        """
        self.mysql_client = mysql_client
        self.database = database or mysql_client.database
        self.source_timezone = source_timezone or "UTC"
        self.target_timezone = target_timezone or "Asia/Ho_Chi_Minh"
        self._source_zone = self._load_zoneinfo(self.source_timezone)
        self._target_zone = self._load_zoneinfo(self.target_timezone)
        self._validate_identifier(self.database)
        self._validate_identifier(self.TABLE_NAME)
        self._validate_identifier(self.TIMESTAMP_COLUMN)

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
            FROM {self._source_table()}
            WHERE {self._quote(self.TIMESTAMP_COLUMN)} >= %s
              AND {self._quote(self.TIMESTAMP_COLUMN)} < %s
            ORDER BY {self._quote(self.TIMESTAMP_COLUMN)} ASC
        """

        query_start_dt, query_end_dt_exclusive = self._convert_local_window_to_source(
            start_dt=start_dt,
            end_dt_exclusive=end_dt_exclusive,
        )
        params = (query_start_dt, query_end_dt_exclusive)

        logger.info(
            "Fetching processvalue sensor rows | local_start_dt=%s local_end_dt_exclusive=%s query_start_dt=%s query_end_dt_exclusive=%s source_timezone=%s target_timezone=%s columns=%s",
            start_dt,
            end_dt_exclusive,
            query_start_dt,
            query_end_dt_exclusive,
            self.source_timezone,
            self.target_timezone,
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

    def _validate_identifier(self, identifier: str) -> str:
        """Validate a SQL identifier before it is quoted into a query."""
        if not identifier or not self.IDENTIFIER_PATTERN.match(identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier

    def _quote(self, identifier: str) -> str:
        """Return a backtick-quoted SQL identifier."""
        return f"`{self._validate_identifier(identifier)}`"

    def _source_table(self) -> str:
        """Return the fully qualified processvalue table source."""
        return f"{self._quote(self.database)}.{self._quote(self.TABLE_NAME)}"

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

            self._validate_identifier(normalized)
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
        quoted_columns = [self._quote(self.TIMESTAMP_COLUMN)]
        quoted_columns.extend(self._quote(column) for column in sensor_columns)
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
            "dt": self._convert_row_timestamp_to_target(row.get(self.TIMESTAMP_COLUMN)),
        }

        for column in sensor_columns:
            mapped[column] = row.get(column)

        return mapped

    def _load_zoneinfo(self, timezone_name: str) -> ZoneInfo:
        """Return a ZoneInfo object with a clear error on bad config."""
        try:
            return ZoneInfo(str(timezone_name or "").strip())
        except Exception as exc:
            raise ValueError(f"Invalid timezone: {timezone_name}") from exc

    def _attach_timezone(self, value: datetime, zone: ZoneInfo) -> datetime:
        """Attach or convert a datetime into a specific timezone."""
        if value.tzinfo is None:
            return value.replace(tzinfo=zone)
        return value.astimezone(zone)

    def _to_naive_datetime(self, value: datetime) -> datetime:
        """Drop timezone info after conversion for MySQL-driver compatibility."""
        return value.replace(tzinfo=None)

    def _convert_local_window_to_source(
        self,
        *,
        start_dt: datetime,
        end_dt_exclusive: datetime,
    ) -> tuple[datetime, datetime]:
        """Convert local report datetimes into the stored source timezone."""
        localized_start = self._attach_timezone(start_dt, self._target_zone)
        localized_end = self._attach_timezone(end_dt_exclusive, self._target_zone)
        source_start = localized_start.astimezone(self._source_zone)
        source_end = localized_end.astimezone(self._source_zone)
        return (
            self._to_naive_datetime(source_start),
            self._to_naive_datetime(source_end),
        )

    def _convert_row_timestamp_to_target(self, value: Any) -> Any:
        """Convert one stored timestamp from source timezone into report timezone."""
        if not isinstance(value, datetime):
            return value

        source_value = self._attach_timezone(value, self._source_zone)
        target_value = source_value.astimezone(self._target_zone)
        return self._to_naive_datetime(target_value)
