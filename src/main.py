# -*- coding: utf-8 -*-

from pathlib import Path

from src.config.config_loader import load_config
from src.db.mysql_client import MySQLClient, MySQLConfig
from src.db.queries import DataSourceConfig, EnergyDataRepository
from src.db.report_repository import MySqlEnergyReportRepository
from src.services.aggregation_service import AggregationService
from src.services.csv_export_service import CsvExportService
from src.services.pdf_service import PDFService
from src.services.period_service import PeriodService
from src.services.template_service import TemplateRenderingService
from src.utils.logger import get_logger, setup_logging
from src.config.data_sources import get_data_sources
from src.services.kpi_service import KPIService
from src.services.utility_service import UtilityService

def run_dev_test():
    """Run the local development report flow.

    Args:
        None

    Returns:
        None

    Example:
        python -m src.main
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

    # Build repositories from data sources
    repos = {
        name: EnergyDataRepository(client, cfg)
        for name, cfg in sources.items()
    }
 
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
    #
    kpi_repo = repos["energy_kpi"]

    try:
        kpi_rows = kpi_repo.get_kpi_rows_in_period(
            start_date=period.start_date,
            end_date=period.end_date,
        )
        print(f"[TEST] energy_kpi raw rows={len(kpi_rows)}")

        kpi_service = KPIService()
        latest_kpi_rows = kpi_service.select_latest_kpi_rows(kpi_rows)

        print(f"[TEST] energy_kpi latest rows={len(latest_kpi_rows)}")

        if latest_kpi_rows:
            print("[TEST] energy_kpi first latest row:", latest_kpi_rows[0])

    except Exception as exc:
        print(f"[TEST] energy_kpi: ERROR -> {exc}")
    #
    kpi_object = kpi_service.build_kpi_report_object(
        rows=kpi_rows,
        report_start=period.start_date,
        report_end=period.end_date,
    )

    print(f"[TEST] kpi_object summary={kpi_object['summary']}")
    print(f"[TEST] kpi_object coverage={kpi_object['coverage']}")
    print(f"[TEST] kpi_object selected_rows_count={len(kpi_object['selected_rows'])}")
    print(f"[TEST] kpi_object daily_rows_count={len(kpi_object['daily_rows'])}")
    #
    utility_repo = repos["utility_usage"]

    utility_rows = utility_repo.get_daily_detail_rows(
        start_date=period.start_date,
        end_date=period.end_date,
    )

    utility_service = UtilityService()

    utility_object = utility_service.build_utility_report_object(
        rows=utility_rows,
        report_start=period.start_date,
        report_end=period.end_date,
    )

    print(f"[TEST] utility summary={utility_object['summary']}")
    print(f"[TEST] utility timeseries_count={len(utility_object['timeseries'])}")

    if utility_object["timeseries"]:
        print(f"[TEST] utility first={utility_object['timeseries'][0]}")

    logger.info(
        "Resolved report period | period_type=%s start_date=%s end_date=%s previous_start_date=%s previous_end_date=%s label=%s",
        period.period_type,
        period.start_date,
        period.end_date,
        period.previous_start_date,
        period.previous_end_date,
        period.label,
    )

    return

    service = AggregationService(repo, config)
    report = service.build_report(period)

    print("REPORT PERIOD:", report["report_period"])
    print("TOTAL ENERGY:", report["total_energy"])
    print("BAR CHART:", report["bar_chart_data"])
    print("TOP METERS:", report["top_meters"][:3])
    print("DAILY SUMMARY ROWS:", report["daily_summary_rows"][:2])
    print("COMPARISON:", report["comparison"])

    renderer = TemplateRenderingService(project_root / "src" / "templates")
    html = renderer.render("report_template.html", report)

    output_dir = Path(env_cfg["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = period.file_suffix

    html_output_path = output_dir / f"energy_report_{file_suffix}.html"
    csv_output_path = output_dir / f"energy_report_{file_suffix}_raw.csv"
    pdf_path = output_dir / f"energy_report_{file_suffix}.pdf"

    html_output_path.write_text(html, encoding="utf-8")
    print("HTML FILE:", html_output_path)

    csv_exporter = CsvExportService()
    final_csv_path = csv_exporter.export_rows(
        rows=report["raw_detail_rows"],
        output_path=csv_output_path,
    )
    print("CSV FILE:", final_csv_path)

    pdf_service = PDFService(config)
    pdf_service.export(html_output_path, pdf_path)
    print("PDF FILE:", pdf_path)

    logger.info(
        (
            "ETL job completed | period_type=%s start_date=%s end_date=%s "
            "total_energy=%s total_days=%s days_with_data=%s "
            "total_meter_count=%s html_file=%s csv_file=%s pdf_file=%s"
        ),
        period.period_type,
        period.start_date,
        period.end_date,
        report["total_energy"],
        report["summary"]["total_days"],
        report["summary"]["days_with_data"],
        report["summary"]["total_meter_count"],
        html_output_path,
        final_csv_path,
        pdf_path,
    )


def run_production():
    """Run the production report flow.

    Args:
        None

    Returns:
        None

    Example:
        run_production()
    """
    run_dev_test()


if __name__ == "__main__":
    run_dev_test()