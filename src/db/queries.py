"""
Reusable query repository for tabular energy sources.

This module provides:
- source configuration
- metadata discovery
- daily detail query
- aggregated meter totals
- top N meter extraction

Design principles:
- No hard-coded database/table/view
- Dynamic column discovery
- Safe SQL identifier handling
- Parameterized query for values
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, Sequence

from src.db.mysql_client import MySQLClient

logger = logging.getLogger(__name__)

NUMERIC_MYSQL_TYPES = {
    "tinyint",
    "smallint",
    "mediumint",
    "int",
    "bigint",
    "decimal",
    "float",
    "double",
}


# ==========================================================
# Data Models
# ==========================================================

@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration for a reusable tabular energy source."""

    database: str
    object_name: str
    object_type: str = "view"
    date_column: str = "dt"
    excluded_columns: Sequence[str] = field(default_factory=tuple)
    included_columns: Optional[Sequence[str]] = None


@dataclass(frozen=True)
class ColumnProfile:
    """Metadata profile for one source column."""

    name: str
    data_type: str
    is_nullable: bool
    ordinal_position: int
    is_meter_column: bool


# ==========================================================
# Repository
# ==========================================================

class EnergyDataRepository:
    """Repository for reusable energy source queries."""

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def __init__(self, client: MySQLClient, source_config: DataSourceConfig) -> None:
        self._client = client
        self._config = source_config
        self._validate_source_config()

    # ==========================================================
    # Validation
    # ==========================================================

    def _validate_source_config(self) -> None:
        self._validate_identifier(self._config.database)
        self._validate_identifier(self._config.object_name)
        self._validate_identifier(self._config.date_column)

        if self._config.object_type not in {"table", "view"}:
            raise ValueError("object_type must be 'table' or 'view'")

        for col in self._config.excluded_columns:
            self._validate_identifier(col)

        if self._config.included_columns:
            for col in self._config.included_columns:
                self._validate_identifier(col)

    def _validate_identifier(self, identifier: str) -> str:
        if not identifier or not self.IDENTIFIER_PATTERN.match(identifier):
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier

    def _validate_date_range(self, start_date: date, end_date: date) -> None:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

    def _validate_selected_columns(self, selected: Sequence[str]) -> list[str]:
        valid = set(self.get_meter_columns())
        for col in selected:
            if col not in valid:
                raise ValueError(f"Invalid column: {col}")
        return list(selected)

    # ==========================================================
    # SQL Helpers
    # ==========================================================

    def _quote(self, identifier: str) -> str:
        return f"`{self._validate_identifier(identifier)}`"

    def _source(self) -> str:
        return f"{self._quote(self._config.database)}.{self._quote(self._config.object_name)}"

    def _date_col(self) -> str:
        return self._quote(self._config.date_column)

    # ==========================================================
    # Metadata
    # ==========================================================

    def get_source_columns(self) -> list[ColumnProfile]:
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """

        rows = self._client.fetch_all(query, (self._config.database, self._config.object_name))

        result: list[ColumnProfile] = []

        for r in rows:
            name = r["COLUMN_NAME"]
            dtype = r["DATA_TYPE"].lower()
            is_meter = (
                name != self._config.date_column
                and dtype in NUMERIC_MYSQL_TYPES
                and name not in self._config.excluded_columns
            )

            result.append(
                ColumnProfile(
                    name=name,
                    data_type=dtype,
                    is_nullable=(r["IS_NULLABLE"] == "YES"),
                    ordinal_position=r["ORDINAL_POSITION"],
                    is_meter_column=is_meter,
                )
            )

        return result

    def get_meter_columns(self) -> list[str]:
        cols = self.get_source_columns()

        meters = [c.name for c in cols if c.is_meter_column]

        if self._config.included_columns:
            meters = [c for c in meters if c in self._config.included_columns]

        return meters

    def get_available_date_range(self) -> dict[str, Any]:
        query = f"""
        SELECT MIN({self._date_col()}) AS min_date,
               MAX({self._date_col()}) AS max_date,
               COUNT(*) AS total_rows
        FROM {self._source()}
        """

        row = self._client.fetch_one(query)

        return {
            "min_date": row["min_date"],
            "max_date": row["max_date"],
            "total_rows": row["total_rows"],
        }

    # ==========================================================
    # Business Queries
    # ==========================================================

    def count_rows_in_range(self, start_date: date, end_date: date) -> int:
        self._validate_date_range(start_date, end_date)

        query = f"""
        SELECT COUNT(*) AS cnt
        FROM {self._source()}
        WHERE {self._date_col()} BETWEEN %s AND %s
        """

        row = self._client.fetch_one(query, (start_date, end_date))
        return row["cnt"]

    def get_daily_detail_rows(
        self,
        start_date: date,
        end_date: date,
        selected_columns: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        self._validate_date_range(start_date, end_date)

        cols = selected_columns or self.get_meter_columns()
        cols = self._validate_selected_columns(cols)

        select_clause = ", ".join([self._date_col()] + [self._quote(c) for c in cols])

        query = f"""
        SELECT {select_clause}
        FROM {self._source()}
        WHERE {self._date_col()} BETWEEN %s AND %s
        ORDER BY {self._date_col()} ASC
        """

        return self._client.fetch_all(query, (start_date, end_date))

    def get_meter_totals(
        self,
        start_date: date,
        end_date: date,
        selected_columns: Optional[list[str]] = None,
        sort_desc: bool = True,
    ) -> list[dict[str, Any]]:
        self._validate_date_range(start_date, end_date)

        cols = selected_columns or self.get_meter_columns()
        cols = self._validate_selected_columns(cols)

        if not cols:
            return []

        agg_expr = ", ".join(
            [f"SUM(COALESCE({self._quote(c)},0)) AS {self._quote(c)}" for c in cols]
        )

        query = f"""
        SELECT {agg_expr}
        FROM {self._source()}
        WHERE {self._date_col()} BETWEEN %s AND %s
        """

        row = self._client.fetch_one(query, (start_date, end_date))

        result = [
            {"meter_name": c, "total_value": float(row[c] or 0)}
            for c in cols
        ]

        result.sort(key=lambda x: x["total_value"], reverse=sort_desc)
        return result

    def get_top_n_meters(
        self,
        start_date: date,
        end_date: date,
        top_n: int = 10,
        selected_columns: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        if top_n <= 0:
            raise ValueError("top_n must be > 0")

        totals = self.get_meter_totals(start_date, end_date, selected_columns, True)
        return totals[:top_n]