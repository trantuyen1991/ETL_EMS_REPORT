# -*- coding: utf-8 -*-

"""Excel export service for daily tabular report artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExcelSheetPayload:
    """Flat workbook payload for one Excel sheet."""

    name: str
    columns: list[str]
    rows: list[dict[str, Any]]


class ExcelExportService:
    """Build and export the approved daily-only Excel workbook."""

    def build_daily_sheet_payloads(
        self,
        report_context: dict[str, Any],
    ) -> list[ExcelSheetPayload]:
        """Build flat sheet payloads from the existing daily report context."""
        return [
            self._build_meta_sheet(report_context),
            self._build_electricity_summary_sheet(report_context),
            self._build_electricity_top_meter_sheet(report_context),
            self._build_electricity_detail_sheet(report_context),
            self._build_utility_dashboard_sheet(report_context),
            self._build_utility_consumption_totals_sheet(report_context),
            self._build_utility_consumption_detail_sheet(report_context),
            self._build_utility_energy_detail_sheet(report_context),
            self._build_kpi_totals_sheet(report_context),
            self._build_kpi_summary_matrix_sheet(report_context),
            self._build_kpi_detail_sheet(report_context),
        ]

    def export_daily_workbook(
        self,
        output_path: str | Path,
        report_context: dict[str, Any],
    ) -> Path:
        """Write the daily workbook to disk."""
        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise RuntimeError(
                "openpyxl is required for Excel export. Install dependencies before running workbook export."
            ) from exc

        workbook = Workbook()
        default_sheet = workbook.active
        workbook.remove(default_sheet)

        sheet_payloads = self.build_daily_sheet_payloads(report_context)
        for payload in sheet_payloads:
            worksheet = workbook.create_sheet(title=payload.name)
            worksheet.append(payload.columns)
            for row in payload.rows:
                worksheet.append([self._normalize_cell_value(row.get(column)) for column in payload.columns])

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(output_file)

        logger.info(
            "Daily Excel workbook exported successfully. path=%s sheet_count=%s",
            output_file,
            len(sheet_payloads),
        )
        return output_file

    def _build_meta_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        meta = report_context.get("meta", {})
        period = report_context.get("period", {})
        rows = [
            {"field": "report_title", "value": meta.get("report_title")},
            {"field": "report_subtitle", "value": meta.get("report_subtitle")},
            {"field": "workshop_name", "value": meta.get("workshop_name")},
            {"field": "period_type", "value": period.get("type")},
            {"field": "period_label", "value": period.get("label")},
            {"field": "comparison_label", "value": period.get("comparison_label")},
            {"field": "anchor_date", "value": period.get("anchor_date")},
            {"field": "start_date", "value": period.get("start_date")},
            {"field": "end_date", "value": period.get("end_date")},
            {"field": "previous_start_date", "value": period.get("previous_start_date")},
            {"field": "previous_end_date", "value": period.get("previous_end_date")},
            {"field": "generated_at", "value": report_context.get("generated_at")},
            {"field": "version", "value": report_context.get("version")},
            {"field": "context_mode", "value": report_context.get("context_mode")},
        ]
        return ExcelSheetPayload(name="Meta", columns=["field", "value"], rows=rows)

    def _build_electricity_summary_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        section = report_context.get("sections", {}).get("electricity", {})
        summary = section.get("daily_summary", {})
        rows: list[dict[str, Any]] = []

        for item in summary.get("rows", []):
            rows.append({
                "row_type": "plant",
                "date": item.get("date") or item.get("date_display"),
                "scope_key": "plant",
                "scope_name": "Plant",
                "total_energy_display": item.get("total_energy_display"),
                "top_1_meter": item.get("top_1_meter"),
                "top_1_value_display": item.get("top_1_value_display"),
                "top_1_pct_display": item.get("top_1_pct_display"),
                "active_meter_count": item.get("active_meter_count"),
                "average_per_active_display": item.get("average_per_active_display") or item.get("avg_per_active_display"),
                "total_meter_count": item.get("total_meter_count"),
                "inactive_meter_count": item.get("inactive_meter_count"),
            })

        for item in summary.get("area_rows", []):
            area_map = item.get("areas", {})
            for area_key, area in area_map.items():
                rows.append({
                    "row_type": "area",
                    "date": item.get("date") or item.get("date_display"),
                    "scope_key": area_key,
                    "scope_name": area.get("area_name") or area.get("area_label") or area_key,
                    "total_energy_display": area.get("total_display"),
                    "top_1_meter": area.get("top_1_meter") or area.get("top_meter_name"),
                    "top_1_value_display": area.get("top_1_value_display") or area.get("top_meter_value_display"),
                    "top_1_pct_display": area.get("top_1_pct_display") or area.get("top_meter_pct_display"),
                    "active_meter_count": area.get("active_total_display") or area.get("active_meter_count"),
                    "average_per_active_display": area.get("avg_per_active_display"),
                    "total_meter_count": area.get("total_meter_count"),
                    "inactive_meter_count": area.get("inactive_meter_count"),
                })

        columns = [
            "row_type",
            "date",
            "scope_key",
            "scope_name",
            "total_energy_display",
            "top_1_meter",
            "top_1_value_display",
            "top_1_pct_display",
            "active_meter_count",
            "average_per_active_display",
            "total_meter_count",
            "inactive_meter_count",
        ]
        return ExcelSheetPayload(name="Electricity_Summary", columns=columns, rows=rows)

    def _build_electricity_top_meter_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        rows = report_context.get("sections", {}).get("electricity", {}).get("top10", {}).get("rows", [])
        columns = [
            "rank",
            "area_key",
            "area_display",
            "meter_key",
            "meter_name",
            "display_name",
            "current_display",
            "current_pct_display",
            "previous_display",
            "previous_pct_display",
            "delta_display",
            "delta_pct_display",
        ]
        return ExcelSheetPayload(name="Electricity_Top_Meter", columns=columns, rows=rows)

    def _build_electricity_detail_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        tables = report_context.get("sections", {}).get("electricity", {}).get("daily_detail_tables", [])
        rows: list[dict[str, Any]] = []

        for table in tables:
            column_map = {
                column.get("key"): column.get("display_name")
                for column in table.get("columns", [])
            }
            for detail_row in table.get("rows", []):
                for cell in detail_row.get("cells", []):
                    meter_key = cell.get("key")
                    rows.append({
                        "date": detail_row.get("date") or detail_row.get("date_display"),
                        "area_key": table.get("area_key"),
                        "area_title": table.get("title"),
                        "meter_key": meter_key,
                        "meter_display_name": column_map.get(meter_key, meter_key),
                        "meter_role": cell.get("meter_role"),
                        "raw_value": cell.get("raw_value"),
                        "display_value": cell.get("display"),
                        "official_daily_total": detail_row.get("official_daily_total"),
                        "main_feeder_total": detail_row.get("main_feeder_total"),
                        "submeter_total": detail_row.get("submeter_total"),
                        "unknown_load": detail_row.get("unknown_load"),
                    })

        columns = [
            "date",
            "area_key",
            "area_title",
            "meter_key",
            "meter_display_name",
            "meter_role",
            "raw_value",
            "display_value",
            "official_daily_total",
            "main_feeder_total",
            "submeter_total",
            "unknown_load",
        ]
        return ExcelSheetPayload(name="Electricity_Detail", columns=columns, rows=rows)

    def _build_utility_dashboard_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        rows = report_context.get("sections", {}).get("utility", {}).get("daily_dashboard", {}).get("overview_cards", [])
        columns = [
            "key",
            "title",
            "theme_key",
            "status_label",
            "today_display",
            "yesterday_display",
            "delta_display",
            "delta_pct_display",
        ]
        return ExcelSheetPayload(name="Utility_Dashboard", columns=columns, rows=rows)

    def _build_utility_consumption_totals_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        rows = report_context.get("sections", {}).get("utility", {}).get("consumption", {}).get("totals", {}).get("rows", [])
        columns = [
            "key",
            "display_name",
            "unit",
            "current_value",
            "current_display",
            "previous_value",
            "previous_display",
            "delta_display",
            "delta_pct_display",
        ]
        return ExcelSheetPayload(name="Utility_Consumption_Totals", columns=columns, rows=rows)

    def _build_utility_consumption_detail_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        section = report_context.get("sections", {}).get("utility", {}).get("consumption", {}).get("detail", {})
        columns_meta = {
            column.get("key"): column
            for column in section.get("daily_columns", [])
        }
        rows: list[dict[str, Any]] = []

        for day_row in section.get("daily_rows", []):
            for cell in day_row.get("daily_values", []):
                column_meta = columns_meta.get(cell.get("key"), {})
                rows.append({
                    "date": day_row.get("date") or day_row.get("date_display"),
                    "utility_key": cell.get("key"),
                    "utility_display_name": column_meta.get("display_name") or cell.get("key"),
                    "value_display": cell.get("display"),
                    "family_class": cell.get("family_class"),
                    "is_max": cell.get("is_max"),
                    "status": day_row.get("status"),
                    "coverage_note": day_row.get("coverage_note"),
                })

        columns = [
            "date",
            "utility_key",
            "utility_display_name",
            "value_display",
            "family_class",
            "is_max",
            "status",
            "coverage_note",
        ]
        return ExcelSheetPayload(name="Utility_Consumption_Detail", columns=columns, rows=rows)

    def _build_utility_energy_detail_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        rows = report_context.get("sections", {}).get("utility", {}).get("energy", {}).get("detail_rows", [])
        columns = [
            "key",
            "display_name",
            "group_label",
            "current_display",
            "previous_display",
            "delta_display",
            "delta_pct_display",
            "energy_current_display",
            "energy_previous_display",
            "energy_delta_display",
            "energy_delta_pct_display",
        ]
        return ExcelSheetPayload(name="Utility_Energy_Detail", columns=columns, rows=rows)

    def _build_kpi_totals_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        section = report_context.get("sections", {}).get("kpi", {}).get("totals", {})
        rows: list[dict[str, Any]] = []

        plant = section.get("plant", {})
        if plant:
            rows.append({
                "scope_key": "plant",
                "scope_name": "Plant",
                "current_display": plant.get("current_display"),
                "previous_display": plant.get("previous_display"),
                "coverage_display": plant.get("coverage_display"),
                "unit": plant.get("unit"),
            })

        for area in section.get("areas", []):
            rows.append({
                "scope_key": area.get("area_key"),
                "scope_name": area.get("area_name"),
                "current_display": area.get("current_display"),
                "previous_display": area.get("previous_display"),
                "coverage_display": area.get("coverage_display"),
                "unit": area.get("unit"),
            })

        columns = [
            "scope_key",
            "scope_name",
            "current_display",
            "previous_display",
            "coverage_display",
            "unit",
        ]
        return ExcelSheetPayload(name="KPI_Totals", columns=columns, rows=rows)

    def _build_kpi_summary_matrix_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        section = report_context.get("sections", {}).get("kpi", {}).get("summary_matrix", {})
        scope_keys = [column.get("key") for column in section.get("group_columns", [])]
        rows: list[dict[str, Any]] = []

        for metric_row in section.get("rows", []):
            cell_map = metric_row.get("cells", {})
            for scope_key in scope_keys:
                cell = cell_map.get(scope_key, {})
                delta = cell.get("delta", {})
                rows.append({
                    "metric_label": metric_row.get("metric_label"),
                    "scope_key": scope_key,
                    "today_display": cell.get("today_display"),
                    "yesterday_display": cell.get("yesterday_display"),
                    "delta_display": delta.get("display"),
                    "delta_class": delta.get("class"),
                    "delta_arrow": delta.get("arrow"),
                })

        columns = [
            "metric_label",
            "scope_key",
            "today_display",
            "yesterday_display",
            "delta_display",
            "delta_class",
            "delta_arrow",
        ]
        return ExcelSheetPayload(name="KPI_Summary_Matrix", columns=columns, rows=rows)

    def _build_kpi_detail_sheet(self, report_context: dict[str, Any]) -> ExcelSheetPayload:
        detail_rows = report_context.get("sections", {}).get("kpi", {}).get("daily_detail", {}).get("rows", [])
        rows: list[dict[str, Any]] = []

        for detail_row in detail_rows:
            for area_row in detail_row.get("area_rows", []):
                rows.append({
                    "date": detail_row.get("date") or detail_row.get("date_display"),
                    "time_frame_source": detail_row.get("time_frame_source"),
                    "area_key": area_row.get("area_key"),
                    "area_label": area_row.get("area_label"),
                    "energy_display": self._nested_display(area_row, "energy"),
                    "product_display": self._nested_display(area_row, "product"),
                    "kpi_display": self._nested_display(area_row, "kpi"),
                    "status": detail_row.get("status"),
                    "coverage_note": detail_row.get("coverage_note"),
                })

        columns = [
            "date",
            "time_frame_source",
            "area_key",
            "area_label",
            "energy_display",
            "product_display",
            "kpi_display",
            "status",
            "coverage_note",
        ]
        return ExcelSheetPayload(name="KPI_Detail", columns=columns, rows=rows)

    @staticmethod
    def _nested_display(row: dict[str, Any], key: str) -> Any:
        value = row.get(key)
        if isinstance(value, dict):
            return value.get("display")
        return value

    @staticmethod
    def _normalize_cell_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        if isinstance(value, date):
            return value.isoformat()
        return value
