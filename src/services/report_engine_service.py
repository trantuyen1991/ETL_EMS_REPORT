# -*- coding: utf-8 -*-
"""Shared report-engine entry points for CLI and future Web GUI.

This module keeps heavy ETL/report logic outside route handlers while also
providing a reusable execution path for the existing batch CLI entrypoint.
"""

from __future__ import annotations

import re
import tempfile
import time
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from threading import RLock
from typing import Any, Iterator, Optional

from src.config.config_loader import load_config
from src.config.data_sources import get_data_sources
from src.config.utility_metadata import get_utility_sensor_metadata
from src.db.mysql_client import MySQLClient, MySQLConfig
from src.db.processvalue_repository import ProcessValueRepository
from src.db.queries import EnergyDataRepository
from src.models.period_models import PeriodRequest, ResolvedPeriod
from src.services.energy_service import EnergyService
from src.services.excel_export_service import ExcelExportService
from src.services.kpi_service import KPIService
from src.services.pdf_service import PDFService
from src.services.period_service import PeriodService
from src.services.processvalue_service import ProcessValueService
from src.services.report_builder_service import ReportBuilderService
from src.services.report_snapshot_service import ReportSnapshotService
from src.services.style_service import ReportStyleService
from src.services.template_service import TemplateRenderingService
from src.services.utility_service import UtilityService
from src.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


class ReportRequestError(ValueError):
    """Raised when a browser/API report request is invalid."""


@dataclass(frozen=True)
class ReportRenderResult:
    """Simple render result for browser-facing report generation."""

    period: ResolvedPeriod
    report_context: dict[str, Any]
    html: str
    template_mode: str


@dataclass(frozen=True)
class MemoryCacheEntry:
    """Simple in-memory cache entry with creation timestamp."""

    created_at: float
    value: Any


class ReportEngineService:
    """Provide shared report rendering entry points for batch and web surfaces."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root
        self.period_service = PeriodService()
        self.preview_cache_ttl_seconds = 300.0
        self._preview_context_cache: dict[str, MemoryCacheEntry] = {}
        self._preview_html_cache: dict[str, MemoryCacheEntry] = {}
        self._cache_lock = RLock()
        self._period_artifact_locks: dict[str, RLock] = {}
        self._period_artifact_locks_guard = RLock()

    def bootstrap_runtime(self) -> dict[str, Any]:
        """Bootstrap runtime objects for report generation."""
        project_root = self.project_root or Path(__file__).resolve().parent.parent.parent

        setup_logging(
            logging_config_path=project_root / "config" / "logging.yaml",
            log_file_path=project_root / "logs" / "app.log",
        )

        runtime_logger = get_logger(__name__)
        runtime_logger.info("=== REPORT RUN STARTED ===")

        config = self.load_runtime_config(project_root=project_root)
        env_cfg = config["env"]

        mysql_config = MySQLConfig(
            host=env_cfg["MYSQL_HOST"],
            port=int(env_cfg["MYSQL_PORT"]),
            database=env_cfg["MYSQL_DATABASE"],
            user=env_cfg["MYSQL_USER"],
            password=env_cfg["MYSQL_PASSWORD"],
        )

        client = MySQLClient(mysql_config)
        sources = get_data_sources(database=mysql_config.database)
        repos = {
            name: EnergyDataRepository(client, cfg)
            for name, cfg in sources.items()
        }

        return {
            "project_root": project_root,
            "logger": runtime_logger,
            "config": config,
            "env_cfg": env_cfg,
            "client": client,
            "repos": repos,
        }

    def close_runtime(self, runtime: dict[str, Any] | None) -> None:
        """Close DB resources for one runtime safely."""
        if not runtime:
            return

        client = runtime.get("client")
        close_fn = getattr(client, "close", None)
        if callable(close_fn):
            close_fn()

    def load_runtime_config(self, project_root: Path | None = None) -> dict[str, Any]:
        """Load config only, without opening DB connections."""
        resolved_root = project_root or self.project_root or Path(__file__).resolve().parent.parent.parent
        return load_config(
            env_path=resolved_root / "config" / ".env",
            yaml_path=resolved_root / "config" / "app.yaml",
        )

    def resolve_request_period(
        self,
        runtime: dict[str, Any],
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
    ) -> ResolvedPeriod:
        """Resolve one browser/API request into the canonical period object."""
        config = runtime.get("config") or {}
        return self.resolve_request_period_from_config(
            config,
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )

    def resolve_request_period_from_config(
        self,
        config: dict[str, Any],
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
    ) -> ResolvedPeriod:
        """Resolve one browser/API request using config only, without DB runtime."""
        normalized_period_type = str(period_type or "").strip().lower()

        if not normalized_period_type:
            return self.period_service.resolve_from_config(config=config)

        if normalized_period_type not in {"daily", "weekly", "monthly", "custom"}:
            raise ReportRequestError(
                "period_type must be one of: daily, weekly, monthly, custom."
            )

        if normalized_period_type == "custom":
            custom_start_date = self._parse_required_date(start_date_text, "start_date")
            custom_end_date = self._parse_required_date(end_date_text, "end_date")

            if custom_start_date > custom_end_date:
                raise ReportRequestError("start_date must be <= end_date.")

            total_days = (custom_end_date - custom_start_date).days + 1
            if total_days > 31:
                raise ReportRequestError("custom date range must be 31 days or fewer.")

            request = PeriodRequest(
                period_type="custom",
                custom_start_date=custom_start_date,
                custom_end_date=custom_end_date,
            )
            return self.period_service.resolve(request=request, today=custom_end_date)

        anchor_date = self._parse_optional_date(anchor_date_text)
        if anchor_date is None:
            anchor_date = self.period_service.resolve_anchor_date_from_config(config=config)

        request = PeriodRequest(
            period_type=normalized_period_type,  # type: ignore[arg-type]
            anchor_date=anchor_date,
        )
        return self.period_service.resolve(request=request, today=anchor_date)

    def render_view_report(
        self,
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
    ) -> ReportRenderResult:
        """Render one report HTML view for browser delivery."""
        return self.render_report_surface(
            template_mode="view",
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )

    def render_report_surface(
        self,
        *,
        template_mode: str = "view",
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
        force_refresh: bool = False,
    ) -> ReportRenderResult:
        """Render one selected report surface for browser delivery."""
        project_root = self.project_root or Path(__file__).resolve().parent.parent.parent
        config = self.load_runtime_config(project_root=project_root)
        period = self.resolve_request_period_from_config(
            config,
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )
        normalized_template_mode = self._normalize_template_mode(template_mode)
        render_mode = "pdf" if normalized_template_mode == "pdf_source" else "html"
        cache_fingerprint = self._build_preview_cache_fingerprint(
            project_root=project_root,
            period=period,
        )
        context_cache_key = self._build_preview_context_cache_key(
            period=period,
            render_mode=render_mode,
            cache_fingerprint=cache_fingerprint,
        )
        html_cache_key = self._build_preview_html_cache_key(
            period=period,
            template_mode=normalized_template_mode,
            cache_fingerprint=cache_fingerprint,
        )

        cached_context = None if force_refresh else self._get_memory_cache_value(
            self._preview_context_cache,
            context_cache_key,
        )
        cached_html = None if force_refresh else self._get_memory_cache_value(
            self._preview_html_cache,
            html_cache_key,
        )

        if cached_context is not None and cached_html is not None:
            logger.info(
                "Served Web GUI report HTML from warm cache | template_mode=%s period_type=%s start_date=%s end_date=%s",
                normalized_template_mode,
                period.period_type,
                period.start_date,
                period.end_date,
            )
            return ReportRenderResult(
                period=period,
                report_context=cached_context,
                html=cached_html,
                template_mode=normalized_template_mode,
            )

        template_bundle = self._select_template_bundle(period.period_type)
        template_name = template_bundle["pdf"] if normalized_template_mode == "pdf_source" else template_bundle["view"]

        if cached_context is not None:
            renderer = TemplateRenderingService("src/templates")
            html = renderer.render(template_name, cached_context)
            self._set_memory_cache_value(
                self._preview_html_cache,
                html_cache_key,
                html,
            )
            logger.info(
                "Rendered Web GUI report HTML from warm context cache | template_mode=%s period_type=%s start_date=%s end_date=%s",
                normalized_template_mode,
                period.period_type,
                period.start_date,
                period.end_date,
            )
            return ReportRenderResult(
                period=period,
                report_context=cached_context,
                html=html,
                template_mode=normalized_template_mode,
            )

        runtime: dict[str, Any] | None = None

        try:
            runtime = self.bootstrap_runtime()
            report_context = self.build_report_context(
                runtime=runtime,
                period=period,
                render_mode=render_mode,
            )
            renderer = TemplateRenderingService("src/templates")
            html = renderer.render(template_name, report_context)

            self._set_memory_cache_value(
                self._preview_context_cache,
                context_cache_key,
                report_context,
            )
            self._set_memory_cache_value(
                self._preview_html_cache,
                html_cache_key,
                html,
            )

            logger.info(
                "Rendered Web GUI report HTML | template_mode=%s period_type=%s start_date=%s end_date=%s force_refresh=%s",
                normalized_template_mode,
                period.period_type,
                period.start_date,
                period.end_date,
                force_refresh,
            )

            return ReportRenderResult(
                period=period,
                report_context=report_context,
                html=html,
                template_mode=normalized_template_mode,
            )
        finally:
            self.close_runtime(runtime)

    def build_report_snapshot(
        self,
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Return one machine-facing report snapshot for the selected period."""
        project_root = self.project_root or Path(__file__).resolve().parent.parent.parent
        config = self.load_runtime_config(project_root=project_root)
        period = self.resolve_request_period_from_config(
            config,
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )
        cache_fingerprint = self._build_preview_cache_fingerprint(
            project_root=project_root,
            period=period,
        )
        context_cache_key = self._build_preview_context_cache_key(
            period=period,
            render_mode="html",
            cache_fingerprint=cache_fingerprint,
        )

        report_context = None if force_refresh else self._get_memory_cache_value(
            self._preview_context_cache,
            context_cache_key,
        )
        cache_hit = report_context is not None

        if report_context is None:
            runtime: dict[str, Any] | None = None
            try:
                runtime = self.bootstrap_runtime()
                report_context = self.build_report_context(
                    runtime=runtime,
                    period=period,
                    render_mode="html",
                )
                self._set_memory_cache_value(
                    self._preview_context_cache,
                    context_cache_key,
                    report_context,
                )
            finally:
                self.close_runtime(runtime)

        snapshot_service = ReportSnapshotService()
        snapshot = snapshot_service.build_snapshot(
            period=period,
            report_context=report_context,
            cache_hit=cache_hit,
            cache_fingerprint=cache_fingerprint,
        )
        logger.info(
            "Built Web GUI report snapshot | period_type=%s start_date=%s end_date=%s cache_hit=%s force_refresh=%s",
            period.period_type,
            period.start_date,
            period.end_date,
            cache_hit,
            force_refresh,
        )
        return snapshot

    def build_report_pdf_preview(
        self,
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
        force_refresh: bool = False,
    ) -> Path:
        """Return one real rendered PDF path for browser preview."""
        config = self.load_runtime_config()
        env_cfg = config.get("env") or {}
        project_root = self.project_root or Path(__file__).resolve().parent.parent.parent
        period = self.resolve_request_period_from_config(
            config,
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )

        canonical_output_root = self._resolve_canonical_output_root(
            env_cfg=env_cfg,
            project_root=project_root,
        )
        month_dir = self._resolve_monthly_report_dir(canonical_output_root, period)
        export_stem = self._build_report_export_stem(env_cfg, period)
        pdf_path = month_dir / "pdf" / f"{export_stem}.pdf"
        lock_key = self._build_period_artifact_lock_key(period=period)

        logger.info(
            "Preview PDF request received | lock_key=%s period_type=%s force_refresh=%s pdf_exists=%s pdf_path=%s",
            lock_key,
            period.period_type,
            force_refresh,
            pdf_path.exists(),
            pdf_path,
        )

        with self._acquire_period_artifact_lock(period, scope="preview-pdf"):
            if not force_refresh and pdf_path.exists():
                logger.info(
                    "Reused existing preview PDF | lock_key=%s period_type=%s pdf_path=%s",
                    lock_key,
                    period.period_type,
                    pdf_path,
                )
                return pdf_path

            if force_refresh and pdf_path.exists():
                logger.info(
                    "Preview PDF force refresh requested, rebuilding artifact | lock_key=%s pdf_path=%s",
                    lock_key,
                    pdf_path,
                )
            else:
                logger.info(
                    "Preview PDF artifact missing, building on demand | lock_key=%s pdf_path=%s",
                    lock_key,
                    pdf_path,
                )

            artifacts = self.render_period_package(period=period)
            final_pdf_path = artifacts.get("pdf")
            if not isinstance(final_pdf_path, Path) or not final_pdf_path.exists():
                raise FileNotFoundError("Failed to build preview PDF artifact.")

            logger.info(
                "Built preview PDF on demand | lock_key=%s period_type=%s pdf_path=%s force_refresh=%s",
                lock_key,
                period.period_type,
                final_pdf_path,
                force_refresh,
            )
            return final_pdf_path

    def build_report_package_zip(
        self,
        *,
        period_type: str | None = None,
        anchor_date_text: str | None = None,
        start_date_text: str | None = None,
        end_date_text: str | None = None,
    ) -> Path:
        """Package one built report month folder into a ZIP file for download."""
        config = self.load_runtime_config()
        env_cfg = config.get("env") or {}
        project_root = self.project_root or Path(__file__).resolve().parent.parent.parent
        period = self.resolve_request_period_from_config(
            config,
            period_type=period_type,
            anchor_date_text=anchor_date_text,
            start_date_text=start_date_text,
            end_date_text=end_date_text,
        )

        canonical_output_root = self._resolve_canonical_output_root(
            env_cfg=env_cfg,
            project_root=project_root,
        )
        month_dir = self._resolve_monthly_report_dir(canonical_output_root, period)
        downloads_dir = canonical_output_root / "_downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        zip_path = downloads_dir / f"{month_dir.name}_report_package.zip"
        lock_key = self._build_period_artifact_lock_key(period=period)

        logger.info(
            "Report ZIP request received | lock_key=%s period_type=%s month_dir_exists=%s zip_exists=%s zip_path=%s",
            lock_key,
            period.period_type,
            month_dir.exists() and month_dir.is_dir(),
            zip_path.exists(),
            zip_path,
        )

        with self._acquire_period_artifact_lock(period, scope="download-zip"):
            if not month_dir.exists() or not month_dir.is_dir():
                logger.info(
                    "Report month directory missing, rendering package before ZIP build | lock_key=%s month_dir=%s",
                    lock_key,
                    month_dir,
                )
                self.render_period_package(period=period)

            if not month_dir.exists() or not month_dir.is_dir():
                raise FileNotFoundError(
                    f"Built report package not found for {month_dir.name}."
                )

            if self._is_zip_artifact_fresh(zip_path=zip_path, source_dir=month_dir):
                logger.info(
                    "Reused fresh report package ZIP | lock_key=%s period_type=%s month_dir=%s zip_path=%s",
                    lock_key,
                    period.period_type,
                    month_dir,
                    zip_path,
                )
                return zip_path

            if zip_path.exists():
                logger.info(
                    "Existing report ZIP is stale, rebuilding | lock_key=%s month_dir=%s zip_path=%s",
                    lock_key,
                    month_dir,
                    zip_path,
                )
            else:
                logger.info(
                    "Report ZIP artifact missing, building on demand | lock_key=%s month_dir=%s zip_path=%s",
                    lock_key,
                    month_dir,
                    zip_path,
                )

            temp_zip_path = self._build_temp_output_path(zip_path)
            try:
                with zipfile.ZipFile(temp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
                    for path in sorted(month_dir.rglob("*")):
                        if not path.is_file():
                            continue
                        zip_file.write(path, arcname=path.relative_to(month_dir.parent))
                temp_zip_path.replace(zip_path)
            finally:
                if temp_zip_path.exists():
                    temp_zip_path.unlink(missing_ok=True)

            logger.info(
                "Prepared report package ZIP | lock_key=%s period_type=%s month_dir=%s zip_path=%s",
                lock_key,
                period.period_type,
                month_dir,
                zip_path,
            )
            return zip_path

    def run_scheduled_batch(self, runtime: dict[str, Any]) -> list[dict[str, Any]]:
        """Render all reports scheduled for the effective anchor day."""
        config = runtime["config"]
        env_cfg = runtime["env_cfg"]
        logger_obj = runtime["logger"]

        scheduled_periods = self.period_service.resolve_scheduled_periods_from_config(config=config)

        renderer = TemplateRenderingService("src/templates")
        pdf_service = PDFService(config)
        excel_service = ExcelExportService()

        canonical_output_root = self._resolve_canonical_output_root(
            env_cfg=env_cfg,
            project_root=runtime["project_root"],
        )
        canonical_output_root.mkdir(parents=True, exist_ok=True)

        staging_output_dir = self._resolve_pdf_staging_dir(
            env_cfg=env_cfg,
            canonical_output_root=canonical_output_root,
            project_root=runtime["project_root"],
        )
        staging_output_dir.mkdir(parents=True, exist_ok=True)

        rendered_reports: list[dict[str, Any]] = []

        for period in scheduled_periods:
            report_context = self.build_report_context(runtime=runtime, period=period)
            artifacts = self._render_report_artifacts(
                renderer=renderer,
                pdf_service=pdf_service,
                excel_service=excel_service,
                env_cfg=env_cfg,
                period=period,
                report_context=report_context,
                canonical_output_root=canonical_output_root,
                staging_output_dir=staging_output_dir,
            )

            rendered_reports.append({
                "period": period,
                "artifacts": artifacts,
            })

            logger_obj.info(
                "Rendered scheduled report | period_type=%s anchor_date=%s pdf=%s",
                period.period_type,
                getattr(period, "anchor_date", None),
                artifacts["pdf"],
            )

        batch_paths = self._collect_report_batch_artifacts(rendered_reports=rendered_reports)

        self._cleanup_output_artifacts(
            rendered_reports=rendered_reports,
            canonical_output_root=canonical_output_root,
            staging_output_dir=staging_output_dir,
            logger_obj=logger_obj,
        )

        logger_obj.info(
            "Collected current report batch artifacts | canonical_output_root=%s staging_output_dir=%s file_count=%s",
            canonical_output_root,
            staging_output_dir,
            len(batch_paths),
        )

        return rendered_reports

    def run_production(self) -> None:
        """Run the production batch flow while preserving the current CLI entrypoint."""
        runtime: dict[str, Any] | None = None
        try:
            runtime = self.bootstrap_runtime()
            rendered_reports = self.run_scheduled_batch(runtime)
            runtime["logger"].info(
                "Scheduled production run completed. report_count=%s periods=%s",
                len(rendered_reports),
                [item["period"].period_type for item in rendered_reports],
            )
        finally:
            self.close_runtime(runtime)

    def render_period_package(self, *, period: ResolvedPeriod) -> dict[str, Path]:
        """Render one requested period into the canonical output structure on demand."""
        runtime: dict[str, Any] | None = None
        period_lock_key = self._build_period_artifact_lock_key(period=period)
        logger.info(
            "Starting on-demand report package render | lock_key=%s period_type=%s start_date=%s end_date=%s",
            period_lock_key,
            period.period_type,
            period.start_date,
            period.end_date,
        )
        try:
            runtime = self.bootstrap_runtime()
            renderer = TemplateRenderingService("src/templates")
            pdf_service = PDFService(runtime["config"])
            excel_service = ExcelExportService()

            canonical_output_root = self._resolve_canonical_output_root(
                env_cfg=runtime["env_cfg"],
                project_root=runtime["project_root"],
            )
            canonical_output_root.mkdir(parents=True, exist_ok=True)

            staging_output_dir = self._resolve_pdf_staging_dir(
                env_cfg=runtime["env_cfg"],
                canonical_output_root=canonical_output_root,
                project_root=runtime["project_root"],
            )
            staging_output_dir.mkdir(parents=True, exist_ok=True)

            report_context = self.build_report_context(runtime=runtime, period=period)
            artifacts = self._render_report_artifacts(
                renderer=renderer,
                pdf_service=pdf_service,
                excel_service=excel_service,
                env_cfg=runtime["env_cfg"],
                period=period,
                report_context=report_context,
                canonical_output_root=canonical_output_root,
                staging_output_dir=staging_output_dir,
            )

            self._cleanup_output_artifacts(
                rendered_reports=[{"period": period, "artifacts": artifacts}],
                canonical_output_root=canonical_output_root,
                staging_output_dir=staging_output_dir,
                logger_obj=runtime["logger"],
            )

            runtime["logger"].info(
                "Rendered on-demand report package | lock_key=%s period_type=%s anchor_date=%s month_dir=%s",
                period_lock_key,
                period.period_type,
                getattr(period, "anchor_date", None),
                self._resolve_monthly_report_dir(canonical_output_root, period),
            )
            return artifacts
        finally:
            self.close_runtime(runtime)

    def build_report_context(
        self,
        *,
        runtime: dict[str, Any],
        period: ResolvedPeriod,
        render_mode: str = "html",
    ) -> dict[str, Any]:
        """Build one reusable report context for the requested period."""
        repos = runtime["repos"]
        client = runtime["client"]
        config = runtime["config"]
        env_cfg = runtime["env_cfg"]
        project_root = runtime["project_root"]
        report_timezone = self._resolve_report_timezone(config)

        kpi_object = self._build_kpi_object(repos, period)
        utility_object = self._build_utility_object(
            repos=repos,
            period=period,
            client=client,
            report_timezone=report_timezone,
        )
        energy_object = self._build_energy_object(repos, period)

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

        style_service = ReportStyleService(project_root / "config" / "report_style.json")
        style_context = style_service.build_render_context()

        report_context = report_builder.build_report_context_v3(
            meta=meta,
            period=period_info,
            energy_object=energy_object,
            kpi_object=kpi_object,
            utility_object=utility_object,
            mode=render_mode,
            style_config=style_context.get("report_style"),
        )
        report_context.update(style_context)
        return report_context

    def _build_kpi_object(
        self,
        repos: dict[str, EnergyDataRepository],
        period: ResolvedPeriod,
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
        return kpi_service.build_full_kpi_object(
            current_rows=current_rows,
            previous_rows=previous_rows,
            report_start=period.start_date,
            report_end=period.end_date,
            previous_start=period.previous_start_date,
            previous_end=period.previous_end_date,
        )

    def _build_sensor_monitoring_context(
        self,
        client: MySQLClient,
        report_start: date,
        report_end: date,
        report_timezone: str,
    ) -> dict[str, Any]:
        """Build utility sensor monitoring context for a report period."""
        sensor_metadata = get_utility_sensor_metadata()
        sensor_columns = list(sensor_metadata.keys())

        repo = ProcessValueRepository(
            mysql_client=client,
            source_timezone="UTC",
            target_timezone=report_timezone,
        )
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

        return utility_service.build_sensor_monitoring_context(
            daily_stats=daily_stats,
            report_start=report_start,
            report_end=report_end,
            raw_rows=rows,
        )

    def _build_utility_object(
        self,
        repos: dict[str, EnergyDataRepository],
        period: ResolvedPeriod,
        client: MySQLClient,
        report_timezone: str,
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

        current_sensor_monitoring = self._build_sensor_monitoring_context(
            client=client,
            report_start=period.start_date,
            report_end=period.end_date,
            report_timezone=report_timezone,
        )
        previous_sensor_monitoring = self._build_sensor_monitoring_context(
            client=client,
            report_start=period.previous_start_date,
            report_end=period.previous_end_date,
            report_timezone=report_timezone,
        )

        utility_service = UtilityService()
        return utility_service.build_full_utility_object(
            current_rows=current_rows,
            previous_rows=previous_rows,
            report_start=period.start_date,
            report_end=period.end_date,
            previous_start=period.previous_start_date,
            previous_end=period.previous_end_date,
            current_sensor_monitoring=current_sensor_monitoring,
            previous_sensor_monitoring=previous_sensor_monitoring,
        )

    def _build_energy_object(
        self,
        repos: dict[str, EnergyDataRepository],
        period: ResolvedPeriod,
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
        current_total_energy_rows = repos["total_energy"].get_daily_detail_rows(
            start_date=period.start_date,
            end_date=period.end_date,
        )
        previous_total_energy_rows = repos["total_energy"].get_daily_detail_rows(
            start_date=period.previous_start_date,
            end_date=period.previous_end_date,
        )
        current_area_columns = {
            "diode": repos["diode_energy"].get_meter_columns(),
            "ico": repos["ico_energy"].get_meter_columns(),
            "sakari": repos["sakari_energy"].get_meter_columns(),
        }

        return energy_service.build_full_energy_object(
            current_area_rows=current_area_rows,
            previous_area_rows=previous_area_rows,
            current_area_columns=current_area_columns,
            previous_area_columns=current_area_columns,
            current_total_energy_rows=current_total_energy_rows,
            previous_total_energy_rows=previous_total_energy_rows,
            report_start=period.start_date,
            report_end=period.end_date,
            previous_start=period.previous_start_date,
            previous_end=period.previous_end_date,
        )

    def _select_template_bundle(self, period_type: str) -> dict[str, str]:
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

    def _normalize_template_mode(self, template_mode: str | None) -> str:
        """Normalize browser template surface selection."""
        normalized = str(template_mode or "view").strip().lower() or "view"
        if normalized not in {"view", "pdf_source"}:
            raise ReportRequestError(
                "template_mode must be one of: view, pdf_source."
            )
        return normalized

    def _sanitize_filename_part(self, value: str) -> str:
        """Convert free text into a file-safe lowercase token."""
        sanitized = re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_")
        return sanitized.lower() or "report"

    def _resolve_report_filename_base(self, env_cfg: dict[str, Any]) -> str:
        """Resolve base filename from env config."""
        raw_value = env_cfg.get("REPORT_FILENAME") or env_cfg.get("FILE_NAME_PREFIX") or "report"
        return self._sanitize_filename_part(str(raw_value))

    def _resolve_period_sort_prefix(self, period_type: str) -> str:
        """Resolve the sort prefix for canonical report filenames."""
        normalized = str(period_type or "").strip().lower()
        mapping = {
            "monthly": "01",
            "weekly": "02",
            "daily": "03",
        }
        return mapping.get(normalized, "99")

    def _resolve_report_anchor_value(self, period: ResolvedPeriod):
        """Resolve the canonical anchor date for report naming and monthly grouping."""
        return getattr(period, "anchor_date", None) or period.end_date

    def _build_report_export_stem(self, env_cfg: dict[str, Any], period: ResolvedPeriod) -> str:
        """Build export filename stem as <sort-prefix>_<period>_<filename>_<date>."""
        base_name = self._resolve_report_filename_base(env_cfg)
        anchor_value = self._resolve_report_anchor_value(period)
        period_prefix = self._resolve_period_sort_prefix(period.period_type)
        return f"{period_prefix}_{period.period_type}_{base_name}_{anchor_value.strftime('%Y%m%d')}"

    def _path_contains_hidden_segment(self, path: Path) -> bool:
        """Return True when any path segment is hidden like `.openclaw`."""
        return any(part.startswith(".") for part in path.parts if part not in ("", ".", ".."))

    def _normalize_runtime_path(self, raw_path: str, project_root: Path) -> Path:
        """Normalize one configured path, resolving relative paths from the project root."""
        normalized = Path(raw_path).expanduser()
        if normalized.is_absolute():
            return normalized
        return project_root / normalized

    def _resolve_canonical_output_root(
        self,
        env_cfg: dict[str, Any],
        project_root: Path,
    ) -> Path:
        """Resolve the final month-grouped report output root."""
        configured_output = str(env_cfg.get("OUTPUT_DIR") or "").strip()
        if configured_output:
            return self._normalize_runtime_path(configured_output, project_root)
        return project_root / "output" / "reports"

    def _resolve_pdf_staging_dir(
        self,
        env_cfg: dict[str, Any],
        canonical_output_root: Path,
        project_root: Path,
    ) -> Path:
        """Resolve a Chromium-safe staging directory for HTML-to-PDF printing."""
        configured_staging = str(env_cfg.get("PRINT_STAGING_DIR") or "").strip()
        if configured_staging:
            return self._normalize_runtime_path(configured_staging, project_root)

        if not self._path_contains_hidden_segment(canonical_output_root):
            return canonical_output_root / "_staging"

        project_fallback = project_root / "output" / "reports" / "_staging"
        if not self._path_contains_hidden_segment(project_fallback):
            return project_fallback

        return Path.home() / "Reports" / "_staging"

    def _resolve_monthly_report_dir(
        self,
        canonical_output_root: Path,
        period: ResolvedPeriod,
    ) -> Path:
        """Resolve the canonical month directory for one report anchor."""
        anchor_value = self._resolve_report_anchor_value(period)
        return canonical_output_root / anchor_value.strftime("%Y_%m")

    def _build_preview_cache_fingerprint(
        self,
        *,
        project_root: Path,
        period: ResolvedPeriod,
    ) -> str:
        """Build a lightweight version fingerprint for preview-cache safety."""
        template_bundle = self._select_template_bundle(period.period_type)
        tracked_paths = [
            project_root / "config" / "app.yaml",
            project_root / "config" / "report_style.json",
            project_root / "src" / "services" / "report_builder_service.py",
            project_root / "src" / "templates" / template_bundle["view"],
            project_root / "src" / "templates" / template_bundle["pdf"],
        ]
        parts: list[str] = []
        for path in tracked_paths:
            try:
                parts.append(f"{path.name}:{path.stat().st_mtime_ns}")
            except FileNotFoundError:
                parts.append(f"{path.name}:missing")
        return "|".join(parts)

    def _build_preview_context_cache_key(
        self,
        *,
        period: ResolvedPeriod,
        render_mode: str,
        cache_fingerprint: str,
    ) -> str:
        """Build one cache key for reusable report context."""
        anchor_date = getattr(period, "anchor_date", None)
        return "|".join([
            "context",
            str(period.period_type),
            str(anchor_date.isoformat() if anchor_date else ""),
            str(period.start_date.isoformat()),
            str(period.end_date.isoformat()),
            str(render_mode),
            cache_fingerprint,
        ])

    def _build_preview_html_cache_key(
        self,
        *,
        period: ResolvedPeriod,
        template_mode: str,
        cache_fingerprint: str,
    ) -> str:
        """Build one cache key for rendered preview HTML."""
        anchor_date = getattr(period, "anchor_date", None)
        return "|".join([
            "html",
            str(period.period_type),
            str(anchor_date.isoformat() if anchor_date else ""),
            str(period.start_date.isoformat()),
            str(period.end_date.isoformat()),
            str(template_mode),
            cache_fingerprint,
        ])

    def _build_period_artifact_lock_key(
        self,
        *,
        period: ResolvedPeriod,
    ) -> str:
        """Build one lock key for period-scoped artifact generation."""
        anchor_date = getattr(period, "anchor_date", None)
        return "|".join([
            str(period.period_type),
            str(anchor_date.isoformat() if anchor_date else ""),
            str(period.start_date.isoformat()),
            str(period.end_date.isoformat()),
        ])

    def _build_unique_staging_path(
        self,
        staging_output_dir: Path,
        stem: str,
        suffix: str,
    ) -> Path:
        """Build a unique staging path so concurrent workers never share temp files."""
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", str(stem)).strip("._") or "artifact"
        return staging_output_dir / f"{safe_stem}_{time.time_ns()}{suffix}"

    def _build_temp_output_path(self, final_path: Path) -> Path:
        """Build a unique temp file path in the same directory for atomic replace."""
        final_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = tempfile.NamedTemporaryFile(
            dir=str(final_path.parent),
            prefix=f".{final_path.stem}.",
            suffix=f"{final_path.suffix}.tmp",
            delete=False,
        )
        temp_name = temp_file.name
        temp_file.close()
        return Path(temp_name)

    def _atomic_write_text(self, target_path: Path, content: str, *, encoding: str = "utf-8") -> None:
        """Write text via temp file then atomically replace the final path."""
        temp_path = self._build_temp_output_path(target_path)
        try:
            temp_path.write_text(content, encoding=encoding)
            temp_path.replace(target_path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _atomic_write_bytes(self, target_path: Path, content: bytes) -> None:
        """Write bytes via temp file then atomically replace the final path."""
        temp_path = self._build_temp_output_path(target_path)
        try:
            temp_path.write_bytes(content)
            temp_path.replace(target_path)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @contextmanager
    def _acquire_period_artifact_lock(
        self,
        period: ResolvedPeriod,
        *,
        scope: str,
    ) -> Iterator[None]:
        """Serialize on-demand artifact work per resolved period."""
        lock_key = self._build_period_artifact_lock_key(period=period)
        with self._period_artifact_locks_guard:
            lock = self._period_artifact_locks.get(lock_key)
            if lock is None:
                lock = RLock()
                self._period_artifact_locks[lock_key] = lock

        acquired_immediately = lock.acquire(blocking=False)
        if acquired_immediately:
            lock.release()
            logger.info(
                "Period artifact lock available immediately | scope=%s lock_key=%s",
                scope,
                lock_key,
            )
        else:
            logger.info(
                "Period artifact lock busy, waiting | scope=%s lock_key=%s",
                scope,
                lock_key,
            )

        with lock:
            logger.info(
                "Acquired period artifact lock | scope=%s lock_key=%s",
                scope,
                lock_key,
            )
            yield

    def _get_memory_cache_value(
        self,
        cache_store: dict[str, MemoryCacheEntry],
        cache_key: str,
    ) -> Any:
        """Return cached value when present and not expired."""
        with self._cache_lock:
            self._prune_expired_memory_cache_locked(cache_store)
            entry = cache_store.get(cache_key)
            if entry is None:
                return None
            if (time.time() - entry.created_at) > self.preview_cache_ttl_seconds:
                cache_store.pop(cache_key, None)
                return None
            return entry.value

    def _set_memory_cache_value(
        self,
        cache_store: dict[str, MemoryCacheEntry],
        cache_key: str,
        value: Any,
    ) -> None:
        """Store one in-memory cache value with current timestamp."""
        with self._cache_lock:
            self._prune_expired_memory_cache_locked(cache_store)
            cache_store[cache_key] = MemoryCacheEntry(
                created_at=time.time(),
                value=value,
            )

    def _prune_expired_memory_cache_locked(
        self,
        cache_store: dict[str, MemoryCacheEntry],
    ) -> None:
        """Drop expired cache items while already holding the lock."""
        now = time.time()
        expired_keys = [
            key
            for key, entry in cache_store.items()
            if (now - entry.created_at) > self.preview_cache_ttl_seconds
        ]
        for key in expired_keys:
            cache_store.pop(key, None)

    def _is_zip_artifact_fresh(self, *, zip_path: Path, source_dir: Path) -> bool:
        """Return True when one ZIP file is at least as new as its source files."""
        if not zip_path.exists() or not source_dir.exists() or not source_dir.is_dir():
            return False

        zip_mtime = zip_path.stat().st_mtime
        newest_source_mtime = 0.0
        for path in source_dir.rglob("*"):
            if not path.is_file():
                continue
            newest_source_mtime = max(newest_source_mtime, path.stat().st_mtime)
        return zip_mtime >= newest_source_mtime

    def _collect_report_batch_artifacts(
        self,
        rendered_reports: list[dict[str, Any]],
    ) -> list[Path]:
        """Collect canonical artifact paths from the current run."""
        collected_paths: list[Path] = []
        for item in rendered_reports:
            artifacts = item.get("artifacts", {})
            for artifact_key in ("view_html", "pdf_source_html", "pdf", "excel"):
                artifact_path = artifacts.get(artifact_key)
                if not isinstance(artifact_path, Path) or not artifact_path.exists():
                    continue
                collected_paths.append(artifact_path)
        return collected_paths

    def _looks_like_legacy_root_artifact(self, path: Path) -> bool:
        """Return True when one direct OUTPUT_DIR file looks like a legacy report artifact."""
        if not path.is_file():
            return False
        if path.suffix.lower() not in {".pdf", ".html", ".xlsx"}:
            return False

        file_name = path.name.lower()
        return bool(
            re.search(r"(^|_)(daily|weekly|monthly)_automatic_report_", file_name)
            or "energy_automatic_report" in file_name
            or file_name.endswith("_pdf_source.html")
        )

    def _cleanup_output_artifacts(
        self,
        *,
        rendered_reports: list[dict[str, Any]],
        canonical_output_root: Path,
        staging_output_dir: Path,
        logger_obj,
    ) -> None:
        """Remove staging files and stray root-level report artifacts after successful copy-back."""
        removed_staging_files = 0
        removed_root_files = 0
        removed_empty_staging_dir = False

        for item in rendered_reports:
            artifacts = item.get("artifacts", {})
            for artifact_key in ("staging_html", "staging_pdf"):
                artifact_path = artifacts.get(artifact_key)
                if not isinstance(artifact_path, Path) or not artifact_path.exists():
                    continue
                artifact_path.unlink(missing_ok=True)
                removed_staging_files += 1

        if canonical_output_root.exists():
            for child in canonical_output_root.iterdir():
                if not self._looks_like_legacy_root_artifact(child):
                    continue
                child.unlink(missing_ok=True)
                removed_root_files += 1

        if staging_output_dir.exists() and staging_output_dir != canonical_output_root:
            try:
                next(staging_output_dir.iterdir())
            except StopIteration:
                staging_output_dir.rmdir()
                removed_empty_staging_dir = True
            except (FileNotFoundError, OSError):
                pass

        logger_obj.info(
            "Cleaned output artifacts | canonical_output_root=%s staging_output_dir=%s removed_staging_files=%s removed_root_files=%s removed_empty_staging_dir=%s",
            canonical_output_root,
            staging_output_dir,
            removed_staging_files,
            removed_root_files,
            removed_empty_staging_dir,
        )

    def _render_report_artifacts(
        self,
        *,
        renderer: TemplateRenderingService,
        pdf_service,
        excel_service: ExcelExportService,
        env_cfg: dict[str, Any],
        period: ResolvedPeriod,
        report_context: dict[str, Any],
        canonical_output_root: Path,
        staging_output_dir: Path,
    ) -> dict[str, Path]:
        """Render one report into grouped HTML, PDF source HTML, PDF, and daily Excel."""
        template_bundle = self._select_template_bundle(period.period_type)
        export_stem = self._build_report_export_stem(env_cfg, period)

        month_dir = self._resolve_monthly_report_dir(canonical_output_root, period)
        view_dir = month_dir / "view_html"
        pdf_source_dir = month_dir / "pdf_source_html"
        pdf_dir = month_dir / "pdf"
        excel_dir = month_dir / "excel"

        for path in (view_dir, pdf_source_dir, pdf_dir, excel_dir):
            path.mkdir(parents=True, exist_ok=True)

        view_html = renderer.render(template_bundle["view"], report_context)
        pdf_html = renderer.render(template_bundle["pdf"], report_context)

        view_path = view_dir / f"{export_stem}.html"
        pdf_source_path = pdf_source_dir / f"{export_stem}.html"
        staging_html_path = self._build_unique_staging_path(
            staging_output_dir,
            f"{export_stem}_pdf_source",
            ".html",
        )
        final_pdf_path = pdf_dir / f"{export_stem}.pdf"
        staging_pdf_path = self._build_unique_staging_path(
            staging_output_dir,
            export_stem,
            ".pdf",
        )

        self._atomic_write_text(view_path, view_html)
        self._atomic_write_text(pdf_source_path, pdf_html)
        staging_html_path.write_text(pdf_html, encoding="utf-8")

        pdf_service.export(staging_html_path, staging_pdf_path)
        self._atomic_write_bytes(final_pdf_path, staging_pdf_path.read_bytes())

        artifacts = {
            "view_html": view_path,
            "pdf_source_html": pdf_source_path,
            "pdf": final_pdf_path,
            "staging_html": staging_html_path,
            "staging_pdf": staging_pdf_path,
        }

        if str(period.period_type or "").strip().lower() == "daily":
            excel_path = excel_dir / f"{export_stem}.xlsx"
            temp_excel_path = self._build_temp_output_path(excel_path)
            try:
                excel_service.export_daily_workbook(temp_excel_path, report_context)
                temp_excel_path.replace(excel_path)
            finally:
                if temp_excel_path.exists():
                    temp_excel_path.unlink(missing_ok=True)
            artifacts["excel"] = excel_path

        return artifacts

    def _resolve_report_timezone(self, config: dict[str, Any]) -> str:
        """Resolve report timezone from YAML config with safe fallback."""
        return str(
            (((config.get("config") or {}).get("time") or {}).get("timezone"))
            or "Asia/Ho_Chi_Minh"
        ).strip() or "Asia/Ho_Chi_Minh"

    def _parse_optional_date(self, value: str | None) -> Optional[date]:
        """Parse an optional browser date value."""
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        try:
            return date.fromisoformat(text)
        except ValueError as exc:
            raise ReportRequestError(
                f"Invalid date format for '{text}'. Expected YYYY-MM-DD."
            ) from exc

    def _parse_required_date(self, value: str | None, field_name: str) -> date:
        """Parse one required browser date value."""
        parsed = self._parse_optional_date(value)
        if parsed is None:
            raise ReportRequestError(f"{field_name} is required.")
        return parsed
