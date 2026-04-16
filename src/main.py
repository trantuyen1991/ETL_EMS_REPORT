# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import date

from src.config.config_loader import load_config
from src.db.mysql_client import MySQLClient, MySQLConfig
from src.db.queries import EnergyDataRepository, DataSourceConfig

from src.services.aggregation_service import AggregationService
from src.services.template_service import TemplateRenderingService

def run_dev_test():
    start_date = date(2025, 7, 1)
    end_date = date(2025, 7, 7)
    print("=== DEV MODE ===")

    project_root = Path(__file__).resolve().parent.parent

    config = load_config(
        env_path=project_root / "config" / ".env",
        yaml_path=project_root / "config" / "app.yaml",
    )

    #print("CONFIG TYPE:", type(config))
    #print("CONFIG KEYS:", config.keys())

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
    

    print("DATE RANGE:", repo.get_available_date_range())
    print("METER COLUMNS:", repo.get_meter_columns())

    rows = repo.get_daily_detail_rows(start_date, end_date)
    print("DETAIL ROWS:", rows[:2])

    top = repo.get_top_n_meters(start_date, end_date)
    print("TOP METERS:", top[:5])

    # Tetst AggregationService
    service = AggregationService(repo, config)

    report = service.build_report(start_date, end_date)

    print("TOTAL ENERGY:", report["total_energy"])
    print("BAR CHART:", report["bar_chart_data"])
    print("TOP METERS:", report["top_meters"][:3])

    print(type(report["bar_chart_data"]))
    print(report["bar_chart_data"])

    service = AggregationService(repo, config)

    report = service.build_report(start_date, end_date)

    renderer = TemplateRenderingService(project_root / "src" / "templates")
    html = renderer.render("report_template.html", report)

    print("HTML LENGTH:", len(html))
    print(html[:1000])

    output_html = project_root / "output" / "reports" / "debug_report.html"
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")

    print("HTML FILE:", output_html)

def run_production():
    print("=== PRODUCTION MODE ===")

    # Sau này bạn sẽ:
    # - parse input date
    # - build report
    # - export PDF
    pass


if __name__ == "__main__":
    run_dev_test()