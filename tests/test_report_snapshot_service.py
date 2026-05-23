from __future__ import annotations

from datetime import date

from src.models.period_models import ResolvedPeriod
from src.services.report_snapshot_service import ReportSnapshotService


def _build_period() -> ResolvedPeriod:
    return ResolvedPeriod(
        period_type="monthly",
        grain="day",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        total_days=31,
        previous_start_date=date(2026, 2, 1),
        previous_end_date=date(2026, 2, 28),
        label="March 2026",
        comparison_label="February 2026",
        file_suffix="20260331",
        anchor_date=date(2026, 3, 31),
        previous_anchor_date=date(2026, 2, 28),
    )


def test_build_snapshot_contract_is_stable() -> None:
    service = ReportSnapshotService()
    payload = service.build_snapshot(
        period=_build_period(),
        report_context={
            "generated_at": "2026-05-23 23:00:00",
            "period": {
                "current_period_title": "March 2026",
                "previous_period_title": "February 2026",
            },
            "summary": {
                "coverage": {
                    "has_warning": True,
                    "message": "Coverage warning",
                },
                "electricity_snapshot": {
                    "current_display": "100.00",
                },
                "utility_snapshot_rows": [{"key": "water", "current_display": "10.00"}],
                "kpi_snapshot": {
                    "current_display": "2.50",
                },
                "kpi_area_snapshot_rows": [{"area_key": "ico", "current_display": "2.10"}],
            },
            "sections": {
                "electricity": {
                    "title": "Electricity",
                    "subtitle": "Monthly overview",
                    "totals": {
                        "cards": {
                            "total": {
                                "label": "TOTAL",
                                "value_display": "100.00",
                            }
                        }
                    },
                    "daily_summary": {
                        "title": "Daily summary",
                        "rows": [{"date": date(2026, 3, 1), "value": 100.0}],
                    },
                    "charts": {
                        "daily_trend": {
                            "title": "Trend",
                            "subtitle": "Current vs previous",
                            "note": "Renderer agnostic",
                            "option": {
                                "xAxis": {"data": ["2026-03-01", "2026-03-02"]},
                                "series": [
                                    {"name": "Current", "type": "line", "data": [10, 11]},
                                    {"name": "Previous", "type": "line", "data": [9, 8]},
                                ],
                            },
                        }
                    },
                },
                "utility": {
                    "title": "Utility",
                    "subtitle": "Utility overview",
                    "energy": {
                        "overview_cards": [{"label": "Water", "current_display": "10.00"}],
                        "detail_rows": [{"utility": "Water", "value": 10.0}],
                    },
                    "charts": {},
                },
                "kpi": {
                    "title": "KPI",
                    "subtitle": "KPI overview",
                    "coverage": {
                        "coverage_note": "Coverage note",
                        "is_complete": False,
                        "uncovered_ranges": [{"start": "2026-03-05", "end": "2026-03-06"}],
                    },
                    "charts": {
                        "daily_dashboard": {
                            "cards": [{"label": "TOTAL", "value_display": "2.50", "is_total": True}],
                            "charts": {
                                "kpi_total": {
                                    "title": "KPI trend",
                                    "option": {
                                        "series": [{"name": "KPI", "type": "bar", "data": [2.5]}],
                                    },
                                }
                            },
                        }
                    },
                },
            },
        },
        cache_hit=True,
        cache_fingerprint="style:1|config:2",
    )

    assert payload["meta"]["contract"] == {"name": "report_snapshot", "version": 2}
    assert payload["availability"]["warning_count"] == 2
    assert payload["artifacts"]["artifact_manifest_url"].startswith("/api/v1/report/artifacts?")

    electricity = payload["sections"]["electricity"]
    assert electricity["section_key"] == "electricity"
    assert electricity["card_count"] == 1
    assert electricity["table_count"] == 1
    assert electricity["chart_count"] == 1
    assert electricity["tables"][0]["columns"] == ["date", "value"]
    assert electricity["charts"][0]["series_count"] == 2


def test_build_artifact_manifest_contract_is_stable() -> None:
    service = ReportSnapshotService()
    payload = service.build_artifact_manifest(
        period=_build_period(),
        cache_fingerprint="style:1|config:2",
        artifact_state={
            "group": {
                "month_bucket": "2026_03",
                "month_dir_exists": True,
            },
            "interactive": {
                "artifact_key": "interactive",
                "artifact_type": "interactive_html",
                "media_type": "text/html",
                "status": "available",
                "filename": "report.html",
                "exists": True,
                "url": "/reports?...",
                "size_bytes": 123,
            },
            "zip_package": {
                "artifact_key": "zip_package",
                "artifact_type": "report_zip_package",
                "media_type": "application/zip",
                "status": "stale",
                "filename": "2026_03_report_package.zip",
                "exists": True,
                "url": "/reports/download-zip?...",
                "size_bytes": 456,
                "freshness": {"source_dir_exists": True, "is_fresh": False},
            },
            "excel": {
                "artifact_key": "excel",
                "artifact_type": "daily_excel_workbook",
                "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "status": "missing",
                "filename": "report.xlsx",
                "exists": False,
                "url": None,
            },
        },
    )

    assert payload["meta"]["contract"] == {"name": "report_artifact_manifest", "version": 2}
    assert payload["artifacts"]["summary"] == {
        "artifact_count": 3,
        "available_count": 1,
        "stale_count": 1,
        "missing_count": 1,
    }
    assert payload["artifacts"]["zip_package"]["status"] == "stale"
