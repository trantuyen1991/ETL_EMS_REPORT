# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
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
        )

        v3_period_block["flags"]["show_sensor_monitoring"] = bool(
            v3_utility_section.get("sensor_monitoring", {}).get("enabled", False)
        )

        v3_kpi_section = self._build_v3_kpi_section(
            kpi_object=kpi_object,
            period_type=str(period.get("type") or "").strip().lower(),
        )

        notes = self._build_notes(kpi_object, utility_object)

        report_context: Dict[str, Any] = {
            "meta": {
                "report_title": meta.get("report_title", ""),
                "report_subtitle": "Automatic Report",
                "workshop_name": meta.get("workshop_name", ""),
                "energy_unit": meta.get("energy_unit", "kWh"),
                "kpi_unit": meta.get("kpi_unit", "kWh/Ton"),
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
            },
            "ico": {
                "display": "ICO",
                "bar_color": "#84cc16",
                "bar_tint": "rgba(132, 204, 22, 0.16)",
            },
            "sakari": {
                "display": "SAKARI",
                "bar_color": "#f59e0b",
                "bar_tint": "rgba(245, 158, 11, 0.16)",
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

    def _build_v3_area_daily_summary_rows(
        self,
        daily_tables: list[dict[str, Any]],
        area_display_order: list[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        """Build the additional daily summary table split by workshop area."""
        table_lookup = {
            table.get("area_key"): table
            for table in daily_tables
        }
        row_lookup: dict[str, dict[date, dict[str, Any]]] = {}
        all_dates: set[date] = set()

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
        area_daily_summary_rows = self._build_v3_area_daily_summary_rows(
            daily_tables=daily_detail_tables,
            area_display_order=area_display_order,
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
                "area_tables": area_top10_tables,
                "excluded_meter_rules": {},
            },
            "charts": charts,
            "daily_summary": {
                "title": "Daily Summary Table",
                "rows": daily_summary_rows,
                "area_rows": area_daily_summary_rows,
            },
            "daily_detail_tables": daily_detail_tables,
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
            }

        current_daily_rows = sorted(
            energy_object.get("current", {}).get("daily_summary_rows", []),
            key=lambda row: row.get("date") or datetime.min.date(),
        )
        previous_daily_rows = sorted(
            energy_object.get("previous", {}).get("daily_summary_rows", []),
            key=lambda row: row.get("date") or datetime.min.date(),
        )

        max_daily_points = max(len(current_daily_rows), len(previous_daily_rows))
        daily_labels = [f"D{index}" for index in range(1, max_daily_points + 1)]

        current_daily_values = [
            self._parse_display_number(row.get("total_energy_display"))
            for row in current_daily_rows
        ]
        previous_daily_values = [
            self._parse_display_number(row.get("total_energy_display"))
            for row in previous_daily_rows
        ]

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
            })

        area_labels = [row["area_name"] for row in area_rows]
        current_area_values = [row["current_value"] for row in area_rows]
        previous_area_values = [row["previous_value"] for row in area_rows]

        if period_type == "daily":
            current_total_value = sum(current_area_values)
            share_chart = {
                "title": "Area share",
                "subtitle": "Current day contribution by workshop",
                "option": {
                    "color": ["#2563eb", "#84cc16", "#f59e0b"],
                    "tooltip": {
                        "trigger": "item",
                        "formatter": "{b}: {c} ({d}%)",
                    },
                    "legend": {
                        "top": 4,
                        "left": 8,
                        "itemWidth": 12,
                        "itemHeight": 8,
                    },
                    "graphic": [
                        {
                            "type": "group",
                            "left": "center",
                            "top": "60%",
                            "children": [
                                {
                                    "type": "text",
                                    "x": 0,
                                    "y": -10,
                                    "style": {
                                        "text": self._fmt(current_total_value),
                                        "textAlign": "center",
                                        "textVerticalAlign": "middle",
                                        "fill": "#0f172a",
                                        "fontSize": 17,
                                        "fontWeight": 700,
                                    },
                                },
                                {
                                    "type": "text",
                                    "x": 0,
                                    "y": 12,
                                    "style": {
                                        "text": "Current total",
                                        "textAlign": "center",
                                        "textVerticalAlign": "middle",
                                        "fill": "#64748b",
                                        "fontSize": 10,
                                        "fontWeight": 600,
                                    },
                                },
                            ],
                        }
                    ],
                    "series": [
                        {
                            "name": "Area share",
                            "type": "pie",
                            "radius": ["52%", "76%"],
                            "center": ["50%", "60%"],
                            "avoidLabelOverlap": True,
                            "itemStyle": {
                                "borderColor": "#ffffff",
                                "borderWidth": 6,
                                "borderRadius": 12,
                            },
                            "label": {
                                "show": True,
                                "formatter": "{b}\n{d}%",
                                "color": "#334155",
                                "fontSize": 11,
                                "fontWeight": 600,
                            },
                            "labelLine": {
                                "length": 10,
                                "length2": 8,
                                "lineStyle": {"color": "#94a3b8"},
                            },
                            "data": [
                                {
                                    "name": row["area_name"],
                                    "value": row["current_value"],
                                }
                                for row in area_rows
                            ],
                        }
                    ],
                },
            }
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
                        "left": 30,
                        "right": 12,
                        "top": 36,
                        "bottom": 22,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "boundaryGap": False,
                        "data": daily_labels,
                        "axisLabel": {"color": "#64748b"},
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
                            "smooth": True,
                            "symbol": "circle",
                            "symbolSize": 7,
                            "showSymbol": False,
                            "lineStyle": {"width": 3, "color": "#2563eb"},
                            "itemStyle": {"color": "#2563eb"},
                            "areaStyle": {"color": "rgba(37, 99, 235, 0.12)"},
                            "data": current_daily_values,
                        },
                        {
                            "name": "Previous period",
                            "type": "line",
                            "smooth": True,
                            "symbol": "circle",
                            "symbolSize": 7,
                            "showSymbol": False,
                            "lineStyle": {"width": 2, "type": "dashed", "color": "#7c3aed"},
                            "itemStyle": {"color": "#7c3aed"},
                            "areaStyle": {"color": "rgba(124, 58, 237, 0.08)"},
                            "data": previous_daily_values,
                        },
                    ],
                },
            }

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
                        "top": 36,
                        "bottom": 22,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "data": area_labels,
                        "axisLabel": {"color": "#64748b"},
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
                            "barMaxWidth": 26,
                            "itemStyle": {"color": "#2563eb", "borderRadius": [6, 6, 0, 0]},
                            "data": current_area_values,
                        },
                        {
                            "name": "Previous period",
                            "type": "bar",
                            "barMaxWidth": 26,
                            "itemStyle": {"color": "#7c3aed", "borderRadius": [6, 6, 0, 0]},
                            "data": previous_area_values,
                        },
                    ],
                },
            },
        }

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
                "title": "UTILITY USAGE",
                "subtitle": "Consumption and sensor monitoring.",
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
                    "catalog": {},
                    "groups": [],
                    "default_mode": "avg",
                    "metric_columns": [],
                    "daily_rows": [],
                },
            }

        coverage = self._build_utility_coverage(utility_object)
        total_rows = self._build_utility_snapshot(utility_object)
        daily_columns = self._build_daily_columns(utility_object)
        daily_rows = self._build_daily_rows(utility_object)
        charts = self._build_v3_utility_charts(utility_object)

        return {
            "title": "UTILITY USAGE",
            "subtitle": "Consumption and sensor monitoring.",
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
            "sensor_monitoring": {
                "enabled": bool(
                    utility_object.get("current", {})
                    .get("sensor_monitoring", {})
                    .get("enabled", False)
                ),
                "title": "Sensor monitoring",
                "subtitle": "Average and maximum daily sensor readings.",
                "default_mode": "avg",
                "metric_columns": utility_object.get("current", {})
                .get("sensor_monitoring", {})
                .get("metric_columns", []),
                "daily_rows": utility_object.get("current", {})
                .get("sensor_monitoring", {})
                .get("daily_rows", []),
            },
        }

    def _build_v3_utility_charts(
        self,
        utility_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build ECharts options for utility comparison."""
        if not utility_object:
            return {
                "comparison_bar": {},
            }

        metadata = utility_object.get("current", {}).get("metadata", {})
        comparison = utility_object.get("comparison", {})

        labels: list[str] = []
        chart_labels: list[str] = []
        current_values: list[float] = []
        previous_values: list[float] = []

        for key, meta in metadata.items():
            display_name = meta.get("display_name") or key
            labels.append(display_name)
            if display_name.count(" ") >= 2:
                first, second, third = display_name.split(" ", 2)
                chart_labels.append(f"{first} {second}\n{third}")
            elif " " in display_name:
                first, second = display_name.split(" ", 1)
                chart_labels.append(f"{first}\n{second}")
            else:
                chart_labels.append(display_name)
            current_values.append(float(comparison.get(key, {}).get("current", 0.0) or 0.0))
            previous_values.append(float(comparison.get(key, {}).get("previous", 0.0) or 0.0))

        return {
            "comparison_bar": {
                "title": "Utility comparison",
                "subtitle": "Current vs previous total by load type",
                "option": {
                    "color": ["#0f766e", "#7c3aed"],
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
                        "bottom": 28,
                        "containLabel": True,
                    },
                    "xAxis": {
                        "type": "category",
                        "data": chart_labels,
                        "axisLabel": {
                            "color": "#64748b",
                            "fontSize": 10,
                            "lineHeight": 11,
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
                            "itemStyle": {"color": "#0f766e", "borderRadius": [6, 6, 0, 0]},
                            "data": current_values,
                        },
                        {
                            "name": "Previous period",
                            "type": "bar",
                            "barMaxWidth": 24,
                            "itemStyle": {"color": "#7c3aed", "borderRadius": [6, 6, 0, 0]},
                            "data": previous_values,
                        },
                    ],
                },
            },
        }

    def _build_v3_kpi_section(
        self,
        kpi_object: Optional[Dict[str, Any]],
        period_type: str = "",
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
        current_coverage = kpi_object.get("current", {}).get("coverage", {})
        previous_coverage = kpi_object.get("previous", {}).get("coverage", {})

        current_prod_days = {
            "ico": self._count_positive_kpi_days(current_daily_rows, "ico_prod"),
            "diode": self._count_positive_kpi_days(current_daily_rows, "diode_prod"),
            "sakari": self._count_positive_kpi_days(current_daily_rows, "sakari_prod"),
            "plant": self._count_positive_kpi_days(current_daily_rows, "prod"),
        }
        previous_prod_days = {
            "ico": self._count_positive_kpi_days(previous_daily_rows, "ico_prod"),
            "diode": self._count_positive_kpi_days(previous_daily_rows, "diode_prod"),
            "sakari": self._count_positive_kpi_days(previous_daily_rows, "sakari_prod"),
            "plant": self._count_positive_kpi_days(previous_daily_rows, "prod"),
        }

        if current_prod_days["plant"] == 0:
            current_prod_days["plant"] = int(current_coverage.get("coverage_days", 0) or 0)
        if previous_prod_days["plant"] == 0:
            previous_prod_days["plant"] = int(previous_coverage.get("coverage_days", 0) or 0)

        def build_delta_cell(current_value: Any, previous_value: Any, *, trend_mode: str) -> dict[str, Any]:
            if current_value is None and previous_value is None:
                return {
                    "display": "-",
                    "class": "trend-neutral",
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
            }

        def build_area_cell(current_value: Any, previous_value: Any, *, trend_mode: str, formatter: str = "number") -> dict[str, Any]:
            if formatter == "int":
                value_display = self._fmt_int_or_dash(current_value)
            else:
                value_display = self._fmt(current_value)

            return {
                "value_display": value_display,
                "delta": build_delta_cell(current_value, previous_value, trend_mode=trend_mode),
            }

        rows: list[dict[str, Any]] = [
            {
                "metric_label": "Production day",
                "cells": {
                    "ico": build_area_cell(current_prod_days["ico"], previous_prod_days["ico"], trend_mode="generic", formatter="int"),
                    "diode": build_area_cell(current_prod_days["diode"], previous_prod_days["diode"], trend_mode="generic", formatter="int"),
                    "sakari": build_area_cell(current_prod_days["sakari"], previous_prod_days["sakari"], trend_mode="generic", formatter="int"),
                    "total": build_area_cell(current_prod_days["plant"], previous_prod_days["plant"], trend_mode="generic", formatter="int"),
                },
            },
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
        ]

        return {
            "title": "Current period KPI summary",
            "group_columns": [
                {"key": "ico", "label": "ICO"},
                {"key": "diode", "label": "DIODE"},
                {"key": "sakari", "label": "SAKARI"},
                {"key": "total", "label": "Total"},
            ],
            "rows": rows,
        }

    def _build_v3_kpi_charts(
        self,
        kpi_object: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build KPI charts for the report."""
        if not kpi_object:
            return {
                "daily_grouped_bar": {},
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

        for key, meta in metadata.items():
            comp = comparison.get(key, {})

            result.append({
                "display_name": meta["display_name"],
                "unit": meta["unit"],
                "current_display": self._fmt(comp.get("current")),
                "previous_display": self._fmt(comp.get("previous")),
                "delta_display": self._fmt(comp.get("delta")),
                "delta_pct_display": self._fmt_pct(comp.get("delta_pct")),
                "delta_class": self._consumption_trend_class(comp.get("delta")),
                "delta_pct_class": self._consumption_trend_class(comp.get("delta_pct")),
            })

        return result

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

    def _format_date_with_weekday(self, value) -> str:
        """Format date as YYYY-MM-DD (Day)."""
        if value is None:
            return "-"

        weekday = value.strftime("%a")
        return f"{value.isoformat()} ({weekday})"

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
