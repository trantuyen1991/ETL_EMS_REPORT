from __future__ import annotations

from datetime import date
from pathlib import Path

from src.main import (
    _archive_report_batch,
    _render_report_artifacts,
    _resolve_pdf_staging_dir,
    _resolve_report_batch_dir,
    _select_template_bundle,
)
from src.models.period_models import ResolvedPeriod
from src.services.template_service import TemplateRenderingService


class FakePdfService:
    def export(self, html_path: Path, output_pdf: Path) -> None:
        assert html_path.exists()
        output_pdf.write_bytes(b"%PDF-smoke\n")


def _build_period(period_type: str = "daily") -> ResolvedPeriod:
    return ResolvedPeriod(
        period_type=period_type,
        grain="day",
        start_date=date(2025, 8, 31),
        end_date=date(2025, 8, 31),
        total_days=1,
        previous_start_date=date(2025, 8, 30),
        previous_end_date=date(2025, 8, 30),
        label="2025-08-31",
        comparison_label="2025-08-30",
        file_suffix="2025-08-31",
        anchor_date=date(2025, 8, 31),
        previous_anchor_date=date(2025, 8, 30),
    )


def test_select_template_bundle_maps_periodic_reports_to_shared_templates() -> None:
    assert _select_template_bundle("daily") == {
        "view": "report/view/report_view_daily.html",
        "pdf": "report/pdf/report_pdf_daily.html",
    }
    assert _select_template_bundle("weekly") == {
        "view": "report/view/report_view_periodic.html",
        "pdf": "report/pdf/report_pdf_periodic.html",
    }


def test_render_report_artifacts_writes_view_pdf_source_and_final_pdf(tmp_path: Path) -> None:
    template_dir = tmp_path / "templates"
    (template_dir / "report" / "view").mkdir(parents=True)
    (template_dir / "report" / "pdf").mkdir(parents=True)

    (template_dir / "report" / "view" / "report_view_daily.html").write_text(
        "<html><body>VIEW {{ meta.message }}</body></html>",
        encoding="utf-8",
    )
    (template_dir / "report" / "pdf" / "report_pdf_daily.html").write_text(
        "<html><body>PDF {{ meta.message }}</body></html>",
        encoding="utf-8",
    )

    project_output_dir = tmp_path / "output" / "reports"
    staging_output_dir = tmp_path / "print_staging"
    project_output_dir.mkdir(parents=True)
    staging_output_dir.mkdir(parents=True)

    artifacts = _render_report_artifacts(
        renderer=TemplateRenderingService(template_dir),
        pdf_service=FakePdfService(),
        env_cfg={"REPORT_FILENAME": "Energy Report"},
        period=_build_period(),
        report_context={"meta": {"message": "ok"}},
        project_output_dir=project_output_dir,
        staging_output_dir=staging_output_dir,
    )

    assert artifacts["view_html"].read_text(encoding="utf-8") == "<html><body>VIEW ok</body></html>"
    assert artifacts["pdf_source_html"].read_text(encoding="utf-8") == "<html><body>PDF ok</body></html>"
    assert artifacts["staging_html"].read_text(encoding="utf-8") == "<html><body>PDF ok</body></html>"
    assert artifacts["pdf"].read_bytes() == b"%PDF-smoke\n"
    assert artifacts["staging_pdf"].read_bytes() == b"%PDF-smoke\n"


def test_archive_report_batch_copies_current_run_artifacts_into_dated_folder(tmp_path: Path) -> None:
    project_output_dir = tmp_path / "output" / "reports"
    project_output_dir.mkdir(parents=True)

    view_path = project_output_dir / "daily_automatic_report_daily_20250625_view.html"
    pdf_source_path = project_output_dir / "daily_automatic_report_daily_20250625_pdf_source.html"
    pdf_path = project_output_dir / "daily_automatic_report_daily_20250625.pdf"

    view_path.write_text("view", encoding="utf-8")
    pdf_source_path.write_text("pdf_source", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-test\n")

    report_batch_dir = project_output_dir / "2026_05_01"
    archived_paths = _archive_report_batch(
        rendered_reports=[
            {
                "artifacts": {
                    "view_html": view_path,
                    "pdf_source_html": pdf_source_path,
                    "pdf": pdf_path,
                }
            }
        ],
        report_batch_dir=report_batch_dir,
    )

    assert [path.name for path in archived_paths] == [
        "daily_automatic_report_daily_20250625_view.html",
        "daily_automatic_report_daily_20250625_pdf_source.html",
        "daily_automatic_report_daily_20250625.pdf",
    ]
    assert (report_batch_dir / view_path.name).read_text(encoding="utf-8") == "view"
    assert (report_batch_dir / pdf_source_path.name).read_text(encoding="utf-8") == "pdf_source"
    assert (report_batch_dir / pdf_path.name).read_bytes() == b"%PDF-test\n"


def test_resolve_report_batch_dir_uses_export_run_date_folder_name() -> None:
    report_batch_dir = _resolve_report_batch_dir(
        env_cfg={"APP_TIMEZONE": "UTC"},
        project_output_dir=Path("output/reports"),
    )

    assert report_batch_dir.parent == Path("output/reports")
    assert len(report_batch_dir.name) == 10
    assert report_batch_dir.name.count("_") == 2


def test_resolve_pdf_staging_dir_falls_back_for_hidden_output_paths() -> None:
    staging_dir = _resolve_pdf_staging_dir(
        env_cfg={},
        project_output_dir=Path("/home/nbt/.openclaw/workspace/02_MySQL/output/reports"),
    )

    assert staging_dir == Path.home() / "Reports"
