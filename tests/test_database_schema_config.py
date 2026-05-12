from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.config.data_sources import get_data_sources
from src.db.processvalue_repository import ProcessValueRepository


def test_data_sources_use_configured_database_name() -> None:
    sources = get_data_sources(database="bms_db")

    assert sources
    assert {source.database for source in sources.values()} == {"bms_db"}


@dataclass
class FakeMySQLClient:
    database: str = "bms_db"

    def fetch_all(self, query: str, params: tuple[object, ...]) -> list[dict[str, object]]:
        self.query = query
        self.params = params
        return []


def test_processvalue_repository_uses_client_database_in_source_table() -> None:
    client = FakeMySQLClient(database="bms_db")
    repo = ProcessValueRepository(mysql_client=client)  # type: ignore[arg-type]

    repo.fetch_sensor_rows(
        start_dt="2025-05-18 00:00:00",  # type: ignore[arg-type]
        end_dt_exclusive="2025-05-19 00:00:00",  # type: ignore[arg-type]
        sensor_columns=["ich_rettemp"],
    )

    assert "FROM `bms_db`.`processvalue`" in client.query
    assert "ems_db" not in client.query


def test_processvalue_repository_rejects_invalid_database_identifier() -> None:
    client = FakeMySQLClient(database="bms-db")

    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        ProcessValueRepository(mysql_client=client)  # type: ignore[arg-type]
