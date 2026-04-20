# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Any

from src.config.config_loader import load_config
from src.config.data_sources import get_data_sources
from src.db.mysql_client import MySQLClient, MySQLConfig
from src.db.queries import EnergyDataRepository
from src.services.kpi_service import KPIService
from src.services.period_service import PeriodService
from src.services.report_builder_service import ReportBuilderService
from src.services.utility_service import UtilityService
from src.utils.logger import get_logger, setup_logging
from src.services.template_service import TemplateRenderingService
from src.services.energy_service import EnergyService

from datetime import datetime, date
from src.config.utility_metadata import get_utility_sensor_metadata
from src.db.processvalue_repository import ProcessValueRepository
from src.services.processvalue_service import ProcessValueService

def _bootstrap() -> dict[str, Any]:
    """Bootstrap application runtime objects for development flow.

    Returns:
        dict[str, Any]: Runtime objects required by the dev flow.

    Example:
        runtime = _bootstrap()
    """
    project_root = Path(__file__).resolve().parent.parent

    setup_logging(
        logging_config_path=project_root / "config" / "logging.yaml",
        log_file_path=project_root / "logs" / "app.log",
    )

    logger = get_logger(__name__)
    logger.info("=== DEV MODE STARTED ===")

    config = load_config(
        env_path=project_root / "config" / ".env",
        yaml_path=project_root / "config" / "app.yaml",
    )

    env_cfg = config["env"]

    mysql_config = MySQLConfig(
        host=env_cfg["MYSQL_HOST"],
        port=int(env_cfg["MYSQL_PORT"]),
        database=env_cfg["MYSQL_DATABASE"],
        user=env_cfg["MYSQL_USER"],
        password=env_cfg["MYSQL_PASSWORD"],
    )

    client = MySQLClient(mysql_config)

    period_service = PeriodService()
    period = period_service.resolve_from_config(config)

    sources = get_data_sources()
    repos = {
        name: EnergyDataRepository(client, cfg)
        for name, cfg in sources.items()
    }

    return {
        "project_root": project_root,
        "logger": logger,
        "config": config,
        "env_cfg": env_cfg,
        "client": client,
        "period": period,
        "repos": repos,
    }


def _run_generic_source_smoke_test(
    repos: dict[str, EnergyDataRepository],
    period,
) -> None:
    """Run a quick smoke test for generic dt-based sources."""
    generic_source_names = [
        "all_energy",
        "diode_energy",
        "ico_energy",
        "sakari_energy",
        "utility_usage",
    ]

    for name in generic_source_names:
        repo = repos[name]
        try:
            rows = repo.get_daily_detail_rows(
                start_date=period.start_date,
                end_date=period.end_date,
            )
            print(f"[TEST] {name}: rows={len(rows)}")
        except Exception as exc:
            print(f"[TEST] {name}: ERROR -> {exc}")


def _build_kpi_object(
    repos: dict[str, EnergyDataRepository],
    period,
) -> dict[str, Any]:
    """Build the full KPI object for current and previous period."""
    kpi_repo = repos["energy_kpi"]

    current_rows = kpi_repo.get_kpi_rows_in_period(
        start_date=period.start_date,
        end_date=period.end_date,
    )
    previous_rows = kpi_repo.get_kpi_rows_in_period(
        start_date=period.previous_start_date,
        end_date=period.previous_end_date,
    )

    kpi_service = KPIService()

    kpi_object = kpi_service.build_full_kpi_object(
        current_rows=current_rows,
        previous_rows=previous_rows,
        report_start=period.start_date,
        report_end=period.end_date,
        previous_start=period.previous_start_date,
        previous_end=period.previous_end_date,
    )

    return kpi_object

def _build_sensor_monitoring_context(
    client: MySQLClient,
    report_start: date,
    report_end: date,
) -> dict[str, Any]:
    """Build utility sensor monitoring context for a report period."""
    sensor_metadata = get_utility_sensor_metadata()
    sensor_columns = list(sensor_metadata.keys())

    repo = ProcessValueRepository(mysql_client=client)
    sensor_service = ProcessValueService()
    utility_service = UtilityService()

    start_dt = datetime.combine(report_start, datetime.min.time())
    end_dt_exclusive = datetime.combine(
        report_end.fromordinal(report_end.toordinal() + 1),
        datetime.min.time(),
    )

    rows = repo.fetch_sensor_rows(
        start_dt=start_dt,
        end_dt_exclusive=end_dt_exclusive,
        sensor_columns=sensor_columns,
    )

    daily_stats = sensor_service.aggregate_daily_sensor_stats(
        rows=rows,
        sensor_columns=sensor_columns,
    )

    sensor_monitoring = utility_service.build_sensor_monitoring_context(
        daily_stats=daily_stats,
        report_start=report_start,
        report_end=report_end,
    )

    return sensor_monitoring

def _build_utility_object(
    repos: dict[str, EnergyDataRepository],
    period,
    client: MySQLClient,
) -> dict[str, Any]:
    """Build the full utility object for current and previous period."""
    utility_repo = repos["utility_usage"]

    current_rows = utility_repo.get_daily_detail_rows(
        start_date=period.start_date,
        end_date=period.end_date,
    )
    previous_rows = utility_repo.get_daily_detail_rows(
        start_date=period.previous_start_date,
        end_date=period.previous_end_date,
    )

    current_sensor_monitoring = _build_sensor_monitoring_context(
        client=client,
        report_start=period.start_date,
        report_end=period.end_date,
    )

    previous_sensor_monitoring = _build_sensor_monitoring_context(
        client=client,
        report_start=period.previous_start_date,
        report_end=period.previous_end_date,
    )

    utility_service = UtilityService()

    utility_object = utility_service.build_full_utility_object(
        current_rows=current_rows,
        previous_rows=previous_rows,
        report_start=period.start_date,
        report_end=period.end_date,
        previous_start=period.previous_start_date,
        previous_end=period.previous_end_date,
        current_sensor_monitoring=current_sensor_monitoring,
        previous_sensor_monitoring=previous_sensor_monitoring,
    )

    return utility_object

def _build_energy_object(
    repos: dict[str, EnergyDataRepository],
    period,
    kpi_object: dict[str, Any],
) -> dict[str, Any]:
    """Build the full energy object for current and previous period."""
    energy_service = EnergyService()

    current_area_rows = {
        "diode": repos["diode_energy"].get_daily_detail_rows(
            start_date=period.start_date,
            end_date=period.end_date,
        ),
        "ico": repos["ico_energy"].get_daily_detail_rows(
            start_date=period.start_date,
            end_date=period.end_date,
        ),
        "sakari": repos["sakari_energy"].get_daily_detail_rows(
            start_date=period.start_date,
            end_date=period.end_date,
        ),
    }

    previous_area_rows = {
        "diode": repos["diode_energy"].get_daily_detail_rows(
            start_date=period.previous_start_date,
            end_date=period.previous_end_date,
        ),
        "ico": repos["ico_energy"].get_daily_detail_rows(
            start_date=period.previous_start_date,
            end_date=period.previous_end_date,
        ),
        "sakari": repos["sakari_energy"].get_daily_detail_rows(
            start_date=period.previous_start_date,
            end_date=period.previous_end_date,
        ),
    }

    current_area_columns = {
        "diode": repos["diode_energy"].get_meter_columns(),
        "ico": repos["ico_energy"].get_meter_columns(),
        "sakari": repos["sakari_energy"].get_meter_columns(),
    }

    energy_object = energy_service.build_full_energy_object(
        current_area_rows=current_area_rows,
        previous_area_rows=previous_area_rows,
        current_area_columns=current_area_columns,
        previous_area_columns=current_area_columns,
        current_kpi_summary=kpi_object["current"]["summary"],
        previous_kpi_summary=kpi_object["previous"]["summary"],
        current_kpi_rows=kpi_object["current"]["selected_rows"],
        previous_kpi_rows=kpi_object["previous"]["selected_rows"],
        report_start=period.start_date,
        report_end=period.end_date,
        previous_start=period.previous_start_date,
        previous_end=period.previous_end_date,
    )
    return energy_object

def _build_report_context(
    env_cfg: dict[str, Any],
    period,
    energy_object: dict[str, Any],
    kpi_object: dict[str, Any],
    utility_object: dict[str, Any],
    client: MySQLClient,
) -> dict[str, Any]:
    """Build the unified report context for V2."""
    report_builder = ReportBuilderService()

    meta = {
        "report_title": env_cfg.get("FILE_NAME_PREFIX", ""),
        "report_subtitle": "Automatic Report",
        "workshop_name": env_cfg.get("WORKSHOP_NAME", ""),
        "energy_unit": env_cfg.get("ENERGY_UNIT", "kWh"),
        "kpi_unit": env_cfg.get("KPI_UNIT", "kWh/Ton"),
    }

    period_info = {
        "start_date": period.start_date,
        "end_date": period.end_date,
        "type": period.period_type,
        "label": period.label,
        "comparison_label": period.comparison_label,
        "previous_start_date": period.previous_start_date,
        "previous_end_date": period.previous_end_date,
    }

    report_context = report_builder.build_report_context_v3(
        meta=meta,
        period=period_info,
        energy_object=energy_object,
        kpi_object=kpi_object,
        utility_object=utility_object,
        mode="html",
    )

    return report_context


def run_dev_test() -> None:
    """Run the local development flow for V2 data objects."""
    runtime = _bootstrap()

    logger = runtime["logger"]
    env_cfg = runtime["env_cfg"]
    period = runtime["period"]
    repos = runtime["repos"]

    _run_generic_source_smoke_test(repos, period)

    kpi_object = _build_kpi_object(repos, period)

    utility_object = _build_utility_object(
        repos=repos,
        period=period,
        client=runtime["client"],
    )
    print(
        f"[TEST] current sensor_monitoring keys="
        f"{utility_object['current']['sensor_monitoring'].keys()}"
    )
    print(
        f"[TEST] current sensor first_row="
        f"{utility_object['current']['sensor_monitoring']['daily_rows'][0] if utility_object['current']['sensor_monitoring']['daily_rows'] else None}"
    )
    energy_object = _build_energy_object(repos, period, kpi_object)

    report_context = _build_report_context(
        env_cfg=env_cfg,
        period=period,
        energy_object=energy_object,
        kpi_object=kpi_object,
        utility_object=utility_object,
        client=runtime["client"],
    )
    #
    renderer = TemplateRenderingService("src/templates")

    html = renderer.render("report/view/report_view.html", report_context)

    with open("output/reports/debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(
        (
            "Resolved report period | period_type=%s start_date=%s end_date=%s "
            "previous_start_date=%s previous_end_date=%s label=%s"
        ),
        period.period_type,
        period.start_date,
        period.end_date,
        period.previous_start_date,
        period.previous_end_date,
        period.label,
    )


def run_production() -> None:
    """Run production flow."""
    run_dev_test()


if __name__ == "__main__":
    run_dev_test()