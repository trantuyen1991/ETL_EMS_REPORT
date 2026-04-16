# -*- coding: utf-8 -*-
from src.utils.logger import setup_logging, get_logger
from pathlib import Path
from datetime import date

from src.config.config_loader import load_config
from src.db.mysql_client import MySQLClient, MySQLConfig
from src.db.queries import EnergyDataRepository, DataSourceConfig

from src.services.aggregation_service import AggregationService
from src.services.template_service import TemplateRenderingService

from src.services.csv_export_service import CsvExportService
from src.services.pdf_service import PDFService


def run_dev_test():
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 7)

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

    source_config = DataSourceConfig(
        database="ems_db",
        object_name="diode_energy",
        object_type="view",
        date_column="dt",
        excluded_columns=("dt",),
    )

    repo = EnergyDataRepository(client, source_config)
    service = AggregationService(repo, config)

    report = service.build_report(start_date, end_date)
    
    print("TOTAL ENERGY:", report["total_energy"])
    print("BAR CHART:", report["bar_chart_data"])
    print("TOP METERS:", report["top_meters"][:3])
    print("DAILY SUMMARY ROWS:", report["daily_summary_rows"][:2])
    print("COMPARISON:", report["comparison"])

    renderer = TemplateRenderingService(project_root / "src" / "templates")
    html = renderer.render("report_template.html", report)

    output_dir = Path(env_cfg["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    html_output_path = output_dir / "debug_report.html"
    html_output_path.write_text(html, encoding="utf-8")
    print("HTML FILE:", html_output_path)

    csv_exporter = CsvExportService()
    csv_output_path = output_dir / "debug_report_raw_detail.csv"
    final_csv_path = csv_exporter.export_rows(
        rows=report["raw_detail_rows"],
        output_path=csv_output_path,
    )
    print("CSV FILE:", final_csv_path)

    pdf_path = output_dir / "energy_report.pdf"

    pdf_service = PDFService(config)
    pdf_service.export(html_output_path, pdf_path)

    print("PDF FILE:", pdf_path)

    logger.info(
        "ETL job completed | start_date=%s end_date=%s total_energy=%s total_days=%s total_meter_count=%s html_file=%s csv_file=%s pdf_file=%s",
        start_date,
        end_date,
        report["total_energy"],
        report["summary"]["total_days"],
        report["summary"]["total_meter_count"],
        html_output_path,
        final_csv_path,
        pdf_path,
    )

def run_production():
    print("=== PRODUCTION MODE ===")

    # Future steps:
    # - parse input date
    # - build report
    # - export PDF
    pass


if __name__ == "__main__":
    run_dev_test()