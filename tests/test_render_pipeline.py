from __future__ import annotations

from datetime import date
from pathlib import Path

from src.models.period_models import ResolvedPeriod
from src.services.report_engine_service import ReportEngineService
from src.services.template_service import TemplateRenderingService


class FakePdfService:
    def export(self, html_path: Path, output_pdf: Path) -> None:
        assert html_path.exists()
        output_pdf.write_bytes(b"%PDF-smoke\n")


class FakeExcelService:
    def export_daily_workbook(self, output_path: Path, report_context: dict) -> None:
        output_path.write_bytes(b"XLSX-smoke\n")


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
    service = ReportEngineService()

    assert service._select_template_bundle("daily") == {
        "view": "report/view/report_view_daily.html",
        "pdf": "report/pdf/report_pdf_daily.html",
    }
    assert service._select_template_bundle("weekly") == {
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

    service = ReportEngineService(project_root=tmp_path)
    artifacts = service._render_report_artifacts(
        renderer=TemplateRenderingService(template_dir),
        pdf_service=FakePdfService(),
        excel_service=FakeExcelService(),
        env_cfg={"REPORT_FILENAME": "Energy Report"},
        period=_build_period(),
        report_context={"meta": {"message": "ok"}},
        canonical_output_root=project_output_dir,
        staging_output_dir=staging_output_dir,
    )

    assert artifacts["view_html"].name == "03_daily_energy_report_20250831.html"
    assert artifacts["pdf_source_html"].name == "03_daily_energy_report_20250831.html"
    assert artifacts["pdf"].name == "03_daily_energy_report_20250831.pdf"
    assert artifacts["excel"].name == "03_daily_energy_report_20250831.xlsx"
    assert artifacts["view_html"].read_text(encoding="utf-8") == "<html><body>VIEW ok</body></html>"
    assert artifacts["pdf_source_html"].read_text(encoding="utf-8") == "<html><body>PDF ok</body></html>"
    assert artifacts["staging_html"].read_text(encoding="utf-8") == "<html><body>PDF ok</body></html>"
    assert artifacts["pdf"].read_bytes() == b"%PDF-smoke\n"
    assert artifacts["staging_pdf"].read_bytes() == b"%PDF-smoke\n"
    assert artifacts["excel"].read_bytes() == b"XLSX-smoke\n"


def test_collect_report_batch_artifacts_returns_existing_canonical_paths(tmp_path: Path) -> None:
    project_output_dir = tmp_path / "output" / "reports"
    project_output_dir.mkdir(parents=True)

    view_path = project_output_dir / "daily_automatic_report_daily_20250625_view.html"
    pdf_source_path = project_output_dir / "daily_automatic_report_daily_20250625_pdf_source.html"
    pdf_path = project_output_dir / "daily_automatic_report_daily_20250625.pdf"

    view_path.write_text("view", encoding="utf-8")
    pdf_source_path.write_text("pdf_source", encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-test\n")
    excel_path = project_output_dir / "daily_automatic_report_daily_20250625.xlsx"
    excel_path.write_bytes(b"XLSX-test\n")

    service = ReportEngineService(project_root=tmp_path)
    collected_paths = service._collect_report_batch_artifacts(
        rendered_reports=[
            {
                "artifacts": {
                    "view_html": view_path,
                    "pdf_source_html": pdf_source_path,
                    "pdf": pdf_path,
                    "excel": excel_path,
                }
            }
        ],
    )

    assert [path.name for path in collected_paths] == [
        "daily_automatic_report_daily_20250625_view.html",
        "daily_automatic_report_daily_20250625_pdf_source.html",
        "daily_automatic_report_daily_20250625.pdf",
        "daily_automatic_report_daily_20250625.xlsx",
    ]


def test_resolve_monthly_report_dir_uses_report_anchor_month() -> None:
    service = ReportEngineService()
    report_batch_dir = service._resolve_monthly_report_dir(
        canonical_output_root=Path("output/reports"),
        period=_build_period(),
    )

    assert report_batch_dir.parent == Path("output/reports")
    assert report_batch_dir.name == "2025_08"


def test_resolve_pdf_staging_dir_falls_back_for_hidden_output_paths() -> None:
    service = ReportEngineService()
    staging_dir = service._resolve_pdf_staging_dir(
        env_cfg={},
        canonical_output_root=Path("/home/nbt/.openclaw/workspace/02_MySQL/output/reports"),
        project_root=Path("/home/nbt/.openclaw/workspace/02_MySQL"),
    )

    assert staging_dir == Path.home() / "Reports" / "_staging"
