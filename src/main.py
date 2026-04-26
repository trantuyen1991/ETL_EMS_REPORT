# -*- coding: utf-8 -*-

import re
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
from src.services.pdf_service import PDFService

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
    anchor_date = period_service.resolve_anchor_date_from_config(config)
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
        "anchor_date": anchor_date,
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
        raw_rows=rows,
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
        "anchor_date": getattr(period, "anchor_date", None),
        "previous_anchor_date": getattr(period, "previous_anchor_date", None),
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


def _select_template_bundle(period_type: str) -> dict[str, str]:
    """Choose template files based on report family."""
    normalized = str(period_type or "").strip().lower()

    if normalized == "daily":
        return {
            "view": "report/view/report_view_daily.html",
            "pdf": "report/pdf/report_pdf_daily.html",
        }

    return {
        "view": "report/view/report_view_periodic.html",
        "pdf": "report/pdf/report_pdf_periodic.html",
    }


def _sanitize_filename_part(value: str) -> str:
    """Convert free text into a file-safe lowercase token."""
    sanitized = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_")
    return sanitized.lower() or "report"


def _resolve_report_filename_base(env_cfg: dict[str, Any]) -> str:
    """Resolve base filename from env config."""
    raw_value = env_cfg.get("REPORT_FILENAME") or env_cfg.get("FILE_NAME_PREFIX") or "report"
    return _sanitize_filename_part(str(raw_value))


def _build_report_export_stem(env_cfg: dict[str, Any], period) -> str:
    """Build export filename stem as <filename>_<period>_<date>."""
    base_name = _resolve_report_filename_base(env_cfg)
    anchor_value = getattr(period, "anchor_date", None) or period.end_date
    return f"{base_name}_{period.period_type}_{anchor_value.strftime('%Y%m%d')}"


def _path_contains_hidden_segment(path: Path) -> bool:
    """Return True when any path segment is hidden like `.openclaw`."""
    return any(part.startswith(".") for part in path.parts if part not in ("", ".", ".."))


def _resolve_pdf_staging_dir(
    env_cfg: dict[str, Any],
    project_output_dir: Path,
) -> Path:
    """Resolve a Chromium-safe staging directory for HTML-to-PDF printing."""
    configured_staging = str(env_cfg.get("PRINT_STAGING_DIR") or "").strip()
    if configured_staging:
        return Path(configured_staging)

    configured_output = str(env_cfg.get("OUTPUT_DIR") or "").strip()
    if configured_output:
        output_dir = Path(configured_output)
        if not _path_contains_hidden_segment(output_dir):
            return output_dir

    if not _path_contains_hidden_segment(project_output_dir):
        return project_output_dir

    return Path.home() / "Reports"


def _render_report_artifacts(
    *,
    renderer: TemplateRenderingService,
    pdf_service,
    env_cfg: dict[str, Any],
    period,
    report_context: dict[str, Any],
    project_output_dir: Path,
    staging_output_dir: Path,
) -> dict[str, Path]:
    """Render one report into view HTML, PDF source HTML, and PDF."""
    template_bundle = _select_template_bundle(period.period_type)
    export_stem = _build_report_export_stem(env_cfg, period)

    view_html = renderer.render(template_bundle["view"], report_context)
    pdf_html = renderer.render(template_bundle["pdf"], report_context)

    view_path = project_output_dir / f"{export_stem}_view.html"
    pdf_source_path = project_output_dir / f"{export_stem}_pdf_source.html"
    staging_html_path = staging_output_dir / f"{export_stem}_pdf_source.html"
    final_pdf_path = project_output_dir / f"{export_stem}.pdf"
    staging_pdf_path = staging_output_dir / f"{export_stem}.pdf"

    view_path.write_text(view_html, encoding="utf-8")
    pdf_source_path.write_text(pdf_html, encoding="utf-8")
    staging_html_path.write_text(pdf_html, encoding="utf-8")

    pdf_service.export(staging_html_path, staging_pdf_path)
    final_pdf_path.write_bytes(staging_pdf_path.read_bytes())

    return {
        "view_html": view_path,
        "pdf_source_html": pdf_source_path,
        "pdf": final_pdf_path,
        "staging_html": staging_html_path,
        "staging_pdf": staging_pdf_path,
    }


def _run_report_batch(runtime: dict[str, Any]) -> list[dict[str, Any]]:
    """Render all reports scheduled for the effective anchor day."""
    config = runtime["config"]
    env_cfg = runtime["env_cfg"]
    repos = runtime["repos"]
    client = runtime["client"]
    logger = runtime["logger"]

    period_service = PeriodService()
    scheduled_periods = period_service.resolve_scheduled_periods_from_config(config=config)

    renderer = TemplateRenderingService("src/templates")
    pdf_service = PDFService(config)

    project_output_dir = Path("output/reports")
    project_output_dir.mkdir(parents=True, exist_ok=True)

    staging_output_dir = _resolve_pdf_staging_dir(
        env_cfg=env_cfg,
        project_output_dir=project_output_dir,
    )
    staging_output_dir.mkdir(parents=True, exist_ok=True)

    rendered_reports: list[dict[str, Any]] = []

    for period in scheduled_periods:
        kpi_object = _build_kpi_object(repos, period)
        utility_object = _build_utility_object(
            repos=repos,
            period=period,
            client=client,
        )
        energy_object = _build_energy_object(repos, period, kpi_object)

        report_context = _build_report_context(
            env_cfg=env_cfg,
            period=period,
            energy_object=energy_object,
            kpi_object=kpi_object,
            utility_object=utility_object,
            client=client,
        )

        artifacts = _render_report_artifacts(
            renderer=renderer,
            pdf_service=pdf_service,
            env_cfg=env_cfg,
            period=period,
            report_context=report_context,
            project_output_dir=project_output_dir,
            staging_output_dir=staging_output_dir,
        )

        rendered_reports.append({
            "period": period,
            "artifacts": artifacts,
        })

        logger.info(
            "Rendered scheduled report | period_type=%s anchor_date=%s pdf=%s",
            period.period_type,
            getattr(period, "anchor_date", None),
            artifacts["pdf"],
        )

    return rendered_reports


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

    html = renderer.render(_select_template_bundle(period.period_type)["view"], report_context)

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
    runtime = _bootstrap()
    rendered_reports = _run_report_batch(runtime)

    runtime["logger"].info(
        "Scheduled production run completed. report_count=%s periods=%s",
        len(rendered_reports),
        [item["period"].period_type for item in rendered_reports],
    )


if __name__ == "__main__":
    run_production()
