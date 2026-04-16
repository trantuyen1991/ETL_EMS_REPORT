"""
MySQL client module for database access.

This module provides a production-ready MySQL client with:
- connection management
- reconnect support
- parameterized query execution
- transaction handling
- structured logging
- dictionary-based result fetching
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict
from mysql.connector.pooling import MySQLConnectionPool

from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass(frozen=True)
class MySQLConfig:
    """
    MySQL connection settings.

    Args:
        host: MySQL server hostname or IP address.
        port: MySQL server port.
        database: Database name.
        user: Database username.
        password: Database password.
        connection_timeout: Connection timeout in seconds.
        autocommit: Whether to enable autocommit mode.
        pool_name: Name of the MySQL connection pool.
        pool_size: Number of pooled connections.

    Returns:
        MySQLConfig: Immutable configuration object.

    Example:
        config = MySQLConfig(
            host="127.0.0.1",
            port=3306,
            database="energy_db",
            user="report_user",
            password="secret",
            connection_timeout=10,
            autocommit=False,
            pool_name="energy_pdf_pool",
            pool_size=5,
        )
    """

    host: str
    port: int
    database: str
    user: str
    password: str
    connection_timeout: int = 10
    autocommit: bool = False
    pool_name: str = "energy_pdf_pool"
    pool_size: int = 5


class MySQLClient:
    """
    Production-ready MySQL client.

    This client uses mysql-connector connection pooling and provides helper
    methods for:
    - fetch_all
    - fetch_one
    - execute
    - executemany

    Args:
        config: MySQL configuration object.

    Returns:
        MySQLClient: Database client instance.

    Example:
        config = MySQLConfig(
            host="127.0.0.1",
            port=3306,
            database="energy_db",
            user="report_user",
            password="secret",
        )

        with MySQLClient(config) as client:
            rows = client.fetch_all(
                "SELECT id, meter_name FROM energy_meter WHERE active = %s",
                (1,),
            )
    """

    def __init__(self, config: MySQLConfig) -> None:
        self._config = config
        self._pool: Optional[MySQLConnectionPool] = None
        self._connection: Optional[MySQLConnection] = None

        self._create_pool()
        self._connect()

    def _create_pool(self) -> None:
        """
        Create MySQL connection pool.

        Raises:
            Error: If pool creation fails.

        Example:
            client._create_pool()
        """
        try:
            logger.info(
                "Creating MySQL connection pool. host=%s port=%s db=%s pool_name=%s pool_size=%s",
                self._config.host,
                self._config.port,
                self._config.database,
                self._config.pool_name,
                self._config.pool_size,
            )

            self._pool = MySQLConnectionPool(
                pool_name=self._config.pool_name,
                pool_size=self._config.pool_size,
                host=self._config.host,
                port=self._config.port,
                database=self._config.database,
                user=self._config.user,
                password=self._config.password,
                connection_timeout=self._config.connection_timeout,
                autocommit=self._config.autocommit,
            )
        except Error as exc:
            logger.exception("Failed to create MySQL connection pool.")
            raise RuntimeError("Failed to create MySQL connection pool.") from exc

    def _connect(self) -> None:
        """
        Acquire a connection from the pool.

        Raises:
            RuntimeError: If acquiring connection fails.

        Example:
            client._connect()
        """
        if self._pool is None:
            raise RuntimeError("MySQL connection pool is not initialized.")

        try:
            self._connection = self._pool.get_connection()
            self._connection.autocommit = self._config.autocommit

            logger.info(
                "MySQL connection acquired successfully. autocommit=%s",
                self._connection.autocommit,
            )
        except Error as exc:
            logger.exception("Failed to acquire MySQL connection from pool.")
            raise RuntimeError("Failed to acquire MySQL connection.") from exc

    def _ensure_connection(self) -> None:
        """
        Ensure the current connection is alive.

        Reconnects automatically if connection is closed or invalid.

        Raises:
            RuntimeError: If reconnection fails.

        Example:
            client._ensure_connection()
        """
        try:
            if self._connection is None:
                logger.warning("MySQL connection is None. Reconnecting.")
                self._connect()
                return

            if not self._connection.is_connected():
                logger.warning("MySQL connection is not connected. Reconnecting.")
                self._connect()
        except Error as exc:
            logger.exception("Failed to validate or reconnect MySQL connection.")
            raise RuntimeError("Failed to validate MySQL connection.") from exc

    def fetch_all(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return all rows.

        Args:
            query: SQL query string with placeholders (%s).
            params: Query parameters.

        Returns:
            list[dict[str, Any]]: List of result rows as dictionaries.

        Raises:
            RuntimeError: If query execution fails.

        Example:
            rows = client.fetch_all(
                "SELECT id, kwh FROM energy_reading WHERE reading_date = %s",
                ("2026-04-15",),
            )
        """
        self._ensure_connection()
        cursor: Optional[MySQLCursorDict] = None

        try:
            cursor = self._connection.cursor(dictionary=True)
            logger.debug("Executing fetch_all query: %s | params=%s", query, params)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            logger.info("fetch_all completed successfully. rows=%s", len(rows))
            return rows
        except Error as exc:
            logger.exception("Failed to execute fetch_all query.")
            raise RuntimeError("Failed to execute fetch_all query.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def fetch_one(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Execute a SELECT query and return the first row.

        Args:
            query: SQL query string with placeholders (%s).
            params: Query parameters.

        Returns:
            Optional[dict[str, Any]]: First row as a dictionary, or None.

        Raises:
            RuntimeError: If query execution fails.

        Example:
            row = client.fetch_one(
                "SELECT id, meter_name FROM energy_meter WHERE id = %s",
                (1001,),
            )
        """
        self._ensure_connection()
        cursor: Optional[MySQLCursorDict] = None

        try:
            cursor = self._connection.cursor(dictionary=True)
            logger.debug("Executing fetch_one query: %s | params=%s", query, params)

            cursor.execute(query, params)
            row = cursor.fetchone()

            logger.info("fetch_one completed successfully. found=%s", row is not None)
            return row
        except Error as exc:
            logger.exception("Failed to execute fetch_one query.")
            raise RuntimeError("Failed to execute fetch_one query.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def execute(
        self,
        query: str,
        params: Optional[Sequence[Any]] = None,
        *,
        commit: bool = True,
    ) -> int:
        """
        Execute a single INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL statement with placeholders (%s).
            params: Query parameters.
            commit: Whether to commit after execution.

        Returns:
            int: Number of affected rows.

        Raises:
            RuntimeError: If execution fails.

        Example:
            affected = client.execute(
                "UPDATE report_job SET status = %s WHERE job_id = %s",
                ("DONE", 10),
                commit=True,
            )
        """
        self._ensure_connection()
        cursor = None

        try:
            cursor = self._connection.cursor()
            logger.debug("Executing write query: %s | params=%s", query, params)

            cursor.execute(query, params)

            if commit and not self._connection.autocommit:
                self._connection.commit()

            rowcount = cursor.rowcount
            logger.info("execute completed successfully. affected_rows=%s", rowcount)
            return rowcount
        except Error as exc:
            if self._connection is not None and not self._connection.autocommit:
                self._connection.rollback()

            logger.exception("Failed to execute write query. Transaction rolled back.")
            raise RuntimeError("Failed to execute write query.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def executemany(
        self,
        query: str,
        param_sets: Iterable[Sequence[Any]],
        *,
        commit: bool = True,
    ) -> int:
        """
        Execute batch INSERT, UPDATE, or DELETE statements.

        Args:
            query: SQL statement with placeholders (%s).
            param_sets: Iterable of parameter tuples/lists.
            commit: Whether to commit after execution.

        Returns:
            int: Number of affected rows.

        Raises:
            RuntimeError: If batch execution fails.

        Example:
            affected = client.executemany(
                "INSERT INTO staging_energy (meter_id, kwh) VALUES (%s, %s)",
                [(1, 120.5), (2, 140.2)],
                commit=True,
            )
        """
        self._ensure_connection()
        cursor = None

        try:
            cursor = self._connection.cursor()
            param_sets = list(param_sets)

            logger.debug(
                "Executing batch query: %s | batch_size=%s",
                query,
                len(param_sets),
            )

            cursor.executemany(query, param_sets)

            if commit and not self._connection.autocommit:
                self._connection.commit()

            rowcount = cursor.rowcount
            logger.info("executemany completed successfully. affected_rows=%s", rowcount)
            return rowcount
        except Error as exc:
            if self._connection is not None and not self._connection.autocommit:
                self._connection.rollback()

            logger.exception("Failed to execute batch query. Transaction rolled back.")
            raise RuntimeError("Failed to execute batch query.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def commit(self) -> None:
        """
        Commit the current transaction.

        Raises:
            RuntimeError: If commit fails.

        Example:
            client.commit()
        """
        self._ensure_connection()

        try:
            self._connection.commit()
            logger.info("Transaction committed successfully.")
        except Error as exc:
            logger.exception("Failed to commit transaction.")
            raise RuntimeError("Failed to commit transaction.") from exc

    def rollback(self) -> None:
        """
        Roll back the current transaction.

        Raises:
            RuntimeError: If rollback fails.

        Example:
            client.rollback()
        """
        self._ensure_connection()

        try:
            self._connection.rollback()
            logger.warning("Transaction rolled back.")
        except Error as exc:
            logger.exception("Failed to roll back transaction.")
            raise RuntimeError("Failed to roll back transaction.") from exc

    def close(self) -> None:
        """
        Close the current MySQL connection.

        Example:
            client.close()
        """
        if self._connection is not None:
            try:
                if self._connection.is_connected():
                    self._connection.close()
                    logger.info("MySQL connection closed.")
            except Error:
                logger.exception("Error occurred while closing MySQL connection.")

    def __enter__(self) -> "MySQLClient":
        """
        Enter context manager.

        Returns:
            MySQLClient: Current client instance.

        Example:
            with MySQLClient(config) as client:
                ...
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager and close connection.

        Args:
            exc_type: Exception type.
            exc_val: Exception value.
            exc_tb: Traceback object.

        Example:
            with MySQLClient(config) as client:
                ...
        """
        self.close()