# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportBuilderService:
    """Service to assemble the V3 report context."""

    def build_report_context_v3(
        self,
        *,
        meta: Dict[str, Any],
        period: Dict[str, Any],
        energy_object: Optional[Dict[str, Any]],
        kpi_object: Optional[Dict[str, Any]],
        utility_object: Optional[Dict[str, Any]],
        mode: str = "html",
    ) -> Dict[str, Any]:
        """
        Build the V3 report context.

        Args:
            meta: Base report metadata.
            period: Period metadata prepared by main flow.
            energy_object: Prepared energy domain object.
            kpi_object: Prepared KPI domain object.
            utility_object: Prepared utility domain object.
            mode: Render mode such as html or pdf.

        Returns:
            Dict[str, Any]: V3 report context.

        Example:
            context = report_builder.build_report_context_v3(
                meta=meta,
                period=period_info,
                energy_object=energy_object,
                kpi_object=kpi_object,
                utility_object=utility_object,
                mode="html",
            )
        """
        v3_period_block = self._build_v3_period_block(
            period=period,
            kpi_object=kpi_object,
        )

        v3_summary_block = self._build_v3_summary_block(
            energy_object=energy_object,
            utility_object=utility_object,
            kpi_object=kpi_object,
        )

        v3_electricity_section = self._build_v3_electricity_section(
            energy_object=energy_object,
            period_type=str(period.get("type") or "").strip().lower(),
        )

        v3_utility_section = self._build_v3_utility_section(
            utility_object=utility_object,
            energy_object=energy_object,
            period=period,
        )

        v3_period_block["flags"]["show_sensor_monitoring"] = bool(
            v3_utility_section.get("sensor_monitoring", {}).get("enabled", False)
        )

        v3_kpi_section = self._build_v3_kpi_section(
            kpi_object=kpi_object,
            period_type=str(period.get("type") or "").strip().lower(),
            anchor_date=period.get("anchor_date"),
            previous_anchor_date=period.get("previous_anchor_date"),
        )

        notes = self._build_notes(kpi_object, utility_object)

        report_context: Dict[str, Any] = {
            "meta": {
                "report_title": meta.get("report_title", ""),
                "report_subtitle": "Automatic Report",
                "workshop_name": meta.get("workshop_name", ""),
                "energy_unit": meta.get("energy_unit", "kWh"),
                "kpi_unit": meta.get("kpi_unit", "kWh/Ton"),
                "company_logo_uri": self._build_company_logo_data_uri(),
                "header_background_uri": self._build_icon_data_uri("title_background.png"),
                "utility_header_icon_uri": self._build_icon_data_uri("utilityheader.svg"),
            },
            "period": v3_period_block["period"],
            "flags": v3_period_block["flags"],
            "labels": v3_period_block["labels"],
            "summary": v3_summary_block,
            "sections": {
                "electricity": v3_electricity_section,
                "utility": v3_utility_section,
                "kpi": v3_kpi_section,
            },
            "notes": notes,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "v4.0.0",
            "context_mode": mode,
        }

        logger.info("Report context V3 built successfully")

        return report_context

    def _build_company_logo_data_uri(self) -> str:
        """Embed the company logo so both HTML preview and PDF render consistently."""
        for filename in ("logo_company.svg", "logo_company.png"):
            asset_uri = self._build_icon_data_uri(filename)
            if asset_uri:
                return asset_uri
        return ""

    def _build_icon_data_uri(self, filename: str) -> str:
        """Embed a template icon asset for stable HTML/PDF rendering."""
        icon_path = (
            Path(__file__).resolve().parents[2]
            / "src"
            / "templates"
            / "assets"
            / "icon"
            / filename
        )

        suffix = icon_path.suffix.lower()
        mime_type = "image/svg+xml" if suffix == ".svg" else "image/png"

        try:
            icon_bytes = icon_path.read_bytes()
        except OSError:
            logger.warning("Unable to read icon asset. path=%s", icon_path)
            return ""

        encoded = base64.b64encode(icon_bytes).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _build_v3_period_block(
        self,
        period: Dict[str, Any],
        kpi_object: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build V3 period, flags, and labels block from period metadata.

        Business rules:
        - daily   -> Today / Yesterday
        - weekly  -> This Week / Previous Week
        - monthly -> This Month / Previous Month
        - weekly/monthly should show total days and average per day
        - daily should hide total days and average per day

        Args:
            period: Period metadata prepared by main flow.
            kpi_object: Prepared KPI domain object for coverage warning flag.

        Returns:
            Dict[str, Any]: Combined V3 period-related block.

        Example:
            block = self._build_v3_period_block(period=period_info, kpi_object=kpi_object)
        """
        period_type = str(period.get("type") or "").strip().lower()

        is_daily_report = period_type == "daily"
        is_weekly_report = period_type == "weekly"
        is_monthly_report = period_type == "monthly"

        if is_monthly_report:
            priority = 3
            current_period_title = "This Month"
            previous_period_title = "Previous Month"
            show_total_days = True
            show_average_per_day = True
        elif is_weekly_report:
            priority = 2
            current_period_title = "This Week"
            previous_period_title = "Previous Week"
            show_total_days = True
            show_average_per_day = True
        else:
            priority = 1
            current_period_title = "Today"
            previous_period_title = "Yesterday"
            show_total_days = False
            show_average_per_day = False

        has_coverage_warning = False
        if kpi_object:
            coverage = (
                kpi_object.get("current", {})
                .get("coverage", {})
            )
            has_coverage_warning = not coverage.get("is_full_coverage", True)

        return {
            "period": {
                "type": period_type,
                "priority": priority,
                "start_date": period.get("start_date", ""),
                "end_date": period.get("end_date", ""),
                "previous_start_date": period.get("previous_start_date", ""),
                "previous_end_date": period.get("previous_end_date", ""),
                "label": period.get("label", ""),
                "comparison_label": period.get("comparison_label", ""),
                "current_period_title": current_period_title,
                "previous_period_title": previous_period_title,
                "show_total_days": show_total_days,
                "show_average_per_day": show_average_per_day,
            },
            "flags": {
                "has_coverage_warning": has_coverage_warning,
                "show_electricity_section": True,
                "show_utility_section": True,
                "show_kpi_section": True,
                "show_energy_snapshot": True,
                "show_kpi_snapshot": True,
                "show_utility_snapshot": True,
                "show_total_days": show_total_days,
                "show_average_per_day": show_average_per_day,
                "show_product_context": False,
                "show_sensor_monitoring": False,
                "is_daily_report": is_daily_report,
                "is_weekly_report": is_weekly_report,
                "is_monthly_report": is_monthly_report,
            },
            "labels": {
                "report_section_1": "ELECTRICITY CONSUMPTION",
                "report_section_2": "UTILITY USAGE",
                "report_section_3": "ENERGY KPI",
                "current_period": current_period_title,
                "previous_period": previous_period_title,
                "total_label": "Total",
                "comparison_label": "Comparison",
                "detail_label": "Detail",
            },
        }

    def _build_v3_summary_block(
        self,
        *,
        energy_object: Optional[Dict[str, Any]],
        utility_object: Optional[Dict[str, Any]],
        kpi_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build V3 summary block using existing helper methods.

        Reuse existing snapshot/coverage builders first so the V3 contract
        can be connected quickly without changing the underlying business logic.

        Args:
            energy_object: Prepared energy domain object.
            utility_object: Prepared utility domain object.
            kpi_object: Prepared KPI domain object.

        Returns:
            Dict[str, Any]: V3 summary block.

        Example:
            summary = self._build_v3_summary_block(
                energy_object=energy_object,
                utility_object=utility_object,
                kpi_object=kpi_object,
            )
        """
        electricity_snapshot: Dict[str, Any] = {}
        utility_snapshot_rows: list[dict[str, Any]] = []
        kpi_snapshot: Dict[str, Any] = {}
        kpi_area_snapshot_rows: list[dict[str, Any]] = []
        coverage: Dict[str, Any] = {}

        if energy_object:
            electricity_snapshot = self._build_energy_snapshot(energy_object)

        if utility_object:
            utility_snapshot_rows = self._build_utility_snapshot(utility_object)

        if kpi_object:
            kpi_snapshot = self._build_kpi_snapshot(kpi_object)
            kpi_area_snapshot_rows = self._build_kpi_area_snapshot_rows(kpi_object)
            coverage = self._build_global_coverage(kpi_object)

        return {
            "electricity_snapshot": electricity_snapshot,
            "utility_snapshot_rows": utility_snapshot_rows,
            "kpi_snapshot": kpi_snapshot,
            "kpi_area_snapshot_rows": kpi_area_snapshot_rows,
            "coverage": coverage,
        }

    def _build_v3_electricity_area_stats(
        self,
        energy_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build additional V3 electricity area stats for rendering.

        This helper calculates:
        - current share ratio by area
        - previous share ratio by area
        - active meter count / total meter count for current period

        Args:
            energy_object: Prepared energy domain object.

        Returns:
            Dict[str, Dict[str, Any]]: Area stats keyed by area_key.

        Example:
            stats = self._build_v3_electricity_area_stats(energy_object)
        """
        if not energy_object:
            return {}

        current_summary = energy_object.get("current", {}).get("summary", {})
        previous_summary = energy_object.get("previous", {}).get("summary", {})
        current_tables = energy_object.get("current", {}).get("daily_tables", [])

        current_table_lookup = {
            table.get("area_key"): table
            for table in current_tables
        }

        plant_current_total = 0.0
        plant_previous_total = 0.0

        for area_key in ["diode", "ico", "sakari"]:
            plant_current_total += float(
                current_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0
            )
            plant_previous_total += float(
                previous_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0
            )

        stats: Dict[str, Dict[str, Any]] = {}
        plant_active_meter_count = 0
        plant_total_meter_count = 0

        for area_key in ["diode", "ico", "sakari"]:
            current_value = float(
                current_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0
            )
            previous_value = float(
                previous_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0
            )

            current_ratio = (
                current_value / plant_current_total
                if plant_current_total > 0
                else None
            )
            previous_ratio = (
                previous_value / plant_previous_total
                if plant_previous_total > 0
                else None
            )

            table = current_table_lookup.get(area_key, {})
            meter_columns = table.get("meter_columns", [])
            total_meter_count = len(meter_columns)
            active_meter_count = self._calculate_active_meter_count_for_table(table)

            plant_active_meter_count += active_meter_count
            plant_total_meter_count += total_meter_count

            stats[area_key] = {
                "current_ratio_display": self._fmt_pct(current_ratio),
                "previous_ratio_display": self._fmt_pct(previous_ratio),
                "active_meter_count": active_meter_count,
                "total_meter_count": total_meter_count,
                "active_total_display": f"{active_meter_count}/{total_meter_count}",
            }

        stats["plant"] = {
            "active_meter_count": plant_active_meter_count,
            "total_meter_count": plant_total_meter_count,
            "active_total_display": f"{plant_active_meter_count}/{plant_total_meter_count}",
        }

        return stats

    def _calculate_active_meter_count_for_table(self, table: Dict[str, Any]) -> int:
        """Count meters with at least one positive value in a table."""
        meter_columns = table.get("meter_columns", [])
        active_meter_count = 0

        for meter_key in meter_columns:
            has_positive_value = False

            for row in table.get("rows", []):
                for cell in row.get("cells", []):
                    if cell.get("key") != meter_key:
                        continue

                    raw_value = cell.get("raw_value")
                    if isinstance(raw_value, (int, float)) and float(raw_value) > 0:
                        has_positive_value = True
                        break

                if has_positive_value:
                    break

            if has_positive_value:
                active_meter_count += 1

        return active_meter_count

    def _get_v3_area_visual_map(self) -> Dict[str, Dict[str, str]]:
        """Return stable V3 colors and display names for workshop areas."""
        return {
            "diode": {
                "display": "DIODE",
                "bar_color": "#2563eb",
                "bar_tint": "rgba(37, 99, 235, 0.12)",
                "header_bg": "#eef5ff",
                "soft_bg": "#f8fbff",
                "strong_bg": "#deecff",
            },
            "ico": {
                "display": "ICO",
                "bar_color": "#84cc16",
                "bar_tint": "rgba(132, 204, 22, 0.16)",
                "header_bg": "#f3fae8",
                "soft_bg": "#fbfdf5",
                "strong_bg": "#edf7d8",
            },
            "sakari": {
                "display": "SAKARI",
                "bar_color": "#f59e0b",
                "bar_tint": "rgba(245, 158, 11, 0.16)",
                "header_bg": "#fff6e8",
                "soft_bg": "#fffbf5",
                "strong_bg": "#feedd1",
            },
        }

    def _build_v3_top10_rows(
        self,
        source_rows: list[dict[str, Any]],
        *,
        current_total: float,
        previous_total: float,
    ) -> list[dict[str, Any]]:
        """Build rendered Top 10 rows with visual metadata."""
        result: list[dict[str, Any]] = []
        area_visual_map = self._get_v3_area_visual_map()
        max_top10_current = max(
            [float(item.get("current") or 0.0) for item in source_rows],
            default=0.0,
        )

        for index, item in enumerate(source_rows, start=1):
            current_value = item.get("current")
            previous_value = item.get("previous")

            current_ratio = None
            previous_ratio = None

            if current_total > 0 and current_value is not None:
                current_ratio = float(current_value) / current_total

            if previous_total > 0 and previous_value is not None:
                previous_ratio = float(previous_value) / previous_total

            normalized_area = str(item.get("area") or "").strip().lower()
            if normalized_area not in area_visual_map:
                normalized_area = "diode"
            area_visual = area_visual_map[normalized_area]

            meter_fill_pct = 0.0
            if max_top10_current > 0 and current_value is not None:
                meter_fill_pct = max(
                    18.0,
                    min(100.0, (float(current_value) / max_top10_current) * 100.0),
                )

            result.append({
                "rank": item.get("rank") or index,
                "meter_key": item.get("meter_name"),
                "meter_name": item.get("meter_name"),
                "display_name": item.get("meter_name"),
                "area": normalized_area,
                "area_display": area_visual["display"],
                "area_key": normalized_area,
                "meter_fill_pct": round(meter_fill_pct, 2),
                "meter_bar_color": area_visual["bar_color"],
                "meter_bar_tint": area_visual["bar_tint"],
                "current_display": self._fmt(current_value),
                "current_pct_display": self._fmt_pct(current_ratio) if current_ratio is not None else "-",
                "previous_display": self._fmt(previous_value),
                "previous_pct_display": self._fmt_pct(previous_ratio) if previous_ratio is not None else "-",
                "delta_display": self._fmt(item.get("delta")),
                "delta_pct_display": self._fmt_pct(item.get("delta_pct")),
                "delta_class": self._consumption_trend_class(item.get("delta")),
                "delta_pct_class": self._consumption_trend_class(item.get("delta_pct")),
            })

        return result

    def _sum_meter_totals_for_v3_table(self, table: Dict[str, Any]) -> dict[str, float]:
        """Sum meter totals for one rendered daily table, excluding configured feeders."""
        excluded_columns = set(table.get("exclude_from_top10", []))
        valid_columns = [
            column
            for column in table.get("meter_columns", [])
            if column not in excluded_columns
        ]

        result: dict[str, float] = {}

        for column in valid_columns:
            total = 0.0
            has_numeric_data = False

            for row in table.get("rows", []):
                for cell in row.get("cells", []):
                    if cell.get("key") != column:
                        continue

                    raw_value = cell.get("raw_value")
                    if isinstance(raw_value, (int, float)):
                        total += float(raw_value)
                        has_numeric_data = True

            if has_numeric_data:
                result[column] = round(total, 4)

        return result

    def _build_v3_area_top10_tables(
        self,
        energy_object: Optional[Dict[str, Any]],
        area_display_order: list[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        """Build one Top 10 table per area."""
        if not energy_object:
            return []

        current_summary = energy_object.get("current", {}).get("summary", {})
        previous_summary = energy_object.get("previous", {}).get("summary", {})

        current_table_lookup = {
            table.get("area_key"): table
            for table in energy_object.get("current", {}).get("daily_tables", [])
        }
        previous_table_lookup = {
            table.get("area_key"): table
            for table in energy_object.get("previous", {}).get("daily_tables", [])
        }

        result: list[dict[str, Any]] = []

        for area_key, area_name in area_display_order:
            current_table = current_table_lookup.get(area_key, {})
            previous_table = previous_table_lookup.get(area_key, {})

            current_meter_totals = self._sum_meter_totals_for_v3_table(current_table)
            previous_meter_totals = self._sum_meter_totals_for_v3_table(previous_table)

            source_rows: list[dict[str, Any]] = []

            for meter_name, current_value in sorted(
                current_meter_totals.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:10]:
                previous_value = previous_meter_totals.get(meter_name, 0.0)
                delta = current_value - previous_value
                delta_pct = (delta / previous_value) if previous_value != 0 else None

                source_rows.append({
                    "meter_name": meter_name,
                    "area": area_key,
                    "current": current_value,
                    "previous": previous_value,
                    "delta": round(delta, 4),
                    "delta_pct": round(delta_pct, 4) if delta_pct is not None else None,
                })

            rendered_rows = self._build_v3_top10_rows(
                source_rows,
                current_total=float(current_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0),
                previous_total=float(previous_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0),
            )

            result.append({
                "area_key": area_key,
                "title": f"{area_name} Top 10 meters",
                "subtitle": "Sorted by current-period consumption within this area.",
                "rows": rendered_rows,
            })

        return result

    def _build_v3_grouped_top10_rows(
        self,
        plant_rows: list[dict[str, Any]],
        area_tables: list[dict[str, Any]],
        area_display_order: list[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        """Merge plant and area Top 10 rankings into one grouped row layout."""
        area_row_lookup = {
            table.get("area_key"): table.get("rows", [])
            for table in area_tables
        }

        max_length = max(
            [len(plant_rows)]
            + [len(area_row_lookup.get(area_key, [])) for area_key, _ in area_display_order],
            default=0,
        )

        grouped_rows: list[dict[str, Any]] = []

        for index in range(max_length):
            plant_row = plant_rows[index] if index < len(plant_rows) else None
            grouped_rows.append({
                "rank": plant_row.get("rank") if plant_row else index + 1,
                "plant": plant_row,
                "areas": {
                    area_key: (
                        area_row_lookup.get(area_key, [])[index]
                        if index < len(area_row_lookup.get(area_key, []))
                        else None
                    )
                    for area_key, _ in area_display_order
                },
            })

        return grouped_rows

    def _build_v3_area_daily_summary_rows(
        self,
        plant_daily_summary_rows: list[dict[str, Any]],
        daily_tables: list[dict[str, Any]],
        area_display_order: list[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        """Build the additional daily summary table split by workshop area."""
        plant_row_lookup = {
            row.get("date"): row
            for row in plant_daily_summary_rows
            if row.get("date") is not None
        }
        table_lookup = {
            table.get("area_key"): table
            for table in daily_tables
        }
        row_lookup: dict[str, dict[date, dict[str, Any]]] = {}
        all_dates: set[date] = set(plant_row_lookup.keys())

        for area_key, _area_name in area_display_order:
            rows = {
                row.get("date"): row
                for row in table_lookup.get(area_key, {}).get("rows", [])
                if row.get("date") is not None
            }
            row_lookup[area_key] = rows
            all_dates.update(rows.keys())

        result: list[dict[str, Any]] = []

        for dt_value in sorted(all_dates):
            area_values: dict[str, dict[str, Any]] = {}

            plant_row = plant_row_lookup.get(dt_value)
            if plant_row:
                area_values["plant"] = {
                    "area_key": "plant",
                    "area_name": "Plant",
                    "total_display": plant_row.get("total_energy_display", "-"),
                    "active_total_display": f"{plant_row.get('active_meter_count', '-')}/{plant_row.get('total_meter_count', '-')}",
                    "avg_per_active_display": plant_row.get("avg_per_active_display", "-"),
                }
            else:
                area_values["plant"] = {
                    "area_key": "plant",
                    "area_name": "Plant",
                    "total_display": "-",
                    "active_total_display": "-",
                    "avg_per_active_display": "-",
                }

            for area_key, area_name in area_display_order:
                row = row_lookup.get(area_key, {}).get(dt_value)

                if not row:
                    area_values[area_key] = {
                        "area_key": area_key,
                        "area_name": area_name,
                        "total_display": "-",
                        "active_total_display": "-",
                        "avg_per_active_display": "-",
                    }
                    continue

                total_meter_count = len(row.get("cells", []))
                active_meter_count = sum(
                    1
                    for cell in row.get("cells", [])
                    if isinstance(cell.get("raw_value"), (int, float))
                    and float(cell.get("raw_value")) > 0
                )

                total_energy = row.get("official_daily_total")
                average_per_active = None
                if total_energy is not None:
                    average_per_active = (
                        float(total_energy) / active_meter_count
                        if active_meter_count > 0 else 0.0
                    )

                area_values[area_key] = {
                    "area_key": area_key,
                    "area_name": area_name,
                    "total_display": self._fmt_or_dash(total_energy),
                    "active_total_display": f"{active_meter_count}/{total_meter_count}",
                    "avg_per_active_display": self._fmt_or_dash(average_per_active),
                }

            result.append({
                "date": dt_value,
                "date_display": self._format_date_with_weekday(dt_value),
                "areas": area_values,
            })

        return result

    def _build_v3_daily_vertical_detail_tables(
        self,
        daily_tables: list[dict[str, Any]],
        *,
        column_count: int = 3,
    ) -> list[dict[str, Any]]:
        """Build portrait-friendly meter/value columns for the daily report."""
        result: list[dict[str, Any]] = []
        area_visual_map = self._get_v3_area_visual_map()

        for table in daily_tables:
            rows = sorted(
                table.get("rows", []),
                key=lambda row: row.get("date") or datetime.min.date(),
            )
            if not rows:
                continue

            area_key = str(table.get("area_key") or "").strip().lower()
            area_visual = area_visual_map.get(area_key, area_visual_map.get("diode", {}))

            detail_row = rows[-1]
            meter_columns = table.get("columns", [])[1:]
            meter_cells = detail_row.get("cells", [])

            max_numeric = max(
                [float(cell.get("raw_value") or 0.0) for cell in meter_cells if isinstance(cell.get("raw_value"), (int, float))],
                default=0.0,
            )

            entries: list[dict[str, Any]] = []
            for column, cell in zip(meter_columns, meter_cells):
                raw_value = cell.get("raw_value")
                fill_pct = 0.0
                if isinstance(raw_value, (int, float)) and raw_value > 0 and max_numeric > 0:
                    fill_pct = max(4.0, min(100.0, (float(raw_value) / max_numeric) * 100.0))

                entries.append({
                    "meter_name": column.get("display_name") or cell.get("key") or "-",
                    "display": cell.get("display", "-"),
                    "raw_value": raw_value,
                    "fill_pct": round(fill_pct, 2),
                    "heat_class": cell.get("heat_class", ""),
                    "is_max": bool(cell.get("is_row_max")),
                    "is_zero": cell.get("display") in {"0", "0.0", "0.00", "-"},
                })

            if not entries:
                continue

            entries.sort(
                key=lambda entry: (
                    0 if isinstance(entry.get("raw_value"), (int, float)) else 1,
                    -(float(entry.get("raw_value") or 0.0)) if isinstance(entry.get("raw_value"), (int, float)) else 0.0,
                    str(entry.get("meter_name") or ""),
                ),
            )

            for entry_index, entry in enumerate(entries, start=1):
                entry["index"] = entry_index

            safe_column_count = max(1, column_count)
            chunk_size = max(1, (len(entries) + safe_column_count - 1) // safe_column_count)
            column_groups = [
                entries[index:index + chunk_size]
                for index in range(0, len(entries), chunk_size)
            ]

            result.append({
                "area_key": area_key,
                "title": table.get("title") or "Daily Energy Detail",
                "date_display": detail_row.get("date_display", "-"),
                "accent_color": area_visual.get("bar_color", "#2563eb"),
                "accent_tint": area_visual.get("bar_tint", "rgba(37, 99, 235, 0.12)"),
                "accent_header_bg": area_visual.get("header_bg", "#eef5ff"),
                "accent_soft_bg": area_visual.get("soft_bg", "#f8fbff"),
                "accent_strong_bg": area_visual.get("strong_bg", "#deecff"),
                "column_groups": column_groups,
            })

        return result

    def _build_v3_electricity_section(
        self,
        energy_object: Optional[Dict[str, Any]],
        period_type: str = "",
    ) -> Dict[str, Any]:
        """
        Build V3 electricity section from energy object.

        This version reuses the existing energy object contract and maps it
        into the new V3 section structure:
        - totals
        - comparison
        - top10
        - daily summary
        - daily detail tables

        Args:
            energy_object: Prepared energy domain object.

        Returns:
            Dict[str, Any]: V3 electricity section.

        Example:
            section = self._build_v3_electricity_section(energy_object)
        """
        if not energy_object:
            return {
                "title": "ELECTRICITY CONSUMPTION",
                "subtitle": "Total, comparison, top meters, and daily detail.",
                "totals": {"rows": []},
                "comparison": {"rows": []},
                "top10": {"rows": [], "area_tables": [], "excluded_meter_rules": {}},
                "charts": {
                    "daily_trend": {},
                    "area_comparison": {},
                    "period_heatmap": {},
                    "period_area_delta": {},
                },
                "daily_summary": {"title": "Daily Summary Table", "rows": [], "area_rows": []},
                "daily_detail_tables": [],
            }

        area_display_order = [
            ("diode", "DIODE Workshop"),
            ("ico", "ICO Workshop"),
            ("sakari", "SAKARI Workshop"),
        ]

        current_summary = energy_object.get("current", {}).get("summary", {})
        comparison_summary = energy_object.get("comparison", {}).get("summary", {})
        area_stats = self._build_v3_electricity_area_stats(energy_object)

        total_rows: list[dict[str, Any]] = []
        comparison_rows: list[dict[str, Any]] = []

        for area_key, area_name in area_display_order:
            current_item = current_summary.get(area_key, {})
            comparison_item = comparison_summary.get(area_key, {})

            total_rows.append({
                "area_key": area_key,
                "area_name": area_name,
                "current_display": self._fmt(current_item.get("total_energy")),
                "previous_display": self._fmt(
                    energy_object.get("previous", {})
                    .get("summary", {})
                    .get(area_key, {})
                    .get("total_energy")
                ),
                "meter_count": current_item.get("meter_count", 0),
                "meter_active_total_display": area_stats.get(area_key, {}).get("active_total_display", "-"),
            })

            comparison_rows.append({
                "area_key": area_key,
                "area_name": area_name,
                "current_display": self._fmt(comparison_item.get("current")),
                "previous_display": self._fmt(comparison_item.get("previous")),
                "delta_display": self._fmt(comparison_item.get("delta")),
                "delta_pct_display": self._fmt_pct(comparison_item.get("delta_pct")),
                "delta_class": self._consumption_trend_class(comparison_item.get("delta")),
                "delta_pct_class": self._consumption_trend_class(comparison_item.get("delta_pct")),
                "meter_count": comparison_item.get("meter_count", 0),
                "current_ratio_display": area_stats.get(area_key, {}).get("current_ratio_display", "-"),
                "previous_ratio_display": area_stats.get(area_key, {}).get("previous_ratio_display", "-"),
                "active_total_display": area_stats.get(area_key, {}).get("active_total_display", "-"),
            })

        current_total_all_areas = 0.0
        previous_total_all_areas = 0.0

        for area_key in ["diode", "ico", "sakari"]:
            current_total_all_areas += float(
                current_summary.get(area_key, {}).get("total_energy", 0.0) or 0.0
            )
            previous_total_all_areas += float(
                energy_object.get("previous", {})
                .get("summary", {})
                .get(area_key, {})
                .get("total_energy", 0.0) or 0.0
            )

        top10_source_rows = energy_object.get("comparison", {}).get("top10_meters", [])
        top10_rows = self._build_v3_top10_rows(
            top10_source_rows,
            current_total=current_total_all_areas,
            previous_total=previous_total_all_areas,
        )
        area_top10_tables = self._build_v3_area_top10_tables(
            energy_object=energy_object,
            area_display_order=area_display_order,
        )

        daily_summary_rows = energy_object.get("current", {}).get("daily_summary_rows", [])
        daily_detail_tables = energy_object.get("current", {}).get("daily_tables", [])
        grouped_top10_rows = self._build_v3_grouped_top10_rows(
            plant_rows=top10_rows,
            area_tables=area_top10_tables,
            area_display_order=area_display_order,
        )
        area_daily_summary_rows = self._build_v3_area_daily_summary_rows(
            plant_daily_summary_rows=daily_summary_rows,
            daily_tables=daily_detail_tables,
            area_display_order=area_display_order,
        )
        daily_vertical_detail_tables = self._build_v3_daily_vertical_detail_tables(
            daily_detail_tables,
            column_count=3,
        )
        charts = self._build_v3_electricity_charts(
            energy_object=energy_object,
            period_type=period_type,
        )

        return {
            "title": "ELECTRICITY CONSUMPTION",
            "subtitle": "Total, comparison, top meters, and daily detail.",
            "totals": {
                "rows": total_rows,
            },
            "comparison": {
                "rows": comparison_rows,
            },
            "top10": {
                "rows": top10_rows,
                "grouped_rows": grouped_top10_rows,
                "area_tables": area_top10_tables,
                "group_columns": [
                    {"key": "plant", "label": "Plant Meter"},
                    {"key": "diode", "label": "Diode Meter"},
                    {"key": "ico", "label": "ICO Meter"},
                    {"key": "sakari", "label": "SAKARI Meter"},
                ],
                "excluded_meter_rules": {},
            },
            "charts": charts,
            "daily_summary": {
                "title": "Daily Summary Table",
                "rows": daily_summary_rows,
                "area_rows": area_daily_summary_rows,
            },
            "daily_detail_tables": daily_detail_tables,
            "daily_vertical_detail_tables": daily_vertical_detail_tables,
        }

    def _build_v3_electricity_charts(
        self,
        energy_object: Optional[Dict[str, Any]],
        period_type: str = "",
    ) -> Dict[str, Any]:
        """Build ECharts options for the electricity section."""
        if not energy_object:
            return {
                "daily_trend": {},
                "area_comparison": {},
                "period_heatmap": {},
                "period_area_delta": {},
            }

        current_daily_rows = sorted(
            energy_object.get("current", {}).get("daily_summary_rows", []),
            key=lambda row: row.get("date") or datetime.min.date(),
        )
        previous_daily_rows = sorted(
            energy_object.get("previous", {}).get("daily_summary_rows", []),
            key=lambda row: row.get("date") or datetime.min.date(),
        )

        is_weekly_or_monthly = period_type in {"weekly", "monthly"}

        if is_weekly_or_monthly:
            current_daily_values = self._build_periodic_energy_trend_values(
                energy_period_object=energy_object.get("current", {}) or {},
            )
            previous_daily_values = self._build_periodic_energy_trend_values(
                energy_period_object=energy_object.get("previous", {}) or {},
            )
        else:
            current_daily_values = [
                self._parse_display_number(row.get("total_energy_display"))
                for row in current_daily_rows
            ]
            previous_daily_values = [
                self._parse_display_number(row.get("total_energy_display"))
                for row in previous_daily_rows
            ]

        max_daily_points = max(len(current_daily_values), len(previous_daily_values))
        if is_weekly_or_monthly:
            daily_labels = self._build_periodic_energy_trend_labels(
                current_daily_rows=current_daily_rows,
                previous_daily_rows=previous_daily_rows,
                max_daily_points=max_daily_points,
                period_type=period_type,
            )
        else:
            daily_labels = [f"D{index}" for index in range(1, max_daily_points + 1)]

        if len(current_daily_values) < max_daily_points:
            current_daily_values.extend([None] * (max_daily_points - len(current_daily_values)))
        if len(previous_daily_values) < max_daily_points:
            previous_daily_values.extend([None] * (max_daily_points - len(previous_daily_values)))

        area_rows: list[dict[str, Any]] = []
        for area_key, area_name in [
            ("diode", "DIODE"),
            ("ico", "ICO"),
            ("sakari", "SAKARI"),
        ]:
            area_visual = self._get_v3_area_visual_map().get(area_key, {})
            current_value = float(
                energy_object.get("current", {})
                .get("summary", {})
                .get(area_key, {})
                .get("total_energy", 0.0) or 0.0
            )
            previous_value = float(
                energy_object.get("previous", {})
                .get("summary", {})
                .get(area_key, {})
                .get("total_energy", 0.0) or 0.0
            )

            area_rows.append({
                "area_name": area_name,
                "current_value": current_value,
                "previous_value": previous_value,
                "color": area_visual.get("bar_color", "#2563eb"),
            })

        area_labels = [row["area_name"] for row in area_rows]
        current_area_values = [row["current_value"] for row in area_rows]
        previous_area_values = [row["previous_value"] for row in area_rows]

        if period_type == "daily":
            current_total_value = sum(current_area_values)
            share_chart = {
                "title": "Area share",
                "subtitle": "Current day contribution by workshop",
                "option": self._build_v3_contribution_donut_option(
                    items=[
                        {
                            "name": row["area_name"],
                            "value": row["current_value"],
                            "itemStyle": {
                                "color": row["color"],
                            },
                        }
                        for row in area_rows
                    ],
                    total_value=current_total_value,
                    slice_border_radius=6,
                    pie_radius=("39%", "60%"),
                    pie_center=("50%", "58%"),
                    graphic_left="43%",
                    graphic_top="50%",
                    legend_orient="horizontal",
                    legend_left="center",
                    legend_right=0,
                    legend_top="3%",
                    center_value_font_size=10,
                    center_title_font_size=8,
                    center_unit_font_size=7,
                    center_title_y=15,
                    center_unit_y=24,
                ),
            }
            periodic_heatmap_chart = {}
            periodic_area_delta_chart = {}
        else:
            share_chart = {
                "title": "Daily trend",
                "subtitle": "Current vs previous period",
                "option": {
                    "color": ["#2563eb", "#7c3aed"],
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "line"},
                    },
                    "legend": {
                        "top": 6,
                        "left": 8,
                        "itemWidth": 12,
                        "itemHeight": 8,
                    },
                    "grid": {
                        "left": 26,
                        "right": 12,
                        "top": 36,
                        "bottom": 46,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": daily_labels,
                        "axisLabel": {
                            "color": "#64748b",
                            "interval": 0,
                            "rotate": 28,
                            "fontSize": 9,
                        },
                        "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {"color": "#64748b"},
                        "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
                    },
                    "series": [
                        {
                            "name": "Current period",
                            "type": "line",
                            "smooth": False,
                            "symbol": "circle",
                            "symbolSize": 8,
                            "showSymbol": True,
                            "lineStyle": {"width": 3, "color": "#2563eb"},
                            "itemStyle": {"color": "#2563eb"},
                            "areaStyle": {"color": "rgba(37, 99, 235, 0.12)"},
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": "{c}",
                                "fontSize": 8,
                                "color": "#1d4ed8",
                                "backgroundColor": "rgba(255,255,255,0.92)",
                                "padding": [2, 4],
                                "borderRadius": 4,
                            },
                            "data": current_daily_values,
                        },
                        {
                            "name": "Previous period",
                            "type": "line",
                            "smooth": False,
                            "symbol": "circle",
                            "symbolSize": 7,
                            "showSymbol": True,
                            "lineStyle": {"width": 2, "type": "dashed", "color": "#7c3aed"},
                            "itemStyle": {"color": "#7c3aed"},
                            "areaStyle": {"color": "rgba(124, 58, 237, 0.08)"},
                            "label": {
                                "show": True,
                                "position": "bottom",
                                "formatter": "{c}",
                                "fontSize": 8,
                                "color": "#6d28d9",
                                "backgroundColor": "rgba(255,255,255,0.9)",
                                "padding": [2, 4],
                                "borderRadius": 4,
                            },
                            "data": previous_daily_values,
                        },
                    ],
                },
            }
            periodic_heatmap_chart = self._build_v3_periodic_electricity_heatmap_chart(
                plant_daily_summary_rows=current_daily_rows,
                daily_tables=energy_object.get("current", {}).get("daily_tables", []) or [],
                period_type=period_type,
            )
            periodic_area_delta_chart = self._build_v3_periodic_area_delta_chart(
                energy_object=energy_object,
                area_rows=area_rows,
            )

        return {
            "daily_trend": share_chart,
            "area_comparison": {
                "title": "Area comparison",
                "subtitle": "Current vs previous total by workshop",
                "option": {
                    "color": ["#2563eb", "#7c3aed"],
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                    },
                    "legend": {
                        "top": 6,
                        "left": 8,
                        "itemWidth": 12,
                        "itemHeight": 8,
                    },
                    "grid": {
                        "left": 32,
                        "right": 12,
                        "top": 56,
                        "bottom": 38,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "data": area_labels,
                        "axisLabel": {
                            "color": "#64748b",
                            "interval": 0,
                            "rotate": 18,
                            "fontSize": 9,
                            "margin": 12,
                            "hideOverlap": False,
                        },
                        "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                        "axisTick": {"alignWithLabel": True},
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {"color": "#64748b"},
                        "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
                    },
                    "series": [
                        {
                            "name": "Current period",
                            "type": "bar",
                            "barMaxWidth": 22,
                            "labelLayout": {
                                "hideOverlap": True,
                            },
                            "data": [
                                self._build_chart_bar_point(
                                    value,
                                    color="#2563eb",
                                    font_size=8,
                                    label_rotate=16,
                                    label_distance=4,
                                    formatter=self._fmt_chart_compact(value),
                                )
                                for value in current_area_values
                            ],
                        },
                        {
                            "name": "Previous period",
                            "type": "bar",
                            "barMaxWidth": 22,
                            "labelLayout": {
                                "hideOverlap": True,
                            },
                            "data": [
                                self._build_chart_bar_point(
                                    value,
                                    color="#7c3aed",
                                    font_size=8,
                                    label_rotate=16,
                                    label_distance=4,
                                    formatter=self._fmt_chart_compact(value),
                                )
                                for value in previous_area_values
                            ],
                        },
                    ],
                },
            },
            "period_heatmap": periodic_heatmap_chart,
            "period_area_delta": periodic_area_delta_chart,
        }

    def _build_v3_periodic_area_delta_chart(
        self,
        *,
        energy_object: Dict[str, Any],
        area_rows: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a compact area delta chart for periodic electricity reports."""
        if not area_rows:
            return {}

        total_current_value = float(
            energy_object.get("current", {}).get("summary", {}).get("plant", {}).get("total_energy", 0.0) or 0.0
        )
        total_previous_value = float(
            energy_object.get("previous", {}).get("summary", {}).get("plant", {}).get("total_energy", 0.0) or 0.0
        )

        delta_source_rows = [
            {
                "area_name": "TOTAL",
                "current_value": total_current_value,
                "previous_value": total_previous_value,
                "color": "#14b8a6",
            },
            *area_rows,
        ]

        delta_items: list[dict[str, Any]] = []
        for row in delta_source_rows:
            current_value = float(row.get("current_value") or 0.0)
            previous_value = float(row.get("previous_value") or 0.0)
            delta_value = round(current_value - previous_value, 4)
            delta_pct = (delta_value / previous_value) if previous_value not in (0, 0.0) else None
            base_color = row.get("color") or "#2563eb"
            label_text = self._fmt_chart_compact(delta_value)
            if delta_pct is not None:
                label_text = f"{label_text} ({self._fmt_pct(delta_pct)})"

            delta_items.append({
                "name": row.get("area_name") or "-",
                "value": delta_value,
                "itemStyle": {
                    "color": base_color,
                    "opacity": 0.95 if delta_value >= 0 else 0.55,
                    "borderRadius": [0, 7, 7, 0] if delta_value >= 0 else [7, 0, 0, 7],
                },
                "label": {
                    "show": True,
                    "position": "right" if delta_value >= 0 else "left",
                    "distance": 6,
                    "formatter": label_text,
                    "fontSize": 8,
                    "fontWeight": 700,
                    "color": "#334155",
                },
            })

        max_abs = max([abs(float(item.get("value") or 0.0)) for item in delta_items], default=0.0)
        axis_limit = max(1.0, round(max_abs * 1.35, 2))

        return {
            "title": "Consumption delta",
            "subtitle": "Total and workshop change vs previous period",
            "option": {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {"type": "shadow"},
                },
                "grid": {
                    "left": 72,
                    "right": 22,
                    "top": 8,
                    "bottom": 10,
                    "containLabel": False,
                },
                "xAxis": {
                    "type": "value",
                    "min": -axis_limit,
                    "max": axis_limit,
                    "axisLabel": {
                        "color": "#64748b",
                        "fontSize": 8,
                    },
                    "splitLine": {
                        "lineStyle": {
                            "color": "#e2e8f0",
                            "type": "dashed",
                        }
                    },
                },
                "yAxis": {
                    "type": "category",
                    "inverse": True,
                    "data": [item.get("name") for item in delta_items],
                    "axisTick": {"show": False},
                    "axisLine": {"show": False},
                    "axisLabel": {
                        "color": "#334155",
                        "fontWeight": 700,
                        "fontSize": 9,
                    },
                },
                "series": [
                    {
                        "name": "Delta",
                        "type": "bar",
                        "barWidth": 24,
                        "barCategoryGap": "34%",
                        "data": delta_items,
                        "markLine": {
                            "silent": True,
                            "symbol": ["none", "none"],
                            "lineStyle": {
                                "color": "#94a3b8",
                                "width": 1,
                            },
                            "data": [{"xAxis": 0}],
                        },
                    }
                ],
            },
        }

    def _build_v3_periodic_electricity_heatmap_chart(
        self,
        *,
        plant_daily_summary_rows: list[dict[str, Any]],
        daily_tables: list[dict[str, Any]],
        period_type: str,
    ) -> Dict[str, Any]:
        """Build a compact periodic heatmap under the daily trend chart."""
        area_summary_rows = self._build_v3_area_daily_summary_rows(
            plant_daily_summary_rows=plant_daily_summary_rows,
            daily_tables=daily_tables,
            area_display_order=[
                ("diode", "DIODE Workshop"),
                ("ico", "ICO Workshop"),
                ("sakari", "SAKARI Workshop"),
            ],
        )

        if not area_summary_rows:
            return {}

        x_labels = [
            self._format_heatmap_column_label(row.get("date"), period_type)
            for row in area_summary_rows
        ]
        x_labels.append("Avg")

        row_defs = [
            ("plant", "TOTAL"),
            ("diode", "DIODE"),
            ("ico", "ICO"),
            ("sakari", "SAKARI"),
        ]

        y_labels = [label for _key, label in row_defs]
        row_value_map: list[list[float | None]] = []

        for area_key, _label in row_defs:
            values: list[float | None] = []
            for day_row in area_summary_rows:
                area_row = (day_row.get("areas") or {}).get(area_key, {})
                raw_value = self._parse_display_number(area_row.get("total_display"))
                values.append(raw_value)

            numeric_values = [value for value in values if value is not None]
            avg_value = (
                round(sum(numeric_values) / len(numeric_values), 2)
                if numeric_values else None
            )
            values.append(avg_value)
            row_value_map.append(values)

        if not any(any(value is not None for value in row_values) for row_values in row_value_map):
            return {}

        bottom_gap = 44 if len(x_labels) <= 8 else 62
        label_rotate = 0 if len(x_labels) <= 8 else 28
        label_font_size = 9 if len(x_labels) <= 8 else 8

        area_visual_map = self._get_v3_area_visual_map()
        row_palettes = {
            "plant": {"bar_color": "#14b8a6"},
            "diode": area_visual_map.get("diode", {}),
            "ico": area_visual_map.get("ico", {}),
            "sakari": area_visual_map.get("sakari", {}),
        }

        heatmap_data = []
        for row_index, row_values in enumerate(row_value_map):
            row_key = row_defs[row_index][0]
            base_color = row_palettes.get(row_key, {}).get("bar_color", "#2563eb")
            numeric_row_values = [value for value in row_values if value is not None]
            row_min = min(numeric_row_values) if numeric_row_values else 0.0
            row_max = max(numeric_row_values) if numeric_row_values else 0.0
            row_span = row_max - row_min

            for col_index, raw_value in enumerate(row_values):
                if raw_value is None:
                    continue

                display_value = (
                    f"{raw_value:.2f}" if col_index == len(row_values) - 1 else f"{raw_value:.1f}"
                )
                intensity = 0.45
                if row_span > 0:
                    intensity = 0.28 + (0.68 * ((float(raw_value) - row_min) / row_span))

                heatmap_data.append({
                    "value": [col_index, row_index, round(raw_value, 4)],
                    "label": {
                        "formatter": display_value,
                    },
                    "itemStyle": {
                        "color": self._blend_hex_with_white(base_color, intensity),
                        "borderColor": "rgba(255,255,255,0.78)",
                        "borderWidth": 1,
                    },
                })

        return {
            "title": "Daily total heatmap",
            "subtitle": "kWh by area and total",
            "option": {
                "tooltip": {
                    "position": "top",
                },
                "grid": {
                    "left": 58,
                    "right": 18,
                    "top": 10,
                    "bottom": bottom_gap,
                    "containLabel": False,
                },
                "xAxis": {
                    "type": "category",
                    "data": x_labels,
                    "splitArea": {"show": False},
                    "axisLabel": {
                        "interval": 0,
                        "rotate": label_rotate,
                        "fontSize": label_font_size,
                        "color": "#475569",
                    },
                    "axisLine": {"lineStyle": {"color": "#dbe4ee"}},
                    "axisTick": {"show": False},
                },
                "yAxis": {
                    "type": "category",
                    "data": y_labels,
                    "axisLine": {"show": False},
                    "axisTick": {"show": False},
                    "axisLabel": {
                        "fontWeight": 700,
                        "color": "#334155",
                    },
                },
                "series": [
                    {
                        "name": "kWh total",
                        "type": "heatmap",
                        "data": heatmap_data,
                        "label": {
                            "show": True,
                            "fontSize": 8,
                            "fontWeight": 700,
                            "color": "#0f172a",
                        },
                        "emphasis": {
                            "itemStyle": {
                                "shadowBlur": 8,
                                "shadowColor": "rgba(15, 23, 42, 0.15)",
                            },
                        },
                    }
                ],
            },
        }

    def _build_periodic_energy_trend_values(
        self,
        *,
        energy_period_object: Dict[str, Any],
    ) -> list[float | None]:
        """Resolve periodic daily trend values with fallback to area daily totals."""
        summary_rows = sorted(
            energy_period_object.get("daily_summary_rows", []),
            key=lambda row: row.get("date") or datetime.min.date(),
        )
        summary_by_date = {
            row.get("date"): row
            for row in summary_rows
            if row.get("date") is not None
        }

        area_total_by_date: dict[date, float] = {}
        for table in energy_period_object.get("daily_tables", []) or []:
            for row in table.get("rows", []) or []:
                dt_value = row.get("date")
                official_total = row.get("official_daily_total")
                if dt_value is None or not isinstance(official_total, (int, float)):
                    continue
                area_total_by_date[dt_value] = (
                    area_total_by_date.get(dt_value, 0.0) + float(official_total)
                )

        all_dates = sorted(set(summary_by_date.keys()) | set(area_total_by_date.keys()))
        values: list[float | None] = []

        for dt_value in all_dates:
            summary_value = self._parse_display_number(
                summary_by_date.get(dt_value, {}).get("total_energy_display")
            )
            fallback_value = area_total_by_date.get(dt_value)

            if summary_value is None:
                resolved_value = fallback_value
            elif (
                summary_value == 0.0
                and isinstance(fallback_value, (int, float))
                and fallback_value > 0.0
            ):
                resolved_value = fallback_value
            else:
                resolved_value = summary_value

            values.append(round(float(resolved_value), 4) if resolved_value is not None else None)

        return values

    def _build_periodic_energy_trend_labels(
        self,
        *,
        current_daily_rows: list[dict[str, Any]],
        previous_daily_rows: list[dict[str, Any]],
        max_daily_points: int,
        period_type: str,
    ) -> list[str]:
        """Build aligned x-axis labels for periodic electricity trend charts."""
        if max_daily_points <= 0:
            return []

        label_source_rows = current_daily_rows if current_daily_rows else previous_daily_rows
        label_dates = [
            row.get("date")
            for row in label_source_rows
            if row.get("date") is not None
        ]

        normalized_period = str(period_type or "").strip().lower()
        if normalized_period in {"weekly", "monthly"} and len(label_dates) >= max_daily_points:
            return [self._format_periodic_axis_date_label(dt) for dt in label_dates[:max_daily_points]]

        return [f"D{index}" for index in range(1, max_daily_points + 1)]

    def _format_periodic_axis_date_label(self, value) -> str:
        """Format periodic chart x-axis label like Apr 14 (Mon)."""
        if value in (None, ""):
            return "-"

        if isinstance(value, str):
            value = datetime.fromisoformat(value).date()
        elif isinstance(value, datetime):
            value = value.date()

        if not isinstance(value, date):
            return str(value)

        return f"{value.strftime('%b')} {value.day} ({value.strftime('%a')})"

    def _format_heatmap_column_label(self, value, period_type: str) -> str:
        """Format compact heatmap column labels."""
        if value in (None, ""):
            return "-"

        if isinstance(value, str):
            value = datetime.fromisoformat(value).date()
        elif isinstance(value, datetime):
            value = value.date()

        if not isinstance(value, date):
            return str(value)

        normalized_period = str(period_type or "").strip().lower()
        if normalized_period == "weekly":
            return value.strftime("%a")

        return f"{value.strftime('%b')} {value.day}"

    def _blend_hex_with_white(self, hex_color: str, ratio: float) -> str:
        """Blend a hex color with white for heatmap cell tinting."""
        normalized = str(hex_color or "").strip().lstrip("#")
        if len(normalized) != 6:
            return "#e2e8f0"

        try:
            red = int(normalized[0:2], 16)
            green = int(normalized[2:4], 16)
            blue = int(normalized[4:6], 16)
        except ValueError:
            return "#e2e8f0"

        safe_ratio = max(0.0, min(1.0, float(ratio)))
        blended_red = round(255 - ((255 - red) * safe_ratio))
        blended_green = round(255 - ((255 - green) * safe_ratio))
        blended_blue = round(255 - ((255 - blue) * safe_ratio))
        return f"#{blended_red:02x}{blended_green:02x}{blended_blue:02x}"

    def _parse_display_number(self, value: Any) -> float | None:
        """Parse a formatted numeric display string back to float."""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text or text == "-":
            return None

        try:
            return float(text.replace(",", ""))
        except ValueError:
            return None

    def _build_v3_utility_section(
        self,
        utility_object: Optional[Dict[str, Any]],
        energy_object: Optional[Dict[str, Any]] = None,
        period: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build V3 utility section from utility object.

        This version maps the current utility contract into the new V3 layout:
        - consumption totals
        - daily detail
        - sensor monitoring placeholder

        Args:
            utility_object: Prepared utility domain object.

        Returns:
            Dict[str, Any]: V3 utility section.

        Example:
            section = self._build_v3_utility_section(utility_object)
        """
        if not utility_object:
            return {
                "title": "UTILITY OVERVIEW",
                "subtitle": "Consumption and sensor monitoring.",
                "unit_badge": "m³",
                "date_comparison": {
                    "current_label": "Today",
                    "previous_label": "Yesterday",
                    "current_display": "",
                    "previous_display": "",
                },
                "daily_dashboard": {
                    "overview_cards": [],
                    "variance_chart": {},
                },
                "energy": {
                    "enabled": False,
                    "title": "UTILITY ENERGY (CONVERTED TO kWh)",
                    "unit_badge": "kWh",
                    "overview_cards": [],
                    "detail_rows": [],
                },
                "consumption": {
                    "coverage": {},
                    "totals": {"rows": []},
                    "detail": {
                        "daily_columns": [],
                        "daily_rows": [],
                    },
                },
                "charts": {
                    "comparison_bar": {},
                },
                "sensor_monitoring": {
                    "enabled": False,
                    "sensor_count": 0,
                    "active_sensor_count": 0,
                    "overview_cards": [],
                    "groups": [],
                    "anomaly_rows": [],
                    "metric_columns": [],
                    "daily_rows": [],
                },
            }

        coverage = self._build_utility_coverage(utility_object)
        total_rows = self._build_utility_snapshot(utility_object)
        daily_columns = self._build_daily_columns(utility_object)
        daily_rows = self._build_daily_rows(utility_object)
        charts = self._build_v3_utility_charts(utility_object, period=period)
        overview_cards = self._build_v3_utility_overview_cards(utility_object)
        utility_energy = self._build_v3_utility_energy_context(
            utility_object=utility_object,
            energy_object=energy_object,
            period=period,
        )
        sensor_monitoring = {
            **(utility_object.get("current", {}).get("sensor_monitoring", {}) or {}),
        }
        sensor_monitoring["trend_clusters_render"] = self._build_v3_sensor_trend_clusters(sensor_monitoring)

        return {
            "title": "UTILITY OVERVIEW",
            "subtitle": "Consumption and sensor monitoring.",
            "unit_badge": self._resolve_utility_unit_badge(utility_object),
            "date_comparison": self._build_v3_utility_date_comparison(period),
            "daily_dashboard": {
                "overview_cards": overview_cards,
                "variance_chart": charts.get("deviation_vs_yesterday", {}),
            },
            "energy": utility_energy,
            "consumption": {
                "coverage": coverage,
                "totals": {
                    "rows": total_rows,
                },
                "detail": {
                    "daily_columns": daily_columns,
                    "daily_rows": daily_rows,
                },
            },
            "charts": charts,
            "sensor_monitoring": sensor_monitoring,
        }

    def _build_v3_utility_charts(
        self,
        utility_object: Optional[Dict[str, Any]],
        period: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build ECharts options for utility comparison."""
        if not utility_object:
            return {
                "comparison_bar": {},
                "deviation_vs_yesterday": {},
                "period_type_trend": {},
                "period_mix": {},
                "comparison_split": {
                    "wide": {},
                    "narrow": {},
                },
            }

        metadata = utility_object.get("current", {}).get("metadata", {})
        comparison = utility_object.get("comparison", {})

        utility_items: list[dict[str, Any]] = []

        for key, meta in metadata.items():
            display_name = meta.get("display_name") or key
            short_label = self._build_v3_utility_short_label(display_name)
            utility_items.append({
                "key": key,
                "display_name": display_name,
                "short_label": short_label,
                "chart_label": self._build_v3_utility_chart_label(short_label),
                "current": float(comparison.get(key, {}).get("current", 0.0) or 0.0),
                "previous": float(comparison.get(key, {}).get("previous", 0.0) or 0.0),
            })

        split_wide_items = [
            item for item in utility_items
            if "air" not in str(item.get("key") or "").strip().lower()
        ]
        split_narrow_items = [
            item for item in utility_items
            if "air" in str(item.get("key") or "").strip().lower()
        ]
        period_type = str((period or {}).get("type") or "").strip().lower()
        is_daily_report = period_type == "daily"

        return {
            "comparison_bar": {
                "title": "Utility comparison",
                "subtitle": "Current vs previous total by load type",
                "option": self._build_v3_utility_comparison_option(utility_items),
            },
            "deviation_vs_yesterday": {
                "title": "Deviation vs Yesterday (%)" if is_daily_report else "Consumption delta (%)",
                "subtitle": "Positive value means higher consumption" if is_daily_report else "Current period versus previous period",
                "option": self._build_v3_utility_deviation_option(utility_items),
            },
            "period_type_trend": {
                "title": "Utility daily trend",
                "subtitle": "Current period daily total by utility group",
                "option": self._build_v3_utility_type_trend_option(
                    utility_object=utility_object,
                    period_type=period_type,
                ),
            },
            "period_mix": {
                "title": "Current period mix",
                "subtitle": "Share of total utility consumption by group",
                "option": self._build_v3_utility_mix_option(utility_items),
            },
            "comparison_split": {
                "wide": {
                    "title": "Utility comparison",
                    "subtitle": "Water and steam",
                    "option": self._build_v3_utility_comparison_option(split_wide_items),
                },
                "narrow": {
                    "title": "Utility comparison",
                    "subtitle": "Air",
                    "option": self._build_v3_utility_comparison_option(split_narrow_items),
                },
            },
        }

    def _build_v3_utility_short_label(self, display_name: str) -> str:
        """Build shorter utility labels for compact periodic charts."""
        label = str(display_name or "").strip()
        if not label:
            return "-"

        lower_label = label.lower()
        if lower_label.endswith("chilled water"):
            suffix = "CHW"
            prefix_source = label[: -len("Chilled Water")].strip()
        elif lower_label.endswith("water"):
            suffix = "Water"
            prefix_source = label[: -len("Water")].strip()
        elif lower_label.endswith("air"):
            suffix = "Air"
            prefix_source = label[: -len("Air")].strip()
        elif lower_label.endswith("steam"):
            suffix = "Steam"
            prefix_source = label[: -len("Steam")].strip()
        else:
            return label

        prefix_alias_map = {
            "domestic": "Dom",
            "sakari": "SAK",
            "diode": "DIODE",
            "ico": "ICO",
        }
        prefix = prefix_alias_map.get(prefix_source.strip().lower(), prefix_source.strip())
        if not prefix:
            return suffix
        return f"{prefix} {suffix}".strip()

    def _build_v3_utility_chart_label(self, display_name: str) -> str:
        """Wrap utility chart labels for compact chart cards."""
        normalized = str(display_name or "").strip()
        if not normalized:
            return "-"
        if " " in normalized:
            first, second = normalized.rsplit(" ", 1)
            return f"{first}\n{second}"
        return normalized

    def _build_chart_bar_point(
        self,
        value: Any,
        *,
        color: str,
        border_radius: list[int] | None = None,
        font_size: int = 10,
        formatter: str | None = None,
        label_rotate: int = 28,
        label_distance: int = 6,
    ) -> dict[str, Any]:
        """Build one bar datum with a compact value label above the bar."""
        point = {
            "value": round(float(value), 4) if isinstance(value, (int, float)) else None,
            "itemStyle": {
                "color": color,
                "borderRadius": border_radius or [6, 6, 0, 0],
            },
        }

        if isinstance(value, (int, float)):
            point["label"] = {
                "show": True,
                "position": "top",
                "distance": label_distance,
                "rotate": label_rotate,
                "formatter": formatter or self._fmt_chart_callout(value),
                "color": "#475569",
                "fontSize": font_size,
                "fontWeight": 700,
            }
        else:
            point["label"] = {"show": False}

        return point

    def _build_v3_utility_comparison_option(
        self,
        items: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build one grouped utility comparison bar chart option."""
        chart_labels = [item.get("chart_label") or item.get("display_name") or "-" for item in items]
        current_values = [float(item.get("current") or 0.0) for item in items]
        previous_values = [float(item.get("previous") or 0.0) for item in items]

        return {
            "color": ["#2563eb", "#7c3aed"],
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"},
            },
            "legend": {
                "top": 6,
                "left": 8,
                "itemWidth": 12,
                "itemHeight": 8,
            },
            "grid": {
                "left": 28,
                "right": 10,
                "top": 42,
                "bottom": 32,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "data": chart_labels,
                "axisLabel": {
                    "color": "#64748b",
                    "fontSize": 9,
                    "lineHeight": 10,
                    "interval": 0,
                },
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": "#64748b"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "series": [
                {
                    "name": "Current period",
                    "type": "bar",
                    "barMaxWidth": 24,
                    "data": [
                        self._build_chart_bar_point(
                            value,
                            color="#2563eb",
                            font_size=8,
                            label_rotate=16,
                            label_distance=4,
                            formatter=self._fmt_chart_compact(value),
                        )
                        for value in current_values
                    ],
                },
                {
                    "name": "Previous period",
                    "type": "bar",
                    "barMaxWidth": 24,
                    "data": [
                        self._build_chart_bar_point(
                            value,
                            color="#7c3aed",
                            font_size=8,
                            label_rotate=16,
                            label_distance=4,
                            formatter=self._fmt_chart_compact(value),
                        )
                        for value in previous_values
                    ],
                },
            ],
        }

    def _build_v3_utility_type_trend_option(
        self,
        *,
        utility_object: Optional[Dict[str, Any]],
        period_type: str,
    ) -> Dict[str, Any]:
        """Build daily utility trend lines grouped by utility type."""
        if not utility_object:
            return {}

        metadata = utility_object.get("current", {}).get("metadata", {}) or {}
        timeseries = utility_object.get("current", {}).get("timeseries", []) or []
        if not metadata or not timeseries:
            return {}

        category_defs = [
            ("water", "Water", "#2563eb"),
            ("compressed_air", "Air", "#16a34a"),
            ("chilled_water", "CHW", "#0ea5b7"),
            ("steam", "Steam", "#7c3aed"),
        ]

        labels: list[str] = []
        series_values: dict[str, list[float | None]] = {key: [] for key, _label, _color in category_defs}

        for row in timeseries:
            dt_value = row.get("dt")
            labels.append(self._format_periodic_axis_date_label(dt_value))

            grouped_totals = {key: 0.0 for key, _label, _color in category_defs}
            grouped_has_value = {key: False for key, _label, _color in category_defs}

            for utility_key, meta in metadata.items():
                category = str(meta.get("category") or "").strip().lower()
                if category not in grouped_totals:
                    continue

                raw_value = row.get(utility_key)
                if raw_value is None:
                    continue

                grouped_totals[category] += float(raw_value or 0.0)
                grouped_has_value[category] = True

            for key, _label, _color in category_defs:
                if grouped_has_value[key]:
                    series_values[key].append(round(grouped_totals[key], 4))
                else:
                    series_values[key].append(None)

        return {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "line"},
            },
            "legend": {
                "top": 6,
                "left": 8,
                "itemWidth": 12,
                "itemHeight": 8,
            },
            "grid": {
                "left": 32,
                "right": 10,
                "top": 36,
                "bottom": 46,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": labels,
                "axisLabel": {
                    "color": "#64748b",
                    "interval": 0,
                    "rotate": 28,
                    "fontSize": 9,
                    "margin": 12,
                },
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                "axisTick": {"alignWithLabel": True},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {
                    "color": "#64748b",
                    "margin": 14,
                },
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "series": [
                {
                    "name": label,
                    "type": "line",
                    "smooth": False,
                    "symbol": "circle",
                    "symbolSize": 7,
                    "showSymbol": True,
                    "lineStyle": {"width": 2.5, "color": color},
                    "itemStyle": {"color": color},
                    "areaStyle": {"color": self._hex_to_rgba(color, 0.10)},
                    "label": {
                        "show": True,
                        "position": "top",
                        "fontSize": 8,
                        "color": color,
                        "backgroundColor": "rgba(255,255,255,0.92)",
                        "padding": [2, 4],
                        "borderRadius": 4,
                    },
                    "data": [
                        {
                            "value": value,
                            "label": {
                                "formatter": self._fmt_chart_compact(value),
                            },
                        }
                        if value is not None else None
                        for value in series_values[key]
                    ],
                }
                for key, label, color in category_defs
            ],
        }

    def _build_v3_utility_mix_option(
        self,
        items: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a current-period utility mix doughnut chart."""
        category_defs = [
            ("water", "Water", "#2563eb"),
            ("compressed_air", "Air", "#16a34a"),
            ("chilled_water", "CHW", "#0ea5b7"),
            ("steam", "Steam", "#7c3aed"),
        ]
        grouped_totals = {key: 0.0 for key, _label, _color in category_defs}

        for item in items:
            key = str(item.get("key") or "").strip().lower()
            current_value = float(item.get("current") or 0.0)
            if "air" in key:
                grouped_totals["compressed_air"] += current_value
            elif "chilled" in key:
                grouped_totals["chilled_water"] += current_value
            elif "steam" in key:
                grouped_totals["steam"] += current_value
            else:
                grouped_totals["water"] += current_value

        pie_data = [
            {
                "name": label,
                "value": round(grouped_totals[key], 4),
                "itemStyle": {"color": color},
            }
            for key, label, color in category_defs
            if grouped_totals[key] > 0
        ]

        total_value = sum(item.get("value", 0.0) for item in pie_data)

        return {
            "tooltip": {
                "trigger": "item",
            },
            "legend": {
                "bottom": 0,
                "left": "center",
                "itemWidth": 11,
                "itemHeight": 8,
                "textStyle": {
                    "fontSize": 9,
                    "color": "#475569",
                },
            },
            "title": [
                {
                    "text": self._fmt_chart_compact(total_value),
                    "left": "center",
                    "top": "40%",
                    "textStyle": {
                        "fontSize": 18,
                        "fontWeight": 800,
                        "color": "#0f172a",
                    },
                },
                {
                    "text": "Total",
                    "left": "center",
                    "top": "55%",
                    "textStyle": {
                        "fontSize": 9,
                        "fontWeight": 700,
                        "color": "#64748b",
                    },
                },
            ],
            "series": [
                {
                    "type": "pie",
                    "radius": ["48%", "70%"],
                    "center": ["50%", "42%"],
                    "avoidLabelOverlap": True,
                    "label": {
                        "show": True,
                        "formatter": "{b}\\n{d}%",
                        "fontSize": 8,
                        "color": "#334155",
                    },
                    "labelLine": {
                        "length": 8,
                        "length2": 8,
                    },
                    "data": pie_data,
                }
            ],
        }

    def _build_v3_utility_deviation_option(
        self,
        items: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a horizontal deviation chart for utility delta vs yesterday."""
        deviation_items: list[dict[str, Any]] = []

        for item in items:
            previous_value = float(item.get("previous") or 0.0)
            current_value = float(item.get("current") or 0.0)

            if previous_value == 0.0:
                deviation_pct = 0.0 if current_value == 0.0 else 100.0
            else:
                deviation_pct = ((current_value - previous_value) / previous_value) * 100.0

            deviation_items.append({
                "display_name": item.get("display_name") or "-",
                "value": round(deviation_pct, 2),
            })

        deviation_items.sort(key=lambda item: item["value"], reverse=True)

        labels = [
            self._build_v3_utility_chart_label(
                self._build_v3_utility_short_label(item["display_name"])
            )
            for item in deviation_items
        ]
        values = [item["value"] for item in deviation_items]
        colors = [
            "#e33434" if value > 0 else "#18a05e" if value < 0 else "#94a3b8"
            for value in values
        ]

        min_value = min(values, default=0.0)
        max_value = max(values, default=0.0)
        axis_min = min(-10.0, float(min_value))
        axis_max = max(10.0, float(max_value))

        return {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"},
            },
            "grid": {
                "left": 118,
                "right": 24,
                "top": 18,
                "bottom": 28,
            },
            "xAxis": {
                "type": "value",
                "min": round(axis_min - 1.0, 2),
                "max": round(axis_max + 1.0, 2),
                "axisLabel": {
                    "color": "#64748b",
                    "formatter": "{value}%",
                },
                "splitLine": {
                    "lineStyle": {"color": "#e2e8f0"},
                },
            },
            "yAxis": {
                "type": "category",
                "data": labels,
                "axisTick": {"show": False},
                "axisLine": {"show": False},
                "axisLabel": {
                    "color": "#475569",
                    "fontSize": 10,
                    "lineHeight": 11,
                    "fontWeight": 600,
                },
            },
            "series": [
                {
                    "type": "bar",
                    "barWidth": 12,
                    "data": [
                        {
                            "value": value,
                            "itemStyle": {
                                "color": colors[index],
                                "borderRadius": [0, 4, 4, 0] if value >= 0 else [4, 0, 0, 4],
                            },
                            "label": {
                                "show": True,
                                "position": "right" if value >= 0 else "left",
                                "color": "#334155",
                                "fontWeight": 700,
                                "formatter": f"{value:+.2f}%",
                            },
                        }
                        for index, value in enumerate(values)
                    ],
                }
            ],
        }

    def _build_v3_utility_overview_cards(
        self,
        utility_object: Optional[Dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build grouped dashboard cards for water, air, chilled water, and steam."""
        if not utility_object:
            return []

        metadata = utility_object.get("current", {}).get("metadata", {}) or {}
        comparison = utility_object.get("comparison", {}) or {}

        card_map = {
            "water": {
                "title": "WATER (TOTAL)",
                "icon_key": "water",
                "accent_color": "#2563eb",
                "accent_tint": "rgba(37, 99, 235, 0.08)",
                "value_color": "#2563eb",
            },
            "compressed_air": {
                "title": "AIR (TOTAL)",
                "icon_key": "air",
                "accent_color": "#16a34a",
                "accent_tint": "rgba(22, 163, 74, 0.08)",
                "value_color": "#16a34a",
            },
            "chilled_water": {
                "title": "CHILLED WATER",
                "icon_key": "chilled-water",
                "accent_color": "#0ea5b7",
                "accent_tint": "rgba(14, 165, 183, 0.10)",
                "value_color": "#0f766e",
            },
            "steam": {
                "title": "STEAM (TOTAL)",
                "icon_key": "steam",
                "accent_color": "#7c3aed",
                "accent_tint": "rgba(124, 58, 237, 0.08)",
                "value_color": "#7c3aed",
            },
        }
        grouped_values = {
            key: {"current": 0.0, "previous": 0.0}
            for key in card_map.keys()
        }

        for utility_key, meta in metadata.items():
            category = str(meta.get("category") or "").strip().lower()
            if category not in grouped_values:
                continue

            comp = comparison.get(utility_key, {})
            grouped_values[category]["current"] += float(comp.get("current") or 0.0)
            grouped_values[category]["previous"] += float(comp.get("previous") or 0.0)

        cards: list[dict[str, Any]] = []
        for category_key in ["water", "compressed_air", "chilled_water", "steam"]:
            config = card_map[category_key]
            current_value = round(grouped_values[category_key]["current"], 2)
            previous_value = round(grouped_values[category_key]["previous"], 2)
            delta_value = round(current_value - previous_value, 2)

            if previous_value == 0.0:
                delta_pct = 0.0 if current_value == 0.0 else 100.0
            else:
                delta_pct = round(((current_value - previous_value) / previous_value) * 100.0, 2)

            if abs(delta_pct) < 0.01:
                status_label = "STABLE"
                badge_class = "kpi-badge-stable"
                delta_class = "trend-neutral"
            elif delta_pct > 0:
                status_label = "WATCH"
                badge_class = "kpi-badge-watch"
                delta_class = "trend-down"
            else:
                status_label = "GOOD"
                badge_class = "kpi-badge-good"
                delta_class = "trend-up"

            cards.append({
                "key": category_key,
                "title": config["title"],
                "icon_key": config["icon_key"],
                "accent_color": config["accent_color"],
                "accent_tint": config["accent_tint"],
                "value_color": config["value_color"],
                "status_label": status_label,
                "badge_class": badge_class,
                "today_display": self._fmt(current_value),
                "yesterday_display": self._fmt(previous_value),
                "delta_display": self._fmt(delta_value),
                "delta_pct_display": self._fmt_pct(delta_pct / 100.0),
                "delta_class": delta_class,
            })

        return cards

    def _build_v3_utility_energy_context(
        self,
        *,
        utility_object: Optional[Dict[str, Any]],
        energy_object: Optional[Dict[str, Any]],
        period: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build utility energy cards and detail rows from meter mappings."""
        default_context = {
            "enabled": False,
            "title": "UTILITY ENERGY (CONVERTED TO kWh)",
            "unit_badge": "kWh",
            "summary_note": "",
            "overview_cards": [],
            "detail_rows": [],
            "charts": {},
        }

        if not utility_object or not energy_object:
            return default_context

        metadata = utility_object.get("current", {}).get("metadata", {}) or {}
        comparison = utility_object.get("comparison", {}) or {}

        current_lookup = self._build_utility_energy_meter_lookup(
            energy_object.get("current", {}) or {}
        )
        previous_lookup = self._build_utility_energy_meter_lookup(
            energy_object.get("previous", {}) or {}
        )

        detail_rows: list[dict[str, Any]] = []
        category_totals = {
            "compressed_air": {"current": 0.0, "previous": 0.0},
            "chilled_water": {"current": 0.0, "previous": 0.0},
            "steam": {"current": 0.0, "previous": 0.0},
        }
        any_energy_mapping = False

        for utility_key, meta in metadata.items():
            comp = comparison.get(utility_key, {}) or {}
            category = str(meta.get("category") or "").strip().lower()
            energy_area = str(meta.get("energy_area") or "").strip().lower()
            energy_meters = [
                str(item).strip()
                for item in (meta.get("energy_meters") or [])
                if str(item).strip()
            ]

            current_energy = self._resolve_utility_energy_total(
                lookup=current_lookup,
                energy_area=energy_area,
                energy_meters=energy_meters,
            )
            previous_energy = self._resolve_utility_energy_total(
                lookup=previous_lookup,
                energy_area=energy_area,
                energy_meters=energy_meters,
            )
            energy_delta = round(current_energy - previous_energy, 2)
            energy_delta_ratio = self._safe_pct_delta(
                current_value=current_energy,
                previous_value=previous_energy,
            )
            value_delta_ratio = self._safe_pct_delta(
                current_value=float(comp.get("current") or 0.0),
                previous_value=float(comp.get("previous") or 0.0),
            )

            if energy_meters:
                any_energy_mapping = True

            if category in category_totals:
                category_totals[category]["current"] += current_energy
                category_totals[category]["previous"] += previous_energy

            detail_rows.append({
                "key": utility_key,
                "display_name": meta.get("display_name") or utility_key,
                "group_label": self._format_utility_group_label(category),
                "current_display": self._fmt(comp.get("current")),
                "previous_display": self._fmt(comp.get("previous")),
                "delta_display": self._fmt(comp.get("delta")),
                "delta_pct_display": self._fmt_pct(value_delta_ratio),
                "delta_pct_class": self._consumption_trend_class(value_delta_ratio),
                "energy_current_display": self._fmt(current_energy),
                "energy_previous_display": self._fmt(previous_energy),
                "energy_delta_display": self._fmt(energy_delta),
                "energy_delta_pct_display": self._fmt_pct(energy_delta_ratio),
                "energy_delta_pct_class": self._consumption_trend_class(energy_delta_ratio),
            })

        if not any_energy_mapping:
            return default_context

        overview_cards = self._build_v3_utility_energy_overview_cards(category_totals)
        energy_charts = self._build_v3_utility_energy_charts(
            utility_object=utility_object,
            energy_object=energy_object,
            category_totals=category_totals,
            period=period,
        )

        return {
            "enabled": True,
            "title": "UTILITY ENERGY (CONVERTED TO kWh)",
            "unit_badge": "kWh",
            "summary_note": "Total = Air + Chilled Water + Boiler",
            "overview_cards": overview_cards,
            "detail_rows": detail_rows,
            "charts": energy_charts,
        }

    def _build_utility_energy_meter_lookup(
        self,
        energy_period_object: Dict[str, Any],
    ) -> Dict[str, Dict[Any, float]]:
        """Aggregate energy totals by meter for one report period."""
        by_meter: dict[str, float] = {}
        by_area_meter: dict[tuple[str, str], float] = {}
        by_meter_date: dict[tuple[str, Any], float] = {}
        by_area_meter_date: dict[tuple[str, str, Any], float] = {}
        dates_seen: set[Any] = set()

        for area_table in energy_period_object.get("daily_tables", []) or []:
            area_key = str(area_table.get("area_key") or "").strip().lower()

            for row in area_table.get("rows", []) or []:
                dt_value = row.get("date")
                if dt_value is not None:
                    dates_seen.add(dt_value)
                for cell in row.get("cells", []) or []:
                    meter_name = str(cell.get("key") or "").strip()
                    meter_role = str(cell.get("meter_role") or "").strip().lower()
                    raw_value = cell.get("raw_value")

                    if not meter_name or meter_role == "unknown":
                        continue
                    if not isinstance(raw_value, (int, float)):
                        continue

                    value = float(raw_value)
                    by_meter[meter_name] = by_meter.get(meter_name, 0.0) + value
                    by_area_meter[(area_key, meter_name)] = (
                        by_area_meter.get((area_key, meter_name), 0.0) + value
                    )
                    if dt_value is not None:
                        by_meter_date[(meter_name, dt_value)] = (
                            by_meter_date.get((meter_name, dt_value), 0.0) + value
                        )
                        by_area_meter_date[(area_key, meter_name, dt_value)] = (
                            by_area_meter_date.get((area_key, meter_name, dt_value), 0.0) + value
                        )

        return {
            "by_meter": by_meter,
            "by_area_meter": by_area_meter,
            "by_meter_date": by_meter_date,
            "by_area_meter_date": by_area_meter_date,
            "dates": sorted(dates_seen),
        }

    def _resolve_utility_energy_total(
        self,
        *,
        lookup: Dict[str, Dict[Any, float]],
        energy_area: str,
        energy_meters: list[str],
    ) -> float:
        """Resolve one utility energy total using meter mapping."""
        if not energy_meters:
            return 0.0

        by_meter = lookup.get("by_meter", {}) or {}
        by_area_meter = lookup.get("by_area_meter", {}) or {}

        total = 0.0
        for meter_name in energy_meters:
            if energy_area and (energy_area, meter_name) in by_area_meter:
                total += float(by_area_meter.get((energy_area, meter_name), 0.0) or 0.0)
            else:
                total += float(by_meter.get(meter_name, 0.0) or 0.0)

        return round(total, 2)

    def _build_v3_utility_energy_overview_cards(
        self,
        category_totals: Dict[str, Dict[str, float]],
    ) -> list[dict[str, Any]]:
        """Build dashboard cards for total, air, chilled-water, and boiler energy."""
        total_current = sum(item.get("current", 0.0) or 0.0 for item in category_totals.values())
        total_previous = sum(item.get("previous", 0.0) or 0.0 for item in category_totals.values())

        card_map = [
            {
                "key": "total",
                "title": "TOTAL UTILITY ENERGY",
                "icon_key": "energy",
                "accent_color": "#2563eb",
                "accent_tint": "rgba(37, 99, 235, 0.08)",
                "value_color": "#2563eb",
                "current": total_current,
                "previous": total_previous,
            },
            {
                "key": "compressed_air",
                "title": "AIR ENERGY",
                "icon_key": "air",
                "accent_color": "#16a34a",
                "accent_tint": "rgba(22, 163, 74, 0.08)",
                "value_color": "#16a34a",
                "current": category_totals.get("compressed_air", {}).get("current", 0.0) or 0.0,
                "previous": category_totals.get("compressed_air", {}).get("previous", 0.0) or 0.0,
            },
            {
                "key": "chilled_water",
                "title": "CHILLED WATER ENERGY",
                "icon_key": "chilled-water",
                "accent_color": "#0ea5b7",
                "accent_tint": "rgba(14, 165, 183, 0.08)",
                "value_color": "#0f766e",
                "current": category_totals.get("chilled_water", {}).get("current", 0.0) or 0.0,
                "previous": category_totals.get("chilled_water", {}).get("previous", 0.0) or 0.0,
            },
            {
                "key": "steam",
                "title": "BOILER ENERGY",
                "icon_key": "steam",
                "accent_color": "#7c3aed",
                "accent_tint": "rgba(124, 58, 237, 0.08)",
                "value_color": "#7c3aed",
                "current": category_totals.get("steam", {}).get("current", 0.0) or 0.0,
                "previous": category_totals.get("steam", {}).get("previous", 0.0) or 0.0,
            },
        ]

        cards: list[dict[str, Any]] = []
        for card in card_map:
            current_value = round(float(card.get("current") or 0.0), 2)
            previous_value = round(float(card.get("previous") or 0.0), 2)
            delta_value = round(current_value - previous_value, 2)
            delta_ratio = self._safe_pct_delta(
                current_value=current_value,
                previous_value=previous_value,
            )
            status = self._build_dashboard_status(delta_ratio)

            cards.append({
                "key": card["key"],
                "title": card["title"],
                "icon_key": card["icon_key"],
                "accent_color": card["accent_color"],
                "accent_tint": card["accent_tint"],
                "value_color": card["value_color"],
                "status_label": status["label"],
                "badge_class": status["badge_class"],
                "today_display": self._fmt(current_value),
                "yesterday_display": self._fmt(previous_value),
                "delta_display": self._fmt(delta_value),
                "delta_pct_display": self._fmt_pct(delta_ratio),
                "delta_class": status["delta_class"],
            })

        return cards

    def _build_v3_utility_energy_charts(
        self,
        *,
        utility_object: Optional[Dict[str, Any]],
        energy_object: Optional[Dict[str, Any]],
        category_totals: Dict[str, Dict[str, float]],
        period: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build periodic utility-energy charts shown below the overview cards."""
        period_type = str((period or {}).get("type") or "").strip().lower()
        if period_type == "daily" or not utility_object or not energy_object:
            return {}

        energy_current = energy_object.get("current", {}) or {}
        metadata = utility_object.get("current", {}).get("metadata", {}) or {}
        lookup = self._build_utility_energy_meter_lookup(energy_current)
        dates = lookup.get("dates", []) or []
        if not metadata or not dates:
            return {}

        category_defs = [
            ("compressed_air", "Air Energy", "#16a34a"),
            ("chilled_water", "Chilled Water Energy", "#0ea5b7"),
            ("steam", "Boiler Energy", "#7c3aed"),
        ]
        category_series: dict[str, list[float]] = {key: [] for key, _label, _color in category_defs}
        labels = [self._format_periodic_axis_date_label(value) for value in dates]

        for dt_value in dates:
            category_day_totals = {key: 0.0 for key, _label, _color in category_defs}
            for meta in metadata.values():
                category = str(meta.get("category") or "").strip().lower()
                energy_area = str(meta.get("energy_area") or "").strip().lower()
                energy_meters = [
                    str(item).strip()
                    for item in (meta.get("energy_meters") or [])
                    if str(item).strip()
                ]
                if category not in category_day_totals or not energy_meters:
                    continue
                category_day_totals[category] += self._resolve_utility_energy_total_for_date(
                    lookup=lookup,
                    energy_area=energy_area,
                    energy_meters=energy_meters,
                    dt_value=dt_value,
                )

            for key, _label, _color in category_defs:
                category_series[key].append(round(category_day_totals[key], 4))

        total_series = [
            round(
                category_series["compressed_air"][idx]
                + category_series["chilled_water"][idx]
                + category_series["steam"][idx],
                4,
            )
            for idx in range(len(labels))
        ]

        period_badge = self._resolve_utility_energy_period_badge(period_type)
        distribution_items = []
        total_current = 0.0
        for key, label, color in category_defs:
            value = round(float(category_totals.get(key, {}).get("current", 0.0) or 0.0), 2)
            if value <= 0:
                continue
            total_current += value
            distribution_items.append({
                "name": label,
                "value": value,
                "itemStyle": {"color": color},
                "percent_display": "0.0%",
                "value_display": self._fmt(value),
            })

        total_current = round(total_current, 2)
        for item in distribution_items:
            pct_value = (float(item.get("value") or 0.0) / total_current * 100.0) if total_current > 0 else 0.0
            item["percent_display"] = f"{pct_value:.1f}%"

        return {
            "trend": {
                "title": "Utility Energy trend",
                "subtitle": "Current period daily total by energy group",
                "option": self._build_v3_utility_energy_trend_option(
                    labels=labels,
                    air_values=category_series["compressed_air"],
                    chilled_values=category_series["chilled_water"],
                    steam_values=category_series["steam"],
                    total_values=total_series,
                ),
            },
            "distribution": {
                "title": "Utility Distribution",
                "subtitle": f"Current period share ({period_badge.lower()})",
                "period_badge": period_badge,
                "total_display": self._fmt(total_current),
                "total_unit": "kWh",
                "legend_items": distribution_items,
                "option": self._build_v3_utility_energy_distribution_option(
                    items=distribution_items,
                    total_value=total_current,
                    period_badge=period_badge,
                ),
            },
        }

    def _resolve_utility_energy_total_for_date(
        self,
        *,
        lookup: Dict[str, Dict[Any, float]],
        energy_area: str,
        energy_meters: list[str],
        dt_value: Any,
    ) -> float:
        """Resolve one utility energy total for a specific day."""
        if not energy_meters:
            return 0.0

        by_meter_date = lookup.get("by_meter_date", {}) or {}
        by_area_meter_date = lookup.get("by_area_meter_date", {}) or {}
        total = 0.0

        for meter_name in energy_meters:
            if energy_area and (energy_area, meter_name, dt_value) in by_area_meter_date:
                total += float(by_area_meter_date.get((energy_area, meter_name, dt_value), 0.0) or 0.0)
            else:
                total += float(by_meter_date.get((meter_name, dt_value), 0.0) or 0.0)

        return round(total, 2)

    def _resolve_utility_energy_period_badge(self, period_type: str) -> str:
        """Return a short current-period badge label for utility-energy widgets."""
        mapping = {
            "weekly": "This week",
            "monthly": "This month",
            "daily": "Today",
        }
        return mapping.get(period_type, "Current period")

    def _build_v3_utility_energy_trend_option(
        self,
        *,
        labels: list[str],
        air_values: list[float],
        chilled_values: list[float],
        steam_values: list[float],
        total_values: list[float],
    ) -> Dict[str, Any]:
        """Build periodic utility-energy trend line chart."""
        series_defs = [
            ("Air Energy", "#16a34a", air_values),
            ("Chilled Water Energy", "#0ea5b7", chilled_values),
            ("Boiler Energy", "#7c3aed", steam_values),
            ("Total Utility Energy", "#2563eb", total_values),
        ]

        return {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "line"},
            },
            "legend": {
                "top": 6,
                "left": 8,
                "itemWidth": 12,
                "itemHeight": 8,
                "textStyle": {"fontSize": 10},
            },
            "grid": {
                "left": 32,
                "right": 12,
                "top": 40,
                "bottom": 46,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": labels,
                "axisLabel": {
                    "color": "#64748b",
                    "interval": 0,
                    "rotate": 28,
                    "fontSize": 9,
                    "margin": 12,
                },
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                "axisTick": {"alignWithLabel": True},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": "#64748b"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "series": [
                {
                    "name": name,
                    "type": "line",
                    "smooth": False,
                    "symbol": "circle",
                    "symbolSize": 7,
                    "showSymbol": True,
                    "lineStyle": {"width": 2.5, "color": color},
                    "itemStyle": {"color": color},
                    "areaStyle": {"color": self._hex_to_rgba(color, 0.10)},
                    "label": {
                        "show": True,
                        "position": "top",
                        "fontSize": 8,
                        "color": color,
                        "backgroundColor": "rgba(255,255,255,0.92)",
                        "padding": [2, 4],
                        "borderRadius": 4,
                    },
                    "data": [
                        {
                            "value": value,
                            "label": {"formatter": self._fmt_chart_compact(value)},
                        }
                        if value is not None else None
                        for value in values
                    ],
                }
                for name, color, values in series_defs
            ],
        }

    def _build_v3_utility_energy_distribution_option(
        self,
        *,
        items: list[dict[str, Any]],
        total_value: float,
        period_badge: str,
    ) -> Dict[str, Any]:
        """Build periodic utility-energy distribution doughnut option."""
        return {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} kWh ({d}%)"},
            "series": [
                {
                    "type": "pie",
                    "radius": ["52%", "76%"],
                    "center": ["37%", "56%"],
                    "startAngle": 90,
                    "avoidLabelOverlap": True,
                    "minShowLabelAngle": 2,
                    "itemStyle": {
                        "borderColor": "#ffffff",
                        "borderWidth": 3,
                        "borderRadius": 8,
                    },
                    "label": {
                        "show": True,
                        "position": "inside",
                        "formatter": "{d}%",
                        "color": "#ffffff",
                        "fontWeight": 700,
                        "fontSize": 10,
                    },
                    "labelLine": {"show": False},
                    "data": items,
                }
            ],
            "graphic": [
                {
                    "type": "group",
                    "left": "37%",
                    "top": "53%",
                    "silent": True,
                    "children": [
                        {
                            "type": "text",
                            "x": 0,
                            "y": -8,
                            "style": {
                                "text": self._fmt_chart_total(total_value),
                                "textAlign": "center",
                                "fill": "#0f172a",
                                "fontSize": 17,
                                "fontWeight": 800,
                            },
                        },
                        {
                            "type": "text",
                            "x": 0,
                            "y": 14,
                            "style": {
                                "text": "kWh",
                                "textAlign": "center",
                                "fill": "#334155",
                                "fontSize": 10,
                                "fontWeight": 700,
                            },
                        },
                        {
                            "type": "text",
                            "x": 0,
                            "y": 34,
                            "style": {
                                "text": period_badge,
                                "textAlign": "center",
                                "fill": "#64748b",
                                "fontSize": 9,
                                "fontWeight": 600,
                            },
                        },
                    ],
                }
            ],
        }

    def _build_dashboard_status(
        self,
        delta_ratio: Optional[float],
    ) -> Dict[str, str]:
        """Return dashboard badge and trend classes from delta ratio."""
        if delta_ratio is None or abs(delta_ratio) < 0.0001:
            return {
                "label": "STABLE",
                "badge_class": "kpi-badge-stable",
                "delta_class": "trend-neutral",
            }
        if delta_ratio > 0:
            return {
                "label": "WATCH",
                "badge_class": "kpi-badge-watch",
                "delta_class": "trend-down",
            }
        return {
            "label": "GOOD",
            "badge_class": "kpi-badge-good",
            "delta_class": "trend-up",
        }

    def _safe_pct_delta(
        self,
        *,
        current_value: float,
        previous_value: float,
    ) -> Optional[float]:
        """Return ratio delta for current vs previous."""
        if previous_value == 0.0:
            return 0.0 if current_value == 0.0 else 1.0
        return round((current_value - previous_value) / previous_value, 4)

    def _format_utility_group_label(self, category: str) -> str:
        """Map utility category keys to short group labels."""
        mapping = {
            "water": "Water",
            "chilled_water": "Chilled Water",
            "compressed_air": "Air",
            "steam": "Steam",
        }
        return mapping.get(category, category.replace("_", " ").title())

    def _resolve_utility_unit_badge(
        self,
        utility_object: Optional[Dict[str, Any]],
    ) -> str:
        """Resolve one shared unit badge for the utility section."""
        if not utility_object:
            return "m³"

        metadata = utility_object.get("current", {}).get("metadata", {}) or {}
        units = sorted({
            str(meta.get("unit") or "").strip()
            for meta in metadata.values()
            if meta.get("unit")
        })
        return units[0] if len(units) == 1 else "Mixed units"

    def _build_v3_utility_date_comparison(
        self,
        period: Optional[Dict[str, Any]],
    ) -> Dict[str, str]:
        """Build utility header date comparison labels."""
        period = period or {}
        return {
            "current_label": "Today",
            "previous_label": "Yesterday",
            "current_display": self._format_date_short_label(period.get("end_date")),
            "previous_display": self._format_date_short_label(period.get("previous_end_date")),
        }

    def _build_v3_sensor_trend_clusters(
        self,
        sensor_monitoring: Dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build rendered intraday trend clusters for daily utility UI."""
        trend_mode = str(sensor_monitoring.get("trend_mode") or "").strip().lower()
        trend_clusters = sensor_monitoring.get("trend_clusters") or []

        if trend_mode != "intraday" or not trend_clusters:
            return []

        rendered_clusters: list[dict[str, Any]] = []
        for cluster in trend_clusters:
            rendered_charts = self._build_v3_sensor_trend_cluster_charts(cluster)
            if not rendered_charts:
                continue

            rendered_clusters.append({
                "enabled": True,
                "cluster_key": cluster.get("cluster_key") or "",
                "cluster_label": cluster.get("cluster_label") or "",
                "accent_color": cluster.get("accent_color") or "#2563eb",
                "accent_tint": cluster.get("accent_tint") or "rgba(37, 99, 235, 0.08)",
                "sensor_count": int(cluster.get("sensor_count") or 0),
                "active_sensor_count": int(cluster.get("active_sensor_count") or 0),
                "alert_count": int(cluster.get("alert_count") or 0),
                "chart_count": len(rendered_charts),
                "charts": rendered_charts,
            })

        return rendered_clusters

    def _build_v3_sensor_trend_cluster_charts(
        self,
        cluster: Dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build display charts for one sensor cluster."""
        raw_charts = cluster.get("charts") or []
        chart_lookup = {
            str(chart.get("measurement_type") or "").strip().lower(): chart
            for chart in raw_charts
        }

        rendered_charts: list[dict[str, Any]] = []
        cluster_label = cluster.get("cluster_label") or "Sensor cluster"
        cluster_key = str(cluster.get("cluster_key") or "").strip().lower()
        full_width_flow_pressure = cluster_key in {"ico_chiller", "diode_chiller"}

        temperature_chart = chart_lookup.get("temperature")
        if temperature_chart and (temperature_chart.get("series") or []):
            rendered_charts.append({
                "chart_id": f"utility-sensor-trend-{cluster.get('cluster_key')}-temperature",
                "chart_key": f"{cluster.get('cluster_key')}_temperature",
                "title": "Temperature trend",
                "subtitle": f"{cluster_label} · {temperature_chart.get('unit') or '-'}",
                "option": self._build_v3_sensor_intraday_option(
                    temperature_chart,
                    y_axes=[
                        {
                            "name": temperature_chart.get("unit") or "",
                            "series_keys": [
                                str(series.get("sensor_key") or "")
                                for series in (temperature_chart.get("series") or [])
                            ],
                        }
                    ],
                ),
            })

        flow_chart = chart_lookup.get("flow")
        pressure_chart = chart_lookup.get("pressure")
        if flow_chart or pressure_chart:
            combo_series = []
            if flow_chart:
                combo_series.extend(flow_chart.get("series") or [])
            if pressure_chart:
                combo_series.extend(pressure_chart.get("series") or [])

            combo_chart = {
                "chart_key": f"{cluster.get('cluster_key')}_flow_pressure",
                "title": "Flow and pressure trend",
                "series": combo_series,
            }
            y_axes = []
            if flow_chart and (flow_chart.get("series") or []):
                y_axes.append({
                    "name": flow_chart.get("unit") or "",
                    "series_keys": [
                        str(series.get("sensor_key") or "")
                        for series in (flow_chart.get("series") or [])
                    ],
                })
            if pressure_chart and (pressure_chart.get("series") or []):
                y_axes.append({
                    "name": pressure_chart.get("unit") or "",
                    "series_keys": [
                        str(series.get("sensor_key") or "")
                        for series in (pressure_chart.get("series") or [])
                    ],
                })

            if flow_chart and pressure_chart:
                combo_title = "Flow and pressure trend"
                combo_subtitle = f"{cluster_label} · dual-axis view"
            elif flow_chart:
                combo_title = "Flow trend"
                combo_subtitle = f"{cluster_label} · {flow_chart.get('unit') or '-'}"
            else:
                combo_title = "Pressure trend"
                combo_subtitle = f"{cluster_label} · {pressure_chart.get('unit') or '-'}"

            combo_rendered_chart = {
                "chart_id": f"utility-sensor-trend-{cluster.get('cluster_key')}-flow-pressure",
                "chart_key": f"{cluster.get('cluster_key')}_flow_pressure",
                "title": combo_title,
                "subtitle": combo_subtitle,
                "is_full_width": full_width_flow_pressure,
                "option": self._build_v3_sensor_intraday_option(combo_chart, y_axes=y_axes),
            }
        else:
            combo_rendered_chart = None

        capacity_chart = chart_lookup.get("capacity")
        if capacity_chart and (capacity_chart.get("series") or []):
            capacity_rendered_chart = {
                "chart_id": f"utility-sensor-trend-{cluster.get('cluster_key')}-capacity",
                "chart_key": f"{cluster.get('cluster_key')}_capacity",
                "title": "Capacity trend",
                "subtitle": f"{cluster_label} · {capacity_chart.get('unit') or '-'}",
                "option": self._build_v3_sensor_intraday_option(
                    capacity_chart,
                    y_axes=[
                        {
                            "name": capacity_chart.get("unit") or "",
                            "series_keys": [
                                str(series.get("sensor_key") or "")
                                for series in (capacity_chart.get("series") or [])
                            ],
                        }
                    ],
                ),
            }
        else:
            capacity_rendered_chart = None

        if full_width_flow_pressure and capacity_rendered_chart is not None:
            rendered_charts.append(capacity_rendered_chart)
            if combo_rendered_chart is not None:
                rendered_charts.append(combo_rendered_chart)
        else:
            if combo_rendered_chart is not None:
                rendered_charts.append(combo_rendered_chart)
            if capacity_rendered_chart is not None:
                rendered_charts.append(capacity_rendered_chart)

        return rendered_charts

    def _build_v3_sensor_intraday_option(
        self,
        chart: Dict[str, Any],
        *,
        y_axes: list[dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """Build one intraday sensor line chart from raw timestamp points."""
        series_items = chart.get("series") or []
        all_timestamps: list[str] = []

        for series in series_items:
            for point in series.get("points") or []:
                ts_value = str(point.get("ts") or "").strip()
                if ts_value and ts_value not in all_timestamps:
                    all_timestamps.append(ts_value)

        if not all_timestamps:
            all_timestamps = ["-"]

        formatted_labels = [self._build_v3_intraday_axis_label(ts_value) for ts_value in all_timestamps]

        axis_list = y_axes or [{
            "name": chart.get("unit") or "",
            "series_keys": [
                str(series.get("sensor_key") or "")
                for series in series_items
            ],
        }]
        series_axis_map: dict[str, int] = {}
        for axis_index, axis in enumerate(axis_list):
            for sensor_key in axis.get("series_keys") or []:
                series_axis_map[str(sensor_key)] = axis_index

        option_series: list[dict[str, Any]] = []
        for series in series_items:
            point_lookup = {
                str(point.get("ts") or ""): point
                for point in series.get("points") or []
            }
            sensor_key = str(series.get("sensor_key") or "")
            series_color = series.get("color") or "#2563eb"
            series_data = [
                (
                    round(float(point_lookup[ts_value]["value"]), 4)
                    if ts_value in point_lookup and isinstance(point_lookup[ts_value].get("value"), (int, float))
                    else None
                )
                for ts_value in all_timestamps
            ]
            numeric_points = [
                (point_index, float(point_value))
                for point_index, point_value in enumerate(series_data)
                if isinstance(point_value, (int, float))
            ]
            mark_points: list[dict[str, Any]] = []

            if numeric_points:
                min_index, min_value = min(numeric_points, key=lambda item: item[1])
                max_index, max_value = max(numeric_points, key=lambda item: item[1])

                if min_index == max_index and abs(min_value - max_value) < 1e-9:
                    mark_points.append({
                        "name": "Min/Max",
                        "coord": [formatted_labels[min_index], round(min_value, 4)],
                        "value": round(min_value, 4),
                        "itemStyle": {"color": series_color},
                        "label": {
                            "show": True,
                            "position": "top",
                            "distance": 8,
                            "formatter": f"Min/Max {self._fmt_chart_callout(min_value)}",
                            "color": series_color,
                            "fontSize": 9,
                            "fontWeight": 700,
                            "backgroundColor": "rgba(255,255,255,0.92)",
                            "padding": [2, 5],
                            "borderRadius": 4,
                        },
                    })
                else:
                    for marker_name, marker_index, marker_value in [
                        ("Min", min_index, min_value),
                        ("Max", max_index, max_value),
                    ]:
                        mark_points.append({
                            "name": marker_name,
                            "coord": [formatted_labels[marker_index], round(marker_value, 4)],
                            "value": round(marker_value, 4),
                            "itemStyle": {"color": series_color},
                            "label": {
                                "show": True,
                                "position": "top",
                                "distance": 8,
                                "formatter": f"{marker_name} {self._fmt_chart_callout(marker_value)}",
                                "color": series_color,
                                "fontSize": 9,
                                "fontWeight": 700,
                                "backgroundColor": "rgba(255,255,255,0.92)",
                                "padding": [2, 5],
                                "borderRadius": 4,
                            },
                        })

            option_series.append({
                "name": series.get("label") or series.get("sensor_key") or "-",
                "type": "line",
                "smooth": False,
                "showSymbol": False,
                "symbol": "circle",
                "symbolSize": 5,
                "lineStyle": {
                    "width": 2.2,
                    "color": series_color,
                },
                "itemStyle": {
                    "color": series_color,
                },
                "areaStyle": {
                    "color": self._hex_to_rgba(series_color, 0.08),
                },
                "emphasis": {
                    "focus": "series",
                },
                "connectNulls": False,
                "yAxisIndex": int(series_axis_map.get(sensor_key, 0)),
                "data": series_data,
                "markPoint": {
                    "symbol": "circle",
                    "symbolSize": 10,
                    "data": mark_points,
                },
            })

        option_y_axes = []
        for axis_index, axis in enumerate(axis_list):
            option_y_axes.append({
                "type": "value",
                "name": axis.get("name") or "",
                "position": "left" if axis_index == 0 else "right",
                "alignTicks": True if len(axis_list) > 1 else False,
                "nameTextStyle": {
                    "color": "#64748b",
                    "fontSize": 9,
                    "padding": [20, 0, 0, 10],
                },
                "axisLabel": {"color": "#64748b", "fontSize": 9},
                "axisLine": {"show": len(axis_list) > 1, "lineStyle": {"color": "#cbd5e1"}},
                "splitLine": {"show": axis_index == 0, "lineStyle": {"color": "#e2e8f0"}},
            })

        return {
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "line"},
            },
            "legend": {
                "top": 6,
                "left": 8,
                "itemWidth": 12,
                "itemHeight": 8,
                "textStyle": {"color": "#475569", "fontSize": 10},
            },
            "grid": {
                "left": 38,
                "right": 14,
                "top": 38,
                "bottom": 28,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "data": formatted_labels,
                "boundaryGap": False,
                "axisLabel": {
                    "color": "#64748b",
                    "fontSize": 9,
                    "interval": "auto",
                },
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            },
            "yAxis": option_y_axes,
            "series": option_series,
        }

    def _build_v3_intraday_axis_label(
        self,
        timestamp_text: str,
    ) -> str:
        """Return compact chart x-axis label from backend timestamp text."""
        if not timestamp_text:
            return "-"
        if " " in timestamp_text:
            return timestamp_text.split(" ", 1)[1][:5]
        if "T" in timestamp_text:
            return timestamp_text.split("T", 1)[1][:5]
        return timestamp_text[-5:]

    def _build_v3_kpi_section(
        self,
        kpi_object: Optional[Dict[str, Any]],
        period_type: str = "",
        anchor_date: Optional[date] = None,
        previous_anchor_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Build V3 KPI section from KPI object.

        This version maps the existing KPI contract into the new V3 layout:
        - coverage
        - totals
        - comparison
        - product context
        - daily detail

        Args:
            kpi_object: Prepared KPI domain object.

        Returns:
            Dict[str, Any]: V3 KPI section.

        Example:
            section = self._build_v3_kpi_section(kpi_object)
        """
        if not kpi_object:
            return {
                "title": "ENERGY KPI",
                "subtitle": "Energy intensity and production context.",
                "coverage": {},
                "summary_matrix": {
                    "title": "Current period KPI summary",
                    "rows": [],
                },
                "charts": {
                    "daily_grouped_bar": {},
                    "daily_dashboard": {
                        "cards": [],
                        "charts": {},
                    },
                },
                "totals": {
                    "plant": {},
                    "areas": [],
                },
                "comparison": {
                    "plant": {},
                    "areas": [],
                },
                "product_context": {
                    "enabled": False,
                    "title": "Production Context",
                    "rows": [],
                },
                "daily_detail": {
                    "title": "Daily KPI Detail",
                    "rows": [],
                },
            }

        current_summary = kpi_object.get("current", {}).get("summary", {})
        previous_summary = kpi_object.get("previous", {}).get("summary", {})
        current_coverage = kpi_object.get("current", {}).get("coverage", {})
        comparison = kpi_object.get("comparison", {})

        current_plant = current_summary.get("plant", {})
        previous_plant = previous_summary.get("plant", {})
        comparison_plant = comparison.get("plant", {})

        coverage_block = {
            "coverage_display": (
                f"{current_coverage.get('coverage_days', 0)}/"
                f"{current_coverage.get('report_total_days', 0)}"
            ),
            "coverage_note": self._map_kpi_coverage_note(
                current_coverage.get("coverage_note")
            ),
            "uncovered_ranges": self._build_kpi_uncovered_ranges(
                current_coverage.get("uncovered_ranges", [])
            ),
            "is_complete": current_coverage.get("is_full_coverage", False),
        }

        totals_plant = {
            "current_display": self._fmt(current_plant.get("total_kpi")),
            "previous_display": self._fmt(previous_plant.get("total_kpi")),
            "coverage_display": (
                f"{current_coverage.get('coverage_days', 0)}/"
                f"{current_coverage.get('report_total_days', 0)}"
            ),
            "unit": "kWh/Ton",
        }

        totals_areas: list[dict[str, Any]] = []
        product_rows: list[dict[str, Any]] = []
        comparison_areas: list[dict[str, Any]] = []

        area_display_order = [
            ("ico", "ICO"),
            ("diode", "DIODE"),
            ("sakari", "SAKARI"),
        ]

        for area_key, area_name in area_display_order:
            current_area = current_summary.get("areas", {}).get(area_key, {})
            previous_area = previous_summary.get("areas", {}).get(area_key, {})
            comparison_area = comparison.get("areas", {}).get(area_key, {})

            totals_areas.append({
                "area_key": area_key,
                "area_name": area_name,
                "current_display": self._fmt(current_area.get("kpi")),
                "previous_display": self._fmt(previous_area.get("kpi")),
                "unit": "kWh/Ton",
            })

            comparison_areas.append({
                "area_key": area_key,
                "area_name": area_name,
                "current_display": self._fmt(comparison_area.get("current")),
                "previous_display": self._fmt(comparison_area.get("previous")),
                "delta_display": self._fmt(comparison_area.get("delta")),
                "delta_pct_display": self._fmt_pct(comparison_area.get("delta_pct")),
                "delta_class": self._consumption_trend_class(comparison_area.get("delta")),
                "delta_pct_class": self._consumption_trend_class(comparison_area.get("delta_pct")),
            })

            current_prod = current_area.get("prod")
            previous_prod = previous_area.get("prod")

            if current_prod is None and previous_prod is None:
                prod_delta = None
                prod_delta_pct = None
            else:
                curr_val = current_prod or 0.0
                prev_val = previous_prod or 0.0
                prod_delta = curr_val - prev_val
                prod_delta_pct = (prod_delta / prev_val) if prev_val != 0 else None

            product_rows.append({
                "level_name": area_name,
                "current_prod_display": self._fmt(current_prod),
                "previous_prod_display": self._fmt(previous_prod),
                "delta_display": self._fmt(prod_delta),
                "delta_pct_display": self._fmt_pct(prod_delta_pct),
                "delta_class": self._trend_class(prod_delta),
                "delta_pct_class": self._trend_class(prod_delta_pct),
            })

        current_plant_prod = current_plant.get("total_prod")
        previous_plant_prod = previous_plant.get("total_prod")

        if current_plant_prod is None and previous_plant_prod is None:
            plant_prod_delta = None
            plant_prod_delta_pct = None
        else:
            curr_val = current_plant_prod or 0.0
            prev_val = previous_plant_prod or 0.0
            plant_prod_delta = curr_val - prev_val
            plant_prod_delta_pct = (
                (plant_prod_delta / prev_val) if prev_val != 0 else None
            )

        product_rows.insert(0, {
            "level_name": "Plant",
            "current_prod_display": self._fmt(current_plant_prod),
            "previous_prod_display": self._fmt(previous_plant_prod),
            "delta_display": self._fmt(plant_prod_delta),
            "delta_pct_display": self._fmt_pct(plant_prod_delta_pct),
            "delta_class": self._trend_class(plant_prod_delta),
            "delta_pct_class": self._trend_class(plant_prod_delta_pct),
        })

        comparison_block = {
            "plant": {
                "current_display": self._fmt(comparison_plant.get("current")),
                "previous_display": self._fmt(comparison_plant.get("previous")),
                "delta_display": self._fmt(comparison_plant.get("delta")),
                "delta_pct_display": self._fmt_pct(comparison_plant.get("delta_pct")),
                "delta_class": self._consumption_trend_class(comparison_plant.get("delta")),
                "delta_pct_class": self._consumption_trend_class(comparison_plant.get("delta_pct")),
            },
            "areas": comparison_areas,
        }

        daily_detail = {
            "title": "Daily KPI Detail",
            "rows": self._build_kpi_daily_rows(kpi_object),
        }

        summary_matrix = self._build_v3_kpi_summary_matrix(
            kpi_object=kpi_object,
            period_type=period_type,
            anchor_date=anchor_date,
            previous_anchor_date=previous_anchor_date,
        )
        charts = self._build_v3_kpi_charts(kpi_object)

        return {
            "title": "ENERGY KPI",
            "subtitle": "Energy intensity and production context.",
            "coverage": coverage_block,
            "summary_matrix": summary_matrix,
            "charts": charts,
            "totals": {
                "plant": totals_plant,
                "areas": totals_areas,
            },
            "comparison": comparison_block,
            "product_context": {
                "enabled": False,
                "title": "Production Context",
                "rows": product_rows,
            },
            "daily_detail": daily_detail,
        }

    def _build_v3_kpi_summary_matrix(
        self,
        kpi_object: Optional[Dict[str, Any]],
        period_type: str = "",
        anchor_date: Optional[date] = None,
        previous_anchor_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Build the compact KPI summary matrix shown above the KPI chart."""
        if not kpi_object:
            return {
                "title": "Current period KPI summary",
                "group_columns": [],
                "rows": [],
            }

        current_summary = kpi_object.get("current", {}).get("summary", {})
        previous_summary = kpi_object.get("previous", {}).get("summary", {})
        current_daily_rows = kpi_object.get("current", {}).get("daily_rows", [])
        previous_daily_rows = kpi_object.get("previous", {}).get("daily_rows", [])
        def build_delta_cell(current_value: Any, previous_value: Any, *, trend_mode: str) -> dict[str, Any]:
            if current_value is None and previous_value is None:
                return {
                    "display": "-",
                    "class": "trend-neutral",
                    "arrow": "neutral",
                }

            if current_value is None or previous_value is None:
                return {
                    "display": "-",
                    "class": "trend-neutral",
                    "arrow": "neutral",
                }

            curr_val = float(current_value or 0.0)
            prev_val = float(previous_value or 0.0)
            delta = curr_val - prev_val
            delta_pct = (delta / prev_val) if prev_val != 0 else None

            if trend_mode == "consumption":
                css_class = self._consumption_trend_class(delta)
            else:
                css_class = self._trend_class(delta)

            return {
                "display": self._fmt_pct(delta_pct),
                "class": css_class,
                "arrow": self._delta_arrow_direction(delta),
            }

        def build_area_cell(current_value: Any, previous_value: Any, *, trend_mode: str, formatter: str = "number") -> dict[str, Any]:
            if formatter == "int":
                value_display = self._fmt_int_or_dash(current_value)
                previous_display = self._fmt_int_or_dash(previous_value)
            else:
                value_display = self._fmt(current_value)
                previous_display = self._fmt(previous_value)

            return {
                "today_display": value_display,
                "yesterday_display": previous_display,
                "delta": build_delta_cell(current_value, previous_value, trend_mode=trend_mode),
            }

        rows: list[dict[str, Any]] = []

        current_anchor_row = self._find_kpi_daily_row_by_date(current_daily_rows, anchor_date)
        previous_anchor_row = self._find_kpi_daily_row_by_date(previous_daily_rows, previous_anchor_date)

        if period_type != "daily":
            rows.append({
                "metric_label": "Production day",
                "cells": {
                    "ico": build_area_cell(
                        current_anchor_row.get("ico_prod") if current_anchor_row else None,
                        previous_anchor_row.get("ico_prod") if previous_anchor_row else None,
                        trend_mode="generic",
                    ),
                    "diode": build_area_cell(
                        current_anchor_row.get("diode_prod") if current_anchor_row else None,
                        previous_anchor_row.get("diode_prod") if previous_anchor_row else None,
                        trend_mode="generic",
                    ),
                    "sakari": build_area_cell(
                        current_anchor_row.get("sakari_prod") if current_anchor_row else None,
                        previous_anchor_row.get("sakari_prod") if previous_anchor_row else None,
                        trend_mode="generic",
                    ),
                    "total": build_area_cell(
                        current_anchor_row.get("prod") if current_anchor_row else None,
                        previous_anchor_row.get("prod") if previous_anchor_row else None,
                        trend_mode="generic",
                    ),
                },
            })

        rows.extend([
            {
                "metric_label": "Energy",
                "cells": {
                    "ico": build_area_cell(
                        current_summary.get("areas", {}).get("ico", {}).get("energy"),
                        previous_summary.get("areas", {}).get("ico", {}).get("energy"),
                        trend_mode="consumption",
                    ),
                    "diode": build_area_cell(
                        current_summary.get("areas", {}).get("diode", {}).get("energy"),
                        previous_summary.get("areas", {}).get("diode", {}).get("energy"),
                        trend_mode="consumption",
                    ),
                    "sakari": build_area_cell(
                        current_summary.get("areas", {}).get("sakari", {}).get("energy"),
                        previous_summary.get("areas", {}).get("sakari", {}).get("energy"),
                        trend_mode="consumption",
                    ),
                    "total": build_area_cell(
                        current_summary.get("plant", {}).get("total_energy"),
                        previous_summary.get("plant", {}).get("total_energy"),
                        trend_mode="consumption",
                    ),
                },
            },
            {
                "metric_label": "Production",
                "cells": {
                    "ico": build_area_cell(
                        current_summary.get("areas", {}).get("ico", {}).get("prod"),
                        previous_summary.get("areas", {}).get("ico", {}).get("prod"),
                        trend_mode="generic",
                    ),
                    "diode": build_area_cell(
                        current_summary.get("areas", {}).get("diode", {}).get("prod"),
                        previous_summary.get("areas", {}).get("diode", {}).get("prod"),
                        trend_mode="generic",
                    ),
                    "sakari": build_area_cell(
                        current_summary.get("areas", {}).get("sakari", {}).get("prod"),
                        previous_summary.get("areas", {}).get("sakari", {}).get("prod"),
                        trend_mode="generic",
                    ),
                    "total": build_area_cell(
                        current_summary.get("plant", {}).get("total_prod"),
                        previous_summary.get("plant", {}).get("total_prod"),
                        trend_mode="generic",
                    ),
                },
            },
            {
                "metric_label": "Energy KPI",
                "cells": {
                    "ico": build_area_cell(
                        current_summary.get("areas", {}).get("ico", {}).get("kpi"),
                        previous_summary.get("areas", {}).get("ico", {}).get("kpi"),
                        trend_mode="consumption",
                    ),
                    "diode": build_area_cell(
                        current_summary.get("areas", {}).get("diode", {}).get("kpi"),
                        previous_summary.get("areas", {}).get("diode", {}).get("kpi"),
                        trend_mode="consumption",
                    ),
                    "sakari": build_area_cell(
                        current_summary.get("areas", {}).get("sakari", {}).get("kpi"),
                        previous_summary.get("areas", {}).get("sakari", {}).get("kpi"),
                        trend_mode="consumption",
                    ),
                    "total": build_area_cell(
                        current_summary.get("plant", {}).get("total_kpi"),
                        previous_summary.get("plant", {}).get("total_kpi"),
                        trend_mode="consumption",
                    ),
                },
            },
        ])

        return {
            "title": "Current period KPI summary",
            "group_columns": [
                {"key": "total", "label": "Total", "tone": "total", "is_total": True},
                {"key": "diode", "label": "DIODE", "tone": "diode", "is_total": False},
                {"key": "ico", "label": "ICO", "tone": "ico", "is_total": False},
                {"key": "sakari", "label": "SAKARI", "tone": "sakari", "is_total": False},
            ],
            "rows": rows,
        }

    def _find_kpi_daily_row_by_date(
        self,
        daily_rows: list[dict[str, Any]],
        target_date: Optional[date],
    ) -> Optional[dict[str, Any]]:
        """Find one KPI daily presentation row by exact date."""
        if target_date is None:
            return None

        for row in daily_rows:
            if row.get("dt") == target_date:
                return row

        return None

    def _build_v3_kpi_charts(
        self,
        kpi_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build KPI charts for the report."""
        if not kpi_object:
            return {
                "daily_grouped_bar": {},
                "daily_dashboard": {
                    "cards": [],
                    "charts": {},
                    "note": "Energy KPI = Energy (kWh) / Production (Ton)",
                },
            }

        daily_rows = kpi_object.get("current", {}).get("daily_rows", [])
        labels = [
            row.get("dt").strftime("%d") if row.get("dt") else "-"
            for row in daily_rows
        ]

        return {
            "daily_grouped_bar": {
                "title": "Daily KPI grouped bar chart",
                "subtitle": "Grouped by day for ICO, DIODE, SAKARI, and Total",
                "option": {
                    "color": ["#84cc16", "#2563eb", "#f59e0b", "#7c3aed"],
                    "tooltip": {
                        "trigger": "axis",
                        "axisPointer": {"type": "shadow"},
                    },
                    "legend": {
                        "top": 6,
                        "left": 8,
                        "itemWidth": 12,
                        "itemHeight": 8,
                    },
                    "grid": {
                        "left": 32,
                        "right": 12,
                        "top": 36,
                        "bottom": 22,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "data": labels,
                        "axisLabel": {"color": "#64748b", "fontSize": 10},
                        "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                    },
                    "yAxis": {
                        "type": "value",
                        "axisLabel": {"color": "#64748b"},
                        "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
                    },
                    "series": [
                        {
                            "name": "ICO",
                            "type": "bar",
                            "barMaxWidth": 18,
                            "data": [self._safe_float(row.get("ico_kpi")) for row in daily_rows],
                        },
                        {
                            "name": "DIODE",
                            "type": "bar",
                            "barMaxWidth": 18,
                            "data": [self._safe_float(row.get("diode_kpi")) for row in daily_rows],
                        },
                        {
                            "name": "SAKARI",
                            "type": "bar",
                            "barMaxWidth": 18,
                            "data": [self._safe_float(row.get("sakari_kpi")) for row in daily_rows],
                        },
                        {
                            "name": "Total",
                            "type": "bar",
                            "barMaxWidth": 18,
                            "data": [self._safe_float(row.get("kpi")) for row in daily_rows],
                        },
                    ],
                },
            },
            "daily_dashboard": self._build_v3_kpi_daily_dashboard(kpi_object),
        }

    def _build_v3_kpi_daily_dashboard(
        self,
        kpi_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build the daily KPI dashboard cards and charts shown in daily reports."""
        if not kpi_object:
            return {
                "cards": [],
                "charts": {},
                "note": "Energy KPI = Energy (kWh) / Production (Ton)",
            }

        current_summary = kpi_object.get("current", {}).get("summary", {})
        previous_summary = kpi_object.get("previous", {}).get("summary", {})
        area_visual_map = self._get_v3_area_visual_map()

        card_specs = [
            ("total", "TOTAL", "#2563eb", "rgba(37, 99, 235, 0.12)"),
            ("diode", "DIODE", area_visual_map["diode"]["bar_color"], area_visual_map["diode"]["bar_tint"]),
            ("ico", "ICO", area_visual_map["ico"]["bar_color"], area_visual_map["ico"]["bar_tint"]),
            ("sakari", "SAKARI", area_visual_map["sakari"]["bar_color"], area_visual_map["sakari"]["bar_tint"]),
        ]

        cards: list[dict[str, Any]] = []
        today_values: list[float | None] = []
        yesterday_values: list[float | None] = []
        variance_items: list[dict[str, Any]] = []

        for key, label, color, tint in card_specs:
            if key == "total":
                current_block = current_summary.get("plant", {})
                previous_block = previous_summary.get("plant", {})
                current_kpi = current_block.get("total_kpi")
                previous_kpi = previous_block.get("total_kpi")
            else:
                current_block = current_summary.get("areas", {}).get(key, {})
                previous_block = previous_summary.get("areas", {}).get(key, {})
                current_kpi = current_block.get("kpi")
                previous_kpi = previous_block.get("kpi")

            delta = None
            delta_pct = None
            if current_kpi is not None and previous_kpi is not None:
                delta = float(current_kpi) - float(previous_kpi)
                delta_pct = (delta / float(previous_kpi)) if float(previous_kpi) != 0 else None

            badge = self._build_v3_kpi_status_badge(delta_pct)
            trend_class = self._consumption_trend_class(delta)

            cards.append({
                "key": key,
                "label": label,
                "value_display": self._fmt(current_kpi),
                "previous_display": self._fmt(previous_kpi),
                "delta_display": self._fmt(delta),
                "delta_pct_display": self._fmt_pct(delta_pct),
                "delta_class": trend_class,
                "delta_arrow": self._delta_arrow_direction(delta),
                "badge_label": badge["label"],
                "badge_class": badge["class"],
                "accent_color": color,
                "accent_tint": tint,
                "is_total": key == "total",
            })

            today_values.append(self._safe_float(current_kpi))
            yesterday_values.append(self._safe_float(previous_kpi))

            variance_value = None
            if delta_pct is not None:
                variance_value = round(float(delta_pct) * 100.0, 2)

            variance_items.append({
                "name": label if label != "TOTAL" else "Total",
                "value": variance_value,
            })

        current_plant = current_summary.get("plant", {})
        previous_plant = previous_summary.get("plant", {})

        prev_total_kpi = self._safe_float(previous_plant.get("total_kpi")) or 0.0
        curr_total_kpi = self._safe_float(current_plant.get("total_kpi")) or 0.0
        prev_total_energy = self._safe_float(previous_plant.get("total_energy"))
        curr_total_energy = self._safe_float(current_plant.get("total_energy"))
        prev_total_prod = self._safe_float(previous_plant.get("total_prod"))
        curr_total_prod = self._safe_float(current_plant.get("total_prod"))

        energy_impact = 0.0
        if (
            prev_total_prod not in (None, 0.0)
            and prev_total_energy is not None
            and curr_total_energy is not None
        ):
            energy_impact = (curr_total_energy - prev_total_energy) / prev_total_prod

        production_impact = 0.0
        if (
            curr_total_energy is not None
            and curr_total_prod not in (None, 0.0)
            and prev_total_prod not in (None, 0.0)
        ):
            production_impact = (
                (curr_total_energy / curr_total_prod)
                - (curr_total_energy / prev_total_prod)
            )

        contribution_area_order = [
            ("diode", "DIODE"),
            ("ico", "ICO"),
            ("sakari", "SAKARI"),
        ]
        contribution_items: list[dict[str, Any]] = []
        total_contribution_energy = 0.0

        for area_key, area_label in contribution_area_order:
            area_energy = self._safe_float(
                current_summary.get("areas", {}).get(area_key, {}).get("energy")
            ) or 0.0
            total_contribution_energy += area_energy
            contribution_items.append({
                "name": area_label,
                "value": round(area_energy, 4),
                "itemStyle": {
                    "color": area_visual_map[area_key]["bar_color"],
                },
            })

        return {
            "cards": cards,
            "note": "Energy KPI = Energy (kWh) / Production (Ton)",
            "charts": {
                "compare_bar": {
                    "title": "Energy KPI: Today vs yesterday",
                    "subtitle": "KPI comparison by Total and workshop",
                    "option": self._build_v3_kpi_compare_bar_option(
                        labels=["Total", "DIODE", "ICO", "SAKARI"],
                        yesterday_values=yesterday_values,
                        today_values=today_values,
                    ),
                },
                "waterfall": {
                    "title": "Total KPI change explanation",
                    "subtitle": "Decomposition of the Total KPI movement",
                    "option": self._build_v3_kpi_waterfall_option(
                        previous_kpi=prev_total_kpi,
                        energy_impact=energy_impact,
                        production_impact=production_impact,
                        current_kpi=curr_total_kpi,
                    ),
                },
                "variance": {
                    "title": "Deviation vs yesterday (%)",
                    "subtitle": "Positive KPI change means higher energy intensity",
                    "option": self._build_v3_kpi_variance_option(variance_items),
                },
                "contribution": {
                    "title": "Energy distribution by line",
                    "subtitle": "Current-day energy contribution",
                    "option": self._build_v3_kpi_contribution_option(
                        contribution_items=contribution_items,
                        total_energy=total_contribution_energy,
                    ),
                },
            },
        }

    def _build_v3_kpi_status_badge(self, delta_pct: Any) -> dict[str, str]:
        """Map KPI daily card delta to a compact status badge."""
        if delta_pct is None:
            return {"label": "N/A", "class": "kpi-badge-neutral"}

        delta_value = float(delta_pct)
        if delta_value > 0.02:
            return {"label": "WATCH", "class": "kpi-badge-watch"}
        if delta_value <= 0.0:
            return {"label": "GOOD", "class": "kpi-badge-good"}
        return {"label": "STABLE", "class": "kpi-badge-stable"}

    def _build_v3_kpi_compare_bar_option(
        self,
        *,
        labels: list[str],
        yesterday_values: list[float | None],
        today_values: list[float | None],
    ) -> Dict[str, Any]:
        """Build the daily KPI compare bar option."""
        return {
            "color": ["#7c3aed", "#2563eb"],
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"},
            },
            "legend": {
                "top": 6,
                "left": 8,
                "itemWidth": 12,
                "itemHeight": 8,
            },
            "grid": {
                "left": 32,
                "right": 12,
                "top": 48,
                "bottom": 24,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "data": labels,
                "axisLabel": {"color": "#64748b", "fontSize": 10},
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": "#64748b"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "series": [
                {
                    "name": "Yesterday",
                    "type": "bar",
                    "barMaxWidth": 22,
                    "data": [
                        self._build_chart_bar_point(value, color="#7c3aed")
                        for value in yesterday_values
                    ],
                },
                {
                    "name": "Today",
                    "type": "bar",
                    "barMaxWidth": 22,
                    "data": [
                        self._build_chart_bar_point(value, color="#2563eb")
                        for value in today_values
                    ],
                },
            ],
        }

    def _build_v3_kpi_waterfall_option(
        self,
        *,
        previous_kpi: float,
        energy_impact: float,
        production_impact: float,
        current_kpi: float,
    ) -> Dict[str, Any]:
        """Build a waterfall-like chart for total KPI movement."""
        energy_base = previous_kpi if energy_impact >= 0 else previous_kpi + energy_impact
        after_energy = previous_kpi + energy_impact
        production_base = after_energy if production_impact >= 0 else after_energy + production_impact

        return {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {
                "left": 32,
                "right": 12,
                "top": 20,
                "bottom": 34,
                "containLabel": True,
            },
            "xAxis": {
                "type": "category",
                "data": ["Yesterday\nKPI", "Energy\nimpact", "Production\nimpact", "Today\nKPI"],
                "axisLabel": {"color": "#64748b", "fontSize": 10, "interval": 0, "lineHeight": 11},
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            },
            "yAxis": {
                "type": "value",
                "axisLabel": {"color": "#64748b"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "series": [
                {
                    "type": "bar",
                    "stack": "waterfall",
                    "silent": True,
                    "itemStyle": {"color": "rgba(0,0,0,0)"},
                    "emphasis": {"disabled": True},
                    "data": [0, round(energy_base, 4), round(production_base, 4), 0],
                },
                {
                    "type": "bar",
                    "stack": "waterfall",
                    "barMaxWidth": 28,
                    "data": [
                        {
                            "value": round(previous_kpi, 4),
                            "itemStyle": {"color": "#7c3aed", "borderRadius": [6, 6, 0, 0]},
                            "label": {"show": True, "position": "top", "formatter": self._fmt(previous_kpi), "color": "#1e293b", "fontSize": 10},
                        },
                        {
                            "value": round(abs(energy_impact), 4),
                            "itemStyle": {
                                "color": "#dc2626" if energy_impact >= 0 else "#16a34a",
                                "borderRadius": [6, 6, 0, 0],
                            },
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": self._fmt(energy_impact),
                                "color": "#1e293b",
                                "fontSize": 10,
                            },
                        },
                        {
                            "value": round(abs(production_impact), 4),
                            "itemStyle": {
                                "color": "#dc2626" if production_impact >= 0 else "#16a34a",
                                "borderRadius": [6, 6, 0, 0],
                            },
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": self._fmt(production_impact),
                                "color": "#1e293b",
                                "fontSize": 10,
                            },
                        },
                        {
                            "value": round(current_kpi, 4),
                            "itemStyle": {"color": "#2563eb", "borderRadius": [6, 6, 0, 0]},
                            "label": {"show": True, "position": "top", "formatter": self._fmt(current_kpi), "color": "#1e293b", "fontSize": 10},
                        },
                    ],
                },
            ],
        }

    def _build_v3_kpi_variance_option(
        self,
        items: list[dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build a horizontal variance chart for KPI change vs yesterday."""
        chart_data = []
        for item in items:
            value = item.get("value")
            if value is None:
                chart_data.append({
                    "value": 0,
                    "name": item.get("name") or "-",
                    "itemStyle": {"color": "#cbd5e1"},
                    "label": {"show": True, "position": "right", "formatter": "-", "color": "#64748b", "fontSize": 10},
                })
                continue

            chart_data.append({
                "value": round(float(value), 2),
                "name": item.get("name") or "-",
                "itemStyle": {"color": "#dc2626" if float(value) >= 0 else "#16a34a"},
                "label": {
                    "show": True,
                    "position": "right" if float(value) >= 0 else "left",
                    "formatter": f"{float(value):+.2f}%",
                    "color": "#1e293b",
                    "fontSize": 10,
                },
            })

        return {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {
                "left": 70,
                "right": 16,
                "top": 12,
                "bottom": 18,
                "containLabel": False,
            },
            "xAxis": {
                "type": "value",
                "axisLabel": {"color": "#64748b", "formatter": "{value}%"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            "yAxis": {
                "type": "category",
                "data": [item.get("name") or "-" for item in items],
                "axisLabel": {"color": "#475569", "fontWeight": 600},
                "axisTick": {"show": False},
                "axisLine": {"show": False},
            },
            "series": [
                {
                    "type": "bar",
                    "barMaxWidth": 22,
                    "data": chart_data,
                }
            ],
        }

    def _build_v3_kpi_contribution_option(
        self,
        *,
        contribution_items: list[dict[str, Any]],
        total_energy: float,
    ) -> Dict[str, Any]:
        """Build a donut chart for area energy contribution."""
        return self._build_v3_contribution_donut_option(
            items=contribution_items,
            total_value=total_energy,
            pie_radius=("45%", "69%"),
            pie_center=("50%", "60%"),
            graphic_left="40%",
            graphic_top="48%",
            legend_orient="horizontal",
            legend_left="center",
            legend_right=0,
            legend_top="5%",
        )

    def _build_v3_contribution_donut_option(
        self,
        *,
        items: list[dict[str, Any]],
        total_value: float,
        center_title: str = "Total Energy",
        center_unit: str = "(kWh)",
        value_unit: str = "kWh",
        pie_radius: tuple[str, str] = ("48%", "73%"),
        pie_center: tuple[str, str] = ("34%", "54%"),
        graphic_left: str = "24%",
        graphic_top: str = "41%",
        legend_orient: str = "vertical",
        legend_left: str | int = "right",
        legend_right: int = 10,
        legend_top: str = "middle",
        center_value_font_size: int = 17,
        center_title_font_size: int = 10,
        center_unit_font_size: int = 9,
        center_title_y: int = 24,
        center_unit_y: int = 40,
        slice_border_radius: int = 0,
    ) -> Dict[str, Any]:
        """Build a detailed donut chart with center total, callouts, and legend."""
        safe_total = float(total_value or 0.0)
        chart_items: list[dict[str, Any]] = []

        for item in items:
            raw_value = float(item.get("value") or 0.0)
            pct_value = (raw_value / safe_total * 100.0) if safe_total > 0 else 0.0

            chart_item = dict(item)
            chart_item["label"] = {
                "show": True,
                "position": "outside",
                "alignTo": "edge",
                "edgeDistance": 10,
                "bleedMargin": 6,
                "distanceToLabelLine": 4,
                "formatter": (
                    f"{{percent|{pct_value:.2f}%}}\n"
                    f"{{value|({self._fmt_chart_callout(raw_value)} {value_unit})}}"
                ),
                "rich": {
                    "percent": {
                        "color": "#475569",
                        "fontSize": 10,
                        "fontWeight": 500,
                        "lineHeight": 13,
                    },
                    "value": {
                        "color": "#0f172a",
                        "fontSize": 9,
                        "fontWeight": 800,
                        "lineHeight": 14,
                    },
                },
            }
            chart_item["labelLine"] = {
                "show": True,
                "length": 14,
                "length2": 12,
                "lineStyle": {
                    "color": "#64748b",
                    "width": 1.4,
                },
            }
            chart_item["emphasis"] = {
                "scale": False,
            }
            chart_items.append(chart_item)

        return {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {
                "orient": legend_orient,
                "left": legend_left,
                "right": legend_right,
                "top": legend_top,
                "itemWidth": 14,
                "itemHeight": 14,
                "icon": "roundRect",
                "textStyle": {"color": "#475569", "fontSize": 10, "fontWeight": 500},
                "itemGap": 12,
            },
            "series": [
                {
                    "name": "Energy contribution",
                    "type": "pie",
                    "radius": list(pie_radius),
                    "center": list(pie_center),
                    "startAngle": 90,
                    "avoidLabelOverlap": True,
                    "minShowLabelAngle": 1,
                    "itemStyle": {
                        "borderColor": "#ffffff",
                        "borderWidth": 4,
                        "borderRadius": slice_border_radius,
                    },
                    "label": {"show": True, "color": "#0f172a"},
                    "labelLine": {"show": True},
                    "data": chart_items,
                }
            ],
            "graphic": [
                {
                    "type": "group",
                    "left": graphic_left,
                    "top": graphic_top,
                    "silent": True,
                    "children": [
                        {
                            "type": "text",
                            "x": 0,
                            "y": 0,
                            "style": {
                                "text": self._fmt_chart_total(total_value),
                                "textAlign": "center",
                                "fill": "#334155",
                                "fontSize": center_value_font_size,
                                "fontWeight": 800,
                            },
                        },
                        {
                            "type": "text",
                            "x": 0,
                            "y": center_title_y,
                            "style": {
                                "text": center_title,
                                "textAlign": "center",
                                "fill": "#475569",
                                "fontSize": center_title_font_size,
                                "fontWeight": 700,
                            },
                        },
                        {
                            "type": "text",
                            "x": 0,
                            "y": center_unit_y,
                            "style": {
                                "text": center_unit,
                                "textAlign": "center",
                                "fill": "#64748b",
                                "fontSize": center_unit_font_size,
                                "fontWeight": 700,
                            },
                        },
                    ],
                }
            ],
        }

    def _count_positive_kpi_days(
        self,
        daily_rows: list[dict[str, Any]],
        field_name: str,
    ) -> int:
        """Count days where a KPI daily field has a positive numeric value."""
        return sum(
            1
            for row in daily_rows
            if isinstance(row.get(field_name), (int, float))
            and float(row.get(field_name)) > 0
        )

    def _safe_float(self, value: Any) -> float | None:
        """Return float for numeric values, otherwise None for chart gaps."""
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _build_kpi_snapshot(self, kpi_object) -> dict:
        comp = kpi_object["comparison"]["plant"]

        return {
            "current_display": self._fmt(comp["current"]),
            "previous_display": self._fmt(comp["previous"]),
            "delta_display": self._fmt(comp["delta"]),
            "delta_pct_display": self._fmt_pct(comp["delta_pct"]),
            "delta_class": self._consumption_trend_class(comp["delta"]),
            "delta_pct_class": self._consumption_trend_class(comp["delta_pct"]),
        }

    def _build_utility_snapshot(self, utility_object) -> list:
        result = []

        metadata = utility_object["current"]["metadata"]
        comparison = utility_object["comparison"]
        current_max = max(
            (float((comparison.get(key, {}) or {}).get("current") or 0.0) for key in metadata.keys()),
            default=0.0,
        )
        previous_max = max(
            (float((comparison.get(key, {}) or {}).get("previous") or 0.0) for key in metadata.keys()),
            default=0.0,
        )

        for key, meta in metadata.items():
            comp = comparison.get(key, {})
            visual = self._get_v3_utility_visual(key, meta)
            current_value = float(comp.get("current") or 0.0)
            previous_value = float(comp.get("previous") or 0.0)

            result.append({
                "key": key,
                "display_name": meta["display_name"],
                "unit": meta["unit"],
                "current_display": self._fmt(comp.get("current")),
                "previous_display": self._fmt(comp.get("previous")),
                "current_value": current_value,
                "previous_value": previous_value,
                "current_fill_pct": round((current_value / current_max) * 100, 2) if current_max > 0 else 0.0,
                "previous_fill_pct": round((previous_value / previous_max) * 100, 2) if previous_max > 0 else 0.0,
                "delta_display": self._fmt(comp.get("delta")),
                "delta_pct_display": self._fmt_pct(comp.get("delta_pct")),
                "delta_class": self._consumption_trend_class(comp.get("delta")),
                "delta_pct_class": self._consumption_trend_class(comp.get("delta_pct")),
                "value_tone_class": visual.get("tone_class", "utility-tone-neutral"),
            })

        return result

    def _get_v3_utility_visual(
        self,
        utility_key: str,
        meta: dict[str, Any],
    ) -> dict[str, str]:
        """Return color tone class for utility summary rows."""
        text = f"{utility_key} {meta.get('display_name', '')}".lower()
        category = str(meta.get("category") or "").lower()

        if "ico" in text:
            return {"tone_class": "utility-tone-ico"}
        if "diode" in text:
            return {"tone_class": "utility-tone-diode"}
        if "sakari" in text:
            return {"tone_class": "utility-tone-sakari"}
        if "steam" in text or category == "steam":
            return {"tone_class": "utility-tone-steam"}
        if "water" in text or category == "water":
            return {"tone_class": "utility-tone-water"}

        return {"tone_class": "utility-tone-neutral"}

    def _build_global_coverage(self, kpi_object) -> dict:
        """Build global coverage summary for the report banner."""
        cov = kpi_object["current"]["coverage"]

        return {
            "has_warning": not cov["is_full_coverage"],
            "message": "KPI data is partially missing or not applicable for some days.",
            "coverage_items": [
                {
                    "label": "KPI",
                    "coverage_display": f"{cov['coverage_days']}/{cov['report_total_days']}",
                    "coverage_note": self._map_kpi_coverage_note(cov.get("coverage_note")),
                }
            ],
        }

    def _build_daily_columns(self, utility_object):
        metadata = utility_object["current"]["metadata"]

        return [
            {"key": k, "display_name": v["display_name"]}
            for k, v in metadata.items()
        ]

    def _build_daily_rows(self, utility_object):
        timeseries = utility_object["current"]["timeseries"]
        metadata_keys = list(utility_object["current"]["metadata"].keys())

        rows = []

        for row in timeseries:
            values = []
            missing_count = 0
            total_count = len(metadata_keys)

            for key in metadata_keys:
                val = row.get(key)

                if val is None or val == 0:
                    missing_count += 1

                values.append({
                    "display": self._fmt(val)
                })

            # ===== Determine status =====
            if missing_count == total_count:
                status = "Missing"
                status_class = "status-missing"
                row_class = "row-missing"
                note = "No data for this day"

            elif missing_count > 0:
                status = "Partial"
                status_class = "status-partial"
                row_class = "row-partial"
                note = f"{missing_count}/{total_count} utilities missing"

            else:
                status = "OK"
                status_class = "status-ok"
                row_class = "row-ok"
                note = ""

            rows.append({
                "date": row["dt"],
                "date_display": self._format_date_with_weekday(row["dt"]),
                "daily_values": values,
                "status": status,
                "status_class": status_class,
                "row_class": row_class,
                "coverage_note": note,
            })

        return rows

    def _trend_class(self, val):
        if val is None:
            return "trend-neutral"
        if val > 0:
            return "trend-up"
        if val < 0:
            return "trend-down"
        return "trend-neutral"

    def _build_notes(self, kpi_object, utility_object):
        notes = []

        cov = kpi_object["current"]["coverage"]

        if not cov["is_full_coverage"]:
            notes.extend(cov.get("messages", []))

        return notes

    def _build_utility_coverage(self, utility_object):
        """Calculate utility data coverage."""

        timeseries = utility_object["current"]["timeseries"]
        metadata_keys = list(utility_object["current"]["metadata"].keys())

        total_days = len(timeseries)
        covered_days = 0

        for row in timeseries:
            has_data = False

            for key in metadata_keys:
                val = row.get(key)
                if val not in (None, 0):
                    has_data = True
                    break

            if has_data:
                covered_days += 1

        is_complete = covered_days == total_days

        return {
            "coverage_days": covered_days,
            "total_days": total_days,
            "coverage_display": f"{covered_days}/{total_days}",
            "is_complete": is_complete,
            "coverage_note": None if is_complete else "Some days have missing utility data.",
        }

    def _map_kpi_coverage_note(self, value: str | None) -> str:
        """Map internal KPI coverage label to a user-friendly message."""
        if value == "partial_or_not_applicable":
            return "KPI data is partially missing or not applicable for some days."
        if value == "full":
            return "Full KPI coverage."
        return value or ""

    def _build_kpi_area_snapshot_rows(self, kpi_object) -> list[dict[str, Any]]:
        """Build KPI area snapshot cards for executive summary."""
        rows: list[dict[str, Any]] = []

        areas = kpi_object["comparison"]["areas"]

        area_display_order = [
            ("ico", "ICO"),
            ("diode", "DIODE"),
            ("sakari", "SAKARI"),
        ]

        for area_key, area_name in area_display_order:
            area_obj = areas.get(area_key, {})

            rows.append({
                "area_key": area_key,
                "area_name": area_name,
                "current_display": self._fmt(area_obj.get("current")),
                "previous_display": self._fmt(area_obj.get("previous")),
                "delta_display": self._fmt(area_obj.get("delta")),
                "delta_pct_display": self._fmt_pct(area_obj.get("delta_pct")),
                "delta_class": self._consumption_trend_class(area_obj.get("delta")),
                "delta_pct_class": self._consumption_trend_class(area_obj.get("delta_pct")),
            })

        return rows

    def _build_kpi_uncovered_ranges(
        self,
        uncovered_ranges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build display-friendly uncovered date ranges."""
        result: list[dict[str, Any]] = []

        for item in uncovered_ranges:
            start_date = item.get("start_date")
            end_date = item.get("end_date")

            result.append({
                "start_date": start_date,
                "end_date": end_date,
                "display": f"{start_date} → {end_date}",
            })

        return result

    def _build_kpi_daily_rows(self, kpi_object) -> list[dict[str, Any]]:
        """Build KPI daily detail rows for report rendering."""
        rows: list[dict[str, Any]] = []

        current_daily_rows = kpi_object["current"].get("daily_rows", [])

        for row in current_daily_rows:
            coverage_status = row.get("coverage_status")

            if coverage_status == "covered":
                status = "OK"
                status_class = "status-ok"
                row_class = "row-ok"
            elif coverage_status == "covered_by_period_block":
                status = "Block"
                status_class = "status-partial"
                row_class = "row-partial"
            else:
                status = "Missing"
                status_class = "status-missing"
                row_class = "row-missing"

            rows.append({
                "date": row.get("dt"),
                "date_display": self._format_date_with_weekday(row.get("dt")),
                "time_frame_source": row.get("time_frame_source"),

                "plant_prod_display": self._fmt_or_dash(row.get("prod")),
                "ico_prod_display": self._fmt_or_dash(row.get("ico_prod")),
                "diode_prod_display": self._fmt_or_dash(row.get("diode_prod")),
                "sakari_prod_display": self._fmt_or_dash(row.get("sakari_prod")),

                "plant_energy_display": self._fmt_or_dash(row.get("energy")),
                "ico_energy_display": self._fmt_or_dash(row.get("ico_energy")),
                "diode_energy_display": self._fmt_or_dash(row.get("diode_energy")),
                "sakari_energy_display": self._fmt_or_dash(row.get("sakari_energy")),

                "plant_kpi_display": self._fmt_or_dash(row.get("kpi")),
                "ico_kpi_display": self._fmt_or_dash(row.get("ico_kpi")),
                "diode_kpi_display": self._fmt_or_dash(row.get("diode_kpi")),
                "sakari_kpi_display": self._fmt_or_dash(row.get("sakari_kpi")),

                "status": status,
                "status_class": status_class,
                "row_class": row_class,
                "coverage_note": row.get("note") or "",
            })

        return rows

    def _fmt(self, val):
        """Format numeric value for display. Keep zero as numeric zero."""
        if val is None:
            return "-"
        return f"{float(val):,.2f}"

    def _hex_to_rgba(self, value: str, opacity: float) -> str:
        """Convert a hex color to rgba text, falling back to a blue tint."""
        text = str(value or "").strip().lstrip("#")
        if len(text) == 3:
            text = "".join(char * 2 for char in text)

        if len(text) != 6:
            return f"rgba(37, 99, 235, {opacity})"

        try:
            red = int(text[0:2], 16)
            green = int(text[2:4], 16)
            blue = int(text[4:6], 16)
        except ValueError:
            return f"rgba(37, 99, 235, {opacity})"

        safe_opacity = max(0.0, min(1.0, float(opacity)))
        return f"rgba({red}, {green}, {blue}, {safe_opacity})"

    def _fmt_or_dash(self, val):
        """Return dash for None, otherwise numeric display including zero."""
        if val is None:
            return "-"
        return f"{float(val):,.2f}"

    def _fmt_int_or_dash(self, val: Any) -> str:
        """Return dash for None, otherwise integer display without decimals."""
        if val is None:
            return "-"
        return f"{int(round(float(val))):,}"

    def _fmt_pct(self, val):
        """Format ratio to percent display."""
        if val is None:
            return "-"
        return f"{float(val) * 100:.2f}%"

    def _fmt_chart_total(self, val: Any) -> str:
        """Format chart center totals with one decimal for a cleaner dashboard look."""
        if val is None:
            return "-"
        return f"{float(val):,.1f}"

    def _fmt_chart_callout(self, val: Any) -> str:
        """Format callout labels with one decimal to keep donut annotations compact."""
        if val is None:
            return "-"
        return f"{float(val):,.1f}"

    def _fmt_chart_compact(self, val: Any) -> str:
        """Format bar labels into short k/M strings to reduce overlap."""
        if val is None:
            return "-"

        numeric_value = float(val)
        abs_value = abs(numeric_value)

        if abs_value >= 1_000_000:
            return f"{numeric_value / 1_000_000:.1f}M"
        if abs_value >= 1_000:
            return f"{numeric_value / 1_000:.1f}k"
        return f"{numeric_value:,.1f}"

    def _consumption_trend_class(self, val):
        """Return trend class for consumption/intensity metrics.

        Business rule:
        - Positive delta means worse (higher consumption/intensity) -> red
        - Negative delta means better -> green
        """
        if val is None:
            return "trend-neutral"
        if val > 0:
            return "trend-down"
        if val < 0:
            return "trend-up"
        return "trend-neutral"

    def _delta_arrow_direction(self, val: Any) -> str:
        """Return arrow direction based on delta sign, independent from color class."""
        if val is None:
            return "neutral"
        if float(val) > 0:
            return "up"
        if float(val) < 0:
            return "down"
        return "neutral"

    def _format_date_with_weekday(self, value) -> str:
        """Format date as YYYY-MM-DD (Day)."""
        if value is None:
            return "-"

        weekday = value.strftime("%a")
        return f"{value.isoformat()} ({weekday})"

    def _format_date_short_label(self, value) -> str:
        """Format date as Mon DD, YYYY for compact dashboard display."""
        if value in (None, ""):
            return "-"

        if isinstance(value, str):
            value = datetime.fromisoformat(value).date()
        elif isinstance(value, datetime):
            value = value.date()

        if not isinstance(value, date):
            return str(value)

        return value.strftime("%b %d, %Y")

    def _build_energy_snapshot(self, energy_object) -> dict[str, Any]:
        """Build executive energy snapshot."""
        if not energy_object:
            return {}

        area_stats = self._build_v3_electricity_area_stats(energy_object)

        current_total = 0.0
        previous_total = 0.0

        for area_key in ["diode", "ico", "sakari"]:
            current_total += float(
                energy_object["current"]["summary"].get(area_key, {}).get("total_energy", 0.0)
            )
            previous_total += float(
                energy_object["previous"]["summary"].get(area_key, {}).get("total_energy", 0.0)
            )

        delta = current_total - previous_total
        delta_pct = (delta / previous_total) if previous_total != 0 else None

        current_rows = energy_object["current"].get("daily_summary_rows", [])
        total_days = len(current_rows)
        average_per_day = (current_total / total_days) if total_days else None

        return {
            "current_display": self._fmt(current_total),
            "previous_display": self._fmt(previous_total),
            "delta_display": self._fmt(delta),
            "delta_pct_display": self._fmt_pct(delta_pct),
            "delta_class": self._consumption_trend_class(delta),
            "delta_pct_class": self._consumption_trend_class(delta_pct),
            "meter_active_total_display": area_stats.get("plant", {}).get("active_total_display", "-"),
            "total_days": total_days,
            "average_per_day_display": self._fmt(average_per_day),
        }
