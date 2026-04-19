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

    print(f"[TEST] energy_kpi current_raw_rows={len(current_rows)}")
    print(f"[TEST] energy_kpi previous_raw_rows={len(previous_rows)}")

    kpi_service = KPIService()

    kpi_object = kpi_service.build_full_kpi_object(
        current_rows=current_rows,
        previous_rows=previous_rows,
        report_start=period.start_date,
        report_end=period.end_date,
        previous_start=period.previous_start_date,
        previous_end=period.previous_end_date,
    )

    print(f"[TEST] kpi comparison plant={kpi_object['comparison']['plant']}")
    print(f"[TEST] kpi comparison areas={kpi_object['comparison']['areas']}")
    print(
        f"[TEST] kpi current coverage="
        f"{kpi_object['current']['coverage']['coverage_days']}/"
        f"{kpi_object['current']['coverage']['report_total_days']}"
    )
    print(
        f"[TEST] kpi previous coverage="
        f"{kpi_object['previous']['coverage']['coverage_days']}/"
        f"{kpi_object['previous']['coverage']['report_total_days']}"
    )

    return kpi_object


def _build_utility_object(
    repos: dict[str, EnergyDataRepository],
    period,
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

    utility_service = UtilityService()

    utility_object = utility_service.build_full_utility_object(
        current_rows=current_rows,
        previous_rows=previous_rows,
        report_start=period.start_date,
        report_end=period.end_date,
        previous_start=period.previous_start_date,
        previous_end=period.previous_end_date,
    )

    print(f"[TEST] utility comparison keys={utility_object['comparison'].keys()}")

    first_key = list(utility_object["comparison"].keys())[0]
    print(
        f"[TEST] utility comparison sample="
        f"{first_key} -> {utility_object['comparison'][first_key]}"
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

    print(f"[TEST] report_context keys={report_context.keys()}")
    print(f"[TEST] sections={report_context['sections'].keys()}")

    #1
    # print(f"[TEST] period={report_context['period']}")
    # print(f"[TEST] flags={report_context['flags']}")
    # print(f"[TEST] labels={report_context['labels']}")
    #2
    # print(f"[TEST] utility_snapshot_rows={len(report_context['summary']['utility_snapshot_rows'])}")
    # print(f"[TEST] kpi_area_snapshot_rows={len(report_context['summary']['kpi_area_snapshot_rows'])}")
    # print(f"[TEST] coverage={report_context['summary']['coverage']}")
    #3
    # print(
    #     f"[TEST] electricity totals rows="
    #     f"{len(report_context['sections']['electricity']['totals']['rows'])}"
    # )
    # print(
    #     f"[TEST] electricity comparison rows="
    #     f"{len(report_context['sections']['electricity']['comparison']['rows'])}"
    # )
    # print(
    #     f"[TEST] electricity top10 rows="
    #     f"{len(report_context['sections']['electricity']['top10']['rows'])}"
    # )
    # print(
    #     f"[TEST] electricity daily_summary rows="
    #     f"{len(report_context['sections']['electricity']['daily_summary']['rows'])}"
    # )
    # print(
    #     f"[TEST] electricity daily_detail_tables="
    #     f"{len(report_context['sections']['electricity']['daily_detail_tables'])}"
    # )
    # print(
    #     f"[TEST] electricity top10 sample="
    #     f"{report_context['sections']['electricity']['top10']['rows'][0]}"
    # )
    #4
    # print(
    #     f"[TEST] utility totals rows="
    #     f"{len(report_context['sections']['utility']['consumption']['totals']['rows'])}"
    # )
    # print(
    #     f"[TEST] utility daily_columns="
    #     f"{len(report_context['sections']['utility']['consumption']['detail']['daily_columns'])}"
    # )
    # print(
    #     f"[TEST] utility daily_rows="
    #     f"{len(report_context['sections']['utility']['consumption']['detail']['daily_rows'])}"
    # )
    # print(
    #     f"[TEST] utility coverage="
    #     f"{report_context['sections']['utility']['consumption']['coverage']}"
    # )
    # print(
    #     f"[TEST] utility totals sample="
    #     f"{report_context['sections']['utility']['consumption']['totals']['rows'][0]}"
    # )
    #5
    print(
        f"[TEST] kpi totals areas="
        f"{len(report_context['sections']['kpi']['totals']['areas'])}"
    )
    print(
        f"[TEST] kpi comparison areas="
        f"{len(report_context['sections']['kpi']['comparison']['areas'])}"
    )
    print(
        f"[TEST] kpi product_context rows="
        f"{len(report_context['sections']['kpi']['product_context']['rows'])}"
    )
    print(
        f"[TEST] kpi daily_detail rows="
        f"{len(report_context['sections']['kpi']['daily_detail']['rows'])}"
    )
    print(
        f"[TEST] kpi coverage="
        f"{report_context['sections']['kpi']['coverage']}"
    )
    print(
        f"[TEST] kpi comparison plant="
        f"{report_context['sections']['kpi']['comparison']['plant']}"
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
    utility_object = _build_utility_object(repos, period)
    energy_object = _build_energy_object(repos, period, kpi_object)

    report_context = _build_report_context(
        env_cfg=env_cfg,
        period=period,
        energy_object=energy_object,
        kpi_object=kpi_object,
        utility_object=utility_object,
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