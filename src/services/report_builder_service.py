# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
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
        )

        v3_utility_section = self._build_v3_utility_section(
            utility_object=utility_object,
        )

        v3_period_block["flags"]["show_sensor_monitoring"] = bool(
            v3_utility_section.get("sensor_monitoring", {}).get("enabled", False)
        )

        v3_kpi_section = self._build_v3_kpi_section(
            kpi_object=kpi_object,
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
            "version": "v3",
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

            stats[area_key] = {
                "current_ratio_display": self._fmt_pct(current_ratio),
                "previous_ratio_display": self._fmt_pct(previous_ratio),
                "active_meter_count": active_meter_count,
                "total_meter_count": total_meter_count,
                "active_total_display": f"{active_meter_count}/{total_meter_count}",
            }

        return stats

    def _build_v3_electricity_section(
        self,
        energy_object: Optional[Dict[str, Any]],
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
                "top10": {"rows": [], "excluded_meter_rules": {}},
                "charts": {
                    "daily_trend": {},
                    "area_comparison": {},
                },
                "daily_summary": {"title": "Daily Summary Table", "rows": []},
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

        top10_rows: list[dict[str, Any]] = []
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

        for item in energy_object.get("comparison", {}).get("top10_meters", []):
            current_value = item.get("current")
            previous_value = item.get("previous")

            current_ratio = None
            previous_ratio = None

            if current_total_all_areas > 0 and current_value is not None:
                current_ratio = current_value / current_total_all_areas

            if previous_total_all_areas > 0 and previous_value is not None:
                previous_ratio = previous_value / previous_total_all_areas

            current_display = self._fmt(current_value)
            previous_display = self._fmt(previous_value)

            current_pct_display = self._fmt_pct(current_ratio) if current_ratio is not None else "-"
            previous_pct_display = self._fmt_pct(previous_ratio) if previous_ratio is not None else "-"

            top10_rows.append({
                "rank": item.get("rank"),
                "meter_key": item.get("meter_name"),
                "meter_name": item.get("meter_name"),
                "display_name": item.get("meter_name"),
                "area": item.get("area"),
                "current_display": current_display,
                "current_pct_display": current_pct_display,
                "previous_display": previous_display,
                "previous_pct_display": previous_pct_display,
                "delta_display": self._fmt(item.get("delta")),
                "delta_pct_display": self._fmt_pct(item.get("delta_pct")),
                "delta_class": self._consumption_trend_class(item.get("delta")),
                "delta_pct_class": self._consumption_trend_class(item.get("delta_pct")),
            })

        daily_summary_rows = energy_object.get("current", {}).get("daily_summary_rows", [])
        daily_detail_tables = energy_object.get("current", {}).get("daily_tables", [])
        charts = self._build_v3_electricity_charts(energy_object)

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
                "excluded_meter_rules": {},
            },
            "charts": charts,
            "daily_summary": {
                "title": "Daily Summary Table",
                "rows": daily_summary_rows,
            },
            "daily_detail_tables": daily_detail_tables,
        }

    def _build_v3_electricity_charts(
        self,
        energy_object: Optional[Dict[str, Any]],
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

        return {
            "daily_trend": {
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
            },
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

    def _build_v3_kpi_section(
        self,
        kpi_object: Optional[Dict[str, Any]],
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

        return {
            "title": "ENERGY KPI",
            "subtitle": "Energy intensity and production context.",
            "coverage": coverage_block,
            "totals": {
                "plant": totals_plant,
                "areas": totals_areas,
            },
            "comparison": comparison_block,
            "product_context": {
                "enabled": True,
                "title": "Production Context",
                "rows": product_rows,
            },
            "daily_detail": daily_detail,
        }

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
            "total_days": total_days,
            "average_per_day_display": self._fmt(average_per_day),
        }
