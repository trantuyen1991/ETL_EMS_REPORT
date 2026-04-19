# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)

from src.config.energy_metadata import get_energy_area_metadata

class EnergyService:
    """Service for energy summary, comparison, top meter, and daily detail."""

    def build_full_energy_object(
        self,
        current_area_rows: dict[str, list[dict[str, Any]]],
        previous_area_rows: dict[str, list[dict[str, Any]]],
        current_kpi_summary: dict[str, Any],
        previous_kpi_summary: dict[str, Any],
        report_start: date,
        report_end: date,
        previous_start: date,
        previous_end: date,
    ) -> dict[str, Any]:
        """Build full energy object for V2 report."""
        current_obj = self.build_energy_report_object(
            area_rows=current_area_rows,
            kpi_summary=current_kpi_summary,   
            report_start=report_start,
            report_end=report_end,
        )

        previous_obj = self.build_energy_report_object(
            area_rows=previous_area_rows,
            kpi_summary=previous_kpi_summary,  
            report_start=previous_start,
            report_end=previous_end,
        )

        comparison = {
            "summary": self.build_energy_comparison(
                current_summary=current_obj["summary"],
                previous_summary=previous_obj["summary"],
            ),
            "top10_meters": self.build_top10_comparison(
                current_top10=current_obj["top10_meters"],
                previous_area_rows=previous_area_rows,
                previous_kpi_summary=previous_kpi_summary,
                report_start=previous_start,
                report_end=previous_end,
            ),
        }

        return {
            "current": current_obj,
            "previous": previous_obj,
            "comparison": comparison,
        }

    def build_energy_report_object(
        self,
        area_rows: dict[str, list[dict[str, Any]]],
        kpi_summary: dict[str, Any],
        report_start: date,
        report_end: date,
    ) -> dict[str, Any]:
        """Build one period energy object."""
        filtered_area_rows = {
            area: self._filter_rows_in_period(rows, report_start, report_end)
            for area, rows in area_rows.items()
        }

        kpi_daily_lookup = self._build_kpi_daily_energy_lookup(
            kpi_summary=kpi_summary,
            report_start=report_start,
            report_end=report_end,
        )

        area_tables = {
            area: self.build_daily_energy_table(
                area_key=area,
                rows=rows,
                area_daily_energy_lookup={
                    dt_value: daily_item.get(area)
                    for dt_value, daily_item in kpi_daily_lookup.items()
                },
            )
            for area, rows in filtered_area_rows.items()
        }

        return {
            "summary": self.build_energy_summary(
                area_tables=area_tables,
                kpi_summary=kpi_summary,
            ),
            "top10_meters": self.build_top10_meters(area_tables),
            "daily_summary_rows": self.build_daily_summary_rows(
                area_tables=area_tables,
                kpi_daily_lookup=kpi_daily_lookup,
            ),
            "daily_tables": [
                area_tables["diode"],
                area_tables["ico"],
                area_tables["sakari"],
            ],
        }
    def _extract_meter_columns(
        self,
        rows: list[dict[str, Any]],
    ) -> list[str]:
        """Extract dynamic meter columns from raw rows."""
        excluded = {"dt"}

        column_names: set[str] = set()

        for row in rows:
            for key in row.keys():
                if key not in excluded:
                    column_names.add(key)

        return sorted(column_names)

    def build_daily_energy_table(
        self,
        area_key: str,
        rows: list[dict[str, Any]],
        area_daily_energy_lookup: dict[date, float | None],
    ) -> dict[str, Any]:
        """Build one dynamic daily energy table."""
        area_metadata = get_energy_area_metadata()
        area_meta = area_metadata.get(area_key, {})

        main_feeder_columns = list(area_meta.get("main_feeders", []))
        exclude_from_top10 = list(area_meta.get("exclude_from_top10", []))
        unknown_load_key = area_meta.get("unknown_load_key", "unknown_load")
        unknown_load_display_name = area_meta.get("unknown_load_display_name", "Unknown Load")

        meter_columns = self._extract_meter_columns(rows)

        submeter_columns = [
            column
            for column in meter_columns
            if column not in exclude_from_top10
        ]

        columns = [{"key": "dt", "display_name": "Date", "is_date": True}]

        for column in meter_columns:
            meter_role = "main_feeder" if column in main_feeder_columns else "submeter"

            columns.append({
                "key": column,
                "display_name": column,
                "is_date": False,
                "meter_role": meter_role,
            })

        # Append unknown load column ONLY ONCE
        columns.append({
            "key": unknown_load_key,
            "display_name": unknown_load_display_name,
            "is_date": False,
            "meter_role": "unknown",
        })

        daily_rows: list[dict[str, Any]] = []

        for row in sorted(rows, key=lambda item: self._to_date(item.get("dt"))):
            dt_value = self._to_date(row.get("dt"))

            cells: list[dict[str, Any]] = []
            main_feeder_total = 0.0
            submeter_total = 0.0

            # First pass: calculate feeder/submeter totals
            for column in meter_columns:
                raw_value = row.get(column)

                if isinstance(raw_value, (int, float)):
                    value = float(raw_value)

                    if column in main_feeder_columns:
                        main_feeder_total += value
                    elif column in submeter_columns:
                        submeter_total += value

            official_daily_total = area_daily_energy_lookup.get(dt_value)
            official_daily_total_value = float(official_daily_total) if official_daily_total is not None else 0.0

            unknown_load = official_daily_total_value - submeter_total

            # Build row numeric map including unknown load
            row_numeric_map: dict[str, float] = {}

            for column in meter_columns:
                raw_value = row.get(column)
                if isinstance(raw_value, (int, float)):
                    row_numeric_map[column] = float(raw_value)

            row_numeric_map[unknown_load_key] = float(unknown_load)

            positive_values = [value for value in row_numeric_map.values() if value > 0]
            row_max_value = max(positive_values) if positive_values else None

            # Build normal meter cells
            for column in meter_columns:
                raw_value = row.get(column)

                cell_class = ""
                heat_class = ""
                is_row_max = False

                if isinstance(raw_value, (int, float)):
                    numeric_value = float(raw_value)

                    if numeric_value == 0:
                        cell_class = "value-zero"

                    if row_max_value is not None and numeric_value == row_max_value and numeric_value > 0:
                        is_row_max = True

                    if row_max_value is not None and row_max_value > 0 and numeric_value > 0:
                        ratio = numeric_value / row_max_value

                        if ratio >= 0.85:
                            heat_class = "heat-4"
                        elif ratio >= 0.60:
                            heat_class = "heat-3"
                        elif ratio >= 0.35:
                            heat_class = "heat-2"
                        elif ratio >= 0.15:
                            heat_class = "heat-1"

                meter_role = "main_feeder" if column in main_feeder_columns else "submeter"

                cells.append({
                    "key": column,
                    "raw_value": raw_value,
                    "display": self._fmt_or_dash(raw_value),
                    "cell_class": cell_class,
                    "heat_class": heat_class,
                    "is_row_max": is_row_max,
                    "meter_role": meter_role,
                })

            # Build unknown load cell as a normal meter-like cell
            unknown_cell_class = ""
            unknown_heat_class = ""
            unknown_is_row_max = False

            if unknown_load == 0:
                unknown_cell_class = "value-zero"

            if row_max_value is not None and unknown_load == row_max_value and unknown_load > 0:
                unknown_is_row_max = True

            if row_max_value is not None and row_max_value > 0 and unknown_load > 0:
                ratio = unknown_load / row_max_value

                if ratio >= 0.85:
                    unknown_heat_class = "heat-4"
                elif ratio >= 0.60:
                    unknown_heat_class = "heat-3"
                elif ratio >= 0.35:
                    unknown_heat_class = "heat-2"
                elif ratio >= 0.15:
                    unknown_heat_class = "heat-1"

            cells.append({
                "key": unknown_load_key,
                "raw_value": unknown_load,
                "display": self._fmt_or_dash(unknown_load),
                "cell_class": unknown_cell_class,
                "heat_class": unknown_heat_class,
                "is_row_max": unknown_is_row_max,
                "meter_role": "unknown",
            })

            daily_rows.append({
                "date": dt_value,
                "date_display": self._format_date_with_weekday(dt_value),
                "official_daily_total": official_daily_total_value,
                "main_feeder_total": main_feeder_total,
                "submeter_total": submeter_total,
                "unknown_load": unknown_load,
                "unknown_load_key": unknown_load_key,
                "cells": cells,
            })

        return {
            "area_key": area_key,
            "title": f"{area_key.upper()} Daily Energy Detail",
            "columns": columns,
            "rows": daily_rows,
            "meter_columns": meter_columns + [unknown_load_key],
            "main_feeder_columns": main_feeder_columns,
            "submeter_columns": submeter_columns,
            "exclude_from_top10": exclude_from_top10,
            "meter_count": len(meter_columns) + 1,
            "submeter_count": len(submeter_columns) + 1,
        }

    def build_energy_summary(
        self,
        area_tables: dict[str, dict[str, Any]],
        kpi_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Build per-area total summary using KPI summary as official source."""
        result: dict[str, Any] = {}

        kpi_areas = kpi_summary.get("areas", {})
        kpi_plant = kpi_summary.get("plant", {})

        for area_key, table in area_tables.items():
            official_total = (
                kpi_areas.get(area_key, {})
                .get("energy")
            )

            result[area_key] = {
                "total_energy": round(float(official_total), 4) if official_total is not None else None,
                "meter_count": table["meter_count"],
                "row_count": len(table["rows"]),
            }

        result["plant"] = {
            "total_energy": round(float(kpi_plant.get("total_energy")), 4)
            if kpi_plant.get("total_energy") is not None
            else None,
            "meter_count": 0,
            "row_count": max((len(table["rows"]) for table in area_tables.values()), default=0),
        }

        return result

    def build_energy_comparison(
        self,
        current_summary: dict[str, Any],
        previous_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Build energy summary comparison by area."""
        result: dict[str, Any] = {}

        for area_key in ["diode", "ico", "sakari"]:
            current_value = current_summary.get(area_key, {}).get("total_energy")
            previous_value = previous_summary.get(area_key, {}).get("total_energy")

            if current_value is None and previous_value is None:
                delta = None
                delta_pct = None
            else:
                curr = current_value or 0.0
                prev = previous_value or 0.0
                delta = curr - prev
                delta_pct = (delta / prev) if prev != 0 else None

            result[area_key] = {
                "current": current_value,
                "previous": previous_value,
                "delta": delta,
                "delta_pct": round(delta_pct, 4) if delta_pct is not None else None,
                "meter_count": current_summary.get(area_key, {}).get("meter_count", 0),
            }

        return result

    def build_top10_meters(
        self,
        area_tables: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build top 10 meters across three areas for current period."""
        meter_totals: list[dict[str, Any]] = []

        for area_key, table in area_tables.items():
            meter_totals.extend(
                self._sum_meter_totals_for_table(area_key, table)
            )

        meter_totals.sort(key=lambda item: item["current"], reverse=True)

        top10 = meter_totals[:10]

        for index, item in enumerate(top10, start=1):
            item["rank"] = index

        return top10

    def _sum_meter_totals_for_table(
        self,
        area_key: str,
        table: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Sum total energy per meter for one area table excluding configured feeders."""
        result: list[dict[str, Any]] = []

        excluded_columns = set(table.get("exclude_from_top10", []))

        valid_columns = [
            column
            for column in table.get("meter_columns", [])
            if column not in excluded_columns
        ]

        for column in valid_columns:
            total = 0.0

            for row in table["rows"]:
                for cell in row["cells"]:
                    if cell["key"] == column and isinstance(cell["raw_value"], (int, float)):
                        total += float(cell["raw_value"])

            result.append({
                "meter_name": column,
                "area": area_key.upper(),
                "current": round(total, 4),
            })

        return result

    def build_top10_comparison(
        self,
        current_top10: list[dict[str, Any]],
        previous_area_rows: dict[str, list[dict[str, Any]]],
        previous_kpi_summary: dict[str, Any],
        report_start: date,
        report_end: date,
    ) -> list[dict[str, Any]]:
        """Attach previous-period values to current top 10 meters."""
        previous_kpi_daily_lookup = self._build_kpi_daily_energy_lookup(
            kpi_summary=previous_kpi_summary,
            report_start=report_start,
            report_end=report_end,
        )

        previous_tables = {
            area: self.build_daily_energy_table(
                area_key=area,
                rows=self._filter_rows_in_period(rows, report_start, report_end),
                area_daily_energy_lookup={
                    dt_value: daily_item.get(area)
                    for dt_value, daily_item in previous_kpi_daily_lookup.items()
                },
            )
            for area, rows in previous_area_rows.items()
        }
        previous_lookup: dict[tuple[str, str], float] = {}

        for area_key, table in previous_tables.items():
            for item in self._sum_meter_totals_for_table(area_key, table):
                previous_lookup[(area_key.upper(), item["meter_name"])] = item["current"]

        result: list[dict[str, Any]] = []

        for item in current_top10:
            previous_value = previous_lookup.get((item["area"], item["meter_name"]), 0.0)
            current_value = item["current"]
            delta = current_value - previous_value
            delta_pct = (delta / previous_value) if previous_value != 0 else None

            result.append({
                "rank": item["rank"],
                "meter_name": item["meter_name"],
                "area": item["area"],
                "current": current_value,
                "previous": previous_value,
                "delta": round(delta, 4),
                "delta_pct": round(delta_pct, 4) if delta_pct is not None else None,
            })

        return result

    def build_daily_summary_rows(
        self,
        area_tables: dict[str, dict[str, Any]],
        kpi_daily_lookup: dict[date, dict[str, float | None]],
    ) -> list[dict[str, Any]]:
        """Build one daily energy summary table across all three areas."""
        rows_by_date: dict[date, list[tuple[str, float]]] = {}

        for table in area_tables.values():
            for row in table["rows"]:
                dt_value = row["date"]
                rows_by_date.setdefault(dt_value, [])

                for cell in row["cells"]:
                    raw_value = cell["raw_value"]
                    numeric_value = float(raw_value) if isinstance(raw_value, (int, float)) else 0.0
                    rows_by_date[dt_value].append((cell["key"], numeric_value))

        result: list[dict[str, Any]] = []

        for dt_value in sorted(rows_by_date.keys()):
            meter_values = rows_by_date[dt_value]

            plant_daily_total = (
                kpi_daily_lookup.get(dt_value, {}).get("plant_total_energy")
            )
            plant_daily_total_value = (
                float(plant_daily_total) if plant_daily_total is not None else 0.0
            )

            total_meter_count = len(meter_values)

            active_values = [(name, value) for name, value in meter_values if value > 0]
            active_meter_count = len(active_values)
            inactive_meter_count = total_meter_count - active_meter_count

            if active_values:
                top_meter_name, top_meter_value = max(active_values, key=lambda item: item[1])
            else:
                top_meter_name = "-"
                top_meter_value = 0.0

            average_per_active = (
                plant_daily_total_value / active_meter_count
                if active_meter_count > 0 else 0.0
            )

            top_1_pct = None
            if plant_daily_total_value > 0 and top_meter_value > 0:
                top_1_pct = top_meter_value / plant_daily_total_value

            result.append({
                "date": dt_value,
                "date_display": self._format_date_with_weekday(dt_value),
                "total_energy_display": self._fmt(plant_daily_total_value),
                "top_1_meter": top_meter_name,
                "top_1_value_display": self._fmt(top_meter_value),
                "top_1_pct_display": self._fmt_pct(top_1_pct) if top_1_pct is not None else None,
                "active_meter_count": active_meter_count,
                "average_per_active_display": self._fmt(average_per_active),
                "total_meter_count": total_meter_count,
                "inactive_meter_count": inactive_meter_count,
                "avg_per_active_display": self._fmt(average_per_active),
            })

        return result

    def _filter_rows_in_period(
        self,
        rows: list[dict[str, Any]],
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Filter rows within date range."""
        result = []

        for row in rows:
            dt_value = self._to_date(row.get("dt"))
            if dt_value is not None and start_date <= dt_value <= end_date:
                result.append(row)

        return result

    def _to_date(self, value: Any) -> date | None:
        """Convert a value to date."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return None

    def _fmt(self, value: Any) -> str:
        """Format numeric value."""
        if value is None:
            return "-"
        return f"{float(value):,.2f}"

    def _fmt_or_dash(self, value: Any) -> str:
        """Format number or return dash."""
        if value is None:
            return "-"
        return f"{float(value):,.2f}"

    def _format_date_with_weekday(self, value: date | None) -> str:
        """Format date with weekday."""
        if value is None:
            return "-"
        return f"{value.isoformat()} ({value.strftime('%a')})"

    def _fmt_pct(self, val):
        """Format ratio to percent display."""
        if val is None:
            return "-"
        return f"{float(val) * 100:.2f}%"

    def _build_kpi_daily_energy_lookup(
        self,
        kpi_summary: dict[str, Any],
        report_start: date,
        report_end: date,
    ) -> dict[date, dict[str, float | None]]:
        """Build a simple daily KPI energy lookup using period average as proxy."""
        plant_total = kpi_summary.get("plant", {}).get("total_energy")

        area_totals = {
            "diode": kpi_summary.get("areas", {}).get("diode", {}).get("energy"),
            "ico": kpi_summary.get("areas", {}).get("ico", {}).get("energy"),
            "sakari": kpi_summary.get("areas", {}).get("sakari", {}).get("energy"),
        }

        total_days = (report_end - report_start).days + 1
        if total_days <= 0:
            return {}

        plant_daily = (float(plant_total) / total_days) if plant_total is not None else None

        area_daily = {
            area_key: (float(total_value) / total_days) if total_value is not None else None
            for area_key, total_value in area_totals.items()
        }

        result: dict[date, dict[str, float | None]] = {}

        current_day = report_start
        while current_day <= report_end:
            result[current_day] = {
                "plant_total_energy": plant_daily,
                "diode": area_daily["diode"],
                "ico": area_daily["ico"],
                "sakari": area_daily["sakari"],
            }
            current_day = current_day.fromordinal(current_day.toordinal() + 1)

        return result