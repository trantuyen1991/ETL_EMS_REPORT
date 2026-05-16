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
        current_area_columns: dict[str, list[str]],
        previous_area_columns: dict[str, list[str]],
        current_total_energy_rows: list[dict[str, Any]],
        previous_total_energy_rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
        previous_start: date,
        previous_end: date,
    ) -> dict[str, Any]:
        """Build full energy object for V2 report."""
        current_obj = self.build_energy_report_object(
            area_rows=current_area_rows,
            area_columns=current_area_columns,
            total_energy_rows=current_total_energy_rows,
            report_start=report_start,
            report_end=report_end,
        )

        previous_obj = self.build_energy_report_object(
            area_rows=previous_area_rows,
            area_columns=previous_area_columns,
            total_energy_rows=previous_total_energy_rows,
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
                previous_total_energy_rows=previous_total_energy_rows,
                area_columns=current_area_columns,
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
        area_columns: dict[str, list[str]],
        total_energy_rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> dict[str, Any]:
        """Build one period energy object."""
        metadata = get_energy_area_metadata()
        filtered_area_rows = {
            area: self._filter_rows_in_period(rows, report_start, report_end)
            for area, rows in area_rows.items()
        }

        daily_energy_lookup = self._build_total_energy_daily_lookup_from_rows(
            total_energy_rows=total_energy_rows,
            report_start=report_start,
            report_end=report_end,
        )
        period_official_summary = self._build_total_energy_period_summary_from_rows(
            total_energy_rows=total_energy_rows,
        )

        period_days = sorted(daily_energy_lookup.keys())

        area_tables = {
            area: self.build_daily_energy_table(
                area_key=area,
                rows=rows,
                area_daily_energy_lookup={
                    dt_value: daily_item.get(area)
                    for dt_value, daily_item in daily_energy_lookup.items()
                },
                period_days=period_days,
                meter_columns=area_columns.get(area, []),
            )
            for area, rows in filtered_area_rows.items()
        }

        return {
            "summary": self.build_energy_summary(
                area_tables=area_tables,
                official_summary=period_official_summary,
            ),
            "top10_meters": self.build_top10_meters(area_tables),
            "daily_summary_rows": self.build_daily_summary_rows(
                area_tables=area_tables,
                daily_energy_lookup=daily_energy_lookup,
            ),
            "daily_tables": [
                area_tables["diode"],
                area_tables["ico"],
                area_tables["sakari"],
            ],
            "anomalies": self._build_energy_anomalies(
                area_tables=area_tables,
                official_summary=period_official_summary,
                metadata=metadata,
            ),
        }

    def _build_total_energy_daily_lookup_from_rows(
        self,
        total_energy_rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> dict[date, dict[str, float | None]]:
        """Build dense daily official energy lookup from total_energy view rows."""
        result: dict[date, dict[str, float | None]] = {}

        current_day = report_start
        while current_day <= report_end:
            result[current_day] = {
                "plant_total_energy": None,
                "diode": None,
                "ico": None,
                "sakari": None,
            }
            current_day = current_day.fromordinal(current_day.toordinal() + 1)

        for row in total_energy_rows:
            dt_value = self._to_date(row.get("dt"))
            if dt_value is None or dt_value not in result:
                continue

            result[dt_value] = {
                "plant_total_energy": float(row.get("Total_engy")) if row.get("Total_engy") is not None else None,
                "diode": float(row.get("DIODE_engy")) if row.get("DIODE_engy") is not None else None,
                "ico": float(row.get("ICO_engy")) if row.get("ICO_engy") is not None else None,
                "sakari": float(row.get("SAKARI_engy")) if row.get("SAKARI_engy") is not None else None,
            }

        return result

    def _build_total_energy_period_summary_from_rows(
        self,
        total_energy_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build period official totals for Electric from total_energy view rows."""
        plant_total = 0.0
        area_totals = {
            "diode": 0.0,
            "ico": 0.0,
            "sakari": 0.0,
        }
        plant_has_value = False
        area_has_value = {"diode": False, "ico": False, "sakari": False}

        for row in total_energy_rows:
            if row.get("Total_engy") is not None:
                plant_total += float(row.get("Total_engy"))
                plant_has_value = True
            if row.get("DIODE_engy") is not None:
                area_totals["diode"] += float(row.get("DIODE_engy"))
                area_has_value["diode"] = True
            if row.get("ICO_engy") is not None:
                area_totals["ico"] += float(row.get("ICO_engy"))
                area_has_value["ico"] = True
            if row.get("SAKARI_engy") is not None:
                area_totals["sakari"] += float(row.get("SAKARI_engy"))
                area_has_value["sakari"] = True

        return {
            "plant": {
                "total_energy": plant_total if plant_has_value else None,
            },
            "areas": {
                "diode": {"energy": area_totals["diode"] if area_has_value["diode"] else None},
                "ico": {"energy": area_totals["ico"] if area_has_value["ico"] else None},
                "sakari": {"energy": area_totals["sakari"] if area_has_value["sakari"] else None},
            },
        }

    def _build_energy_anomalies(
        self,
        area_tables: dict[str, dict[str, Any]],
        official_summary: dict[str, Any],
        metadata: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build anomaly rows for electricity analysis with topology-aware logic.

        Args:
            area_tables: Daily energy tables per area.
            official_summary: Electric official summary built from total_energy view.
            metadata: Area metadata configuration.

        Returns:
            List of anomaly records.
        """
        anomalies: list[dict[str, Any]] = []

        for area_key, table in area_tables.items():
            area_meta = metadata.get(area_key, {})
            downstream_areas = area_meta.get("downstream_areas", [])

            for row in table.get("rows", []):
                dt_value = row.get("date")

                official_daily_total = float(row.get("official_daily_total") or 0.0)
                main_feeder_total = float(row.get("main_feeder_total") or 0.0)
                submeter_total = float(row.get("submeter_total") or 0.0)
                unknown_load = float(row.get("unknown_load") or 0.0)

                # =========================
                # Ratio calculations
                # =========================
                unknown_ratio = (
                    unknown_load / official_daily_total
                    if official_daily_total > 0 else None
                )

                feeder_gap = main_feeder_total - official_daily_total
                feeder_gap_ratio = (
                    feeder_gap / official_daily_total
                    if official_daily_total > 0 else None
                )

                # =========================
                # Rule 1: Negative unknown
                # =========================
                if unknown_load < 0:
                    anomalies.append({
                        "area_key": area_key,
                        "date": dt_value,
                        "date_display": self._format_date_with_weekday(dt_value),
                        "rule_code": "NEGATIVE_UNKNOWN_LOAD",
                        "severity": "warning",
                        "official_daily_total": official_daily_total,
                        "main_feeder_total": main_feeder_total,
                        "submeter_total": submeter_total,
                        "unknown_load": unknown_load,
                        "unknown_ratio": round(unknown_ratio, 4) if unknown_ratio is not None else None,
                        "message": "Unknown load is negative. Submeter total exceeds official total.",
                    })

                # =========================
                # Rule 2: High unknown load
                # =========================
                if unknown_ratio is not None:
                    if unknown_ratio > 0.5:
                        severity = "critical"
                    elif unknown_ratio > 0.3:
                        severity = "warning"
                    else:
                        severity = None

                    if severity:
                        anomalies.append({
                            "area_key": area_key,
                            "date": dt_value,
                            "date_display": self._format_date_with_weekday(dt_value),
                            "rule_code": "HIGH_UNKNOWN_LOAD",
                            "severity": severity,
                            "official_daily_total": official_daily_total,
                            "main_feeder_total": main_feeder_total,
                            "submeter_total": submeter_total,
                            "unknown_load": unknown_load,
                            "unknown_ratio": round(unknown_ratio, 4),
                            "message": "Unknown load exceeds acceptable threshold.",
                        })

                # =========================
                # Rule 3: Feeder vs official gap
                # =========================
                if feeder_gap_ratio is not None and abs(feeder_gap_ratio) > 0.20:

                    # Calculate expected gap from downstream areas
                    expected_gap = 0.0
                    for child_area in downstream_areas:
                        child_total = (
                            official_summary.get("areas", {})
                            .get(child_area, {})
                            .get("energy")
                        )
                        if child_total:
                            expected_gap += float(child_total)

                    gap_diff = abs(feeder_gap - expected_gap)

                    is_expected_topology = (
                        downstream_areas
                        and expected_gap > 0
                        and gap_diff / expected_gap < 0.05  # tolerance 5%
                    )

                    if is_expected_topology:
                        rule_code = "FEEDER_TOPOLOGY_FLOW"
                        severity = "info"
                        message = "Feeder supplies downstream area(s), gap is expected."
                    else:
                        rule_code = "FEEDER_OFFICIAL_GAP"
                        severity = "warning"
                        message = "Main feeder total differs significantly from official total."

                    anomalies.append({
                        "area_key": area_key,
                        "date": dt_value,
                        "date_display": self._format_date_with_weekday(dt_value),
                        "rule_code": rule_code,
                        "severity": severity,
                        "official_daily_total": official_daily_total,
                        "main_feeder_total": main_feeder_total,
                        "submeter_total": submeter_total,
                        "unknown_load": unknown_load,
                        "feeder_gap": round(feeder_gap, 4),
                        "feeder_gap_ratio": round(feeder_gap_ratio, 4),
                        "expected_gap": round(expected_gap, 4),
                        "message": message,
                    })

        return anomalies
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
        meter_columns: list[str],
        area_daily_energy_lookup: dict[date, float | None],
        period_days: list[date],
    ) -> dict[str, Any]:
        """Build one dynamic daily energy table with dense daily rows."""
        area_metadata = get_energy_area_metadata()
        area_meta = area_metadata.get(area_key, {})

        main_feeder_columns = list(area_meta.get("main_feeders", []))
        exclude_from_top10 = list(area_meta.get("exclude_from_top10", []))
        exclude_from_detail = list(area_meta.get("exclude_from_detail", []))
        unknown_load_key = area_meta.get("unknown_load_key", "unknown_load")
        unknown_load_display_name = area_meta.get("unknown_load_display_name", "Unknown Load")

        raw_meter_columns = meter_columns

        base_meter_columns = [
            column
            for column in raw_meter_columns
            if column not in exclude_from_detail
        ]

        submeter_columns = [
            column
            for column in base_meter_columns
             if column not in exclude_from_top10
        ]

        columns = [{"key": "dt", "display_name": "Date", "is_date": True}]

        for column in base_meter_columns:
            meter_role = "main_feeder" if column in main_feeder_columns else "submeter"
            columns.append({
                "key": column,
                "display_name": column,
                "is_date": False,
                "meter_role": meter_role,
            })

        columns.append({
            "key": unknown_load_key,
            "display_name": unknown_load_display_name,
            "is_date": False,
            "meter_role": "unknown",
        })

        rows_by_date = {
            self._to_date(row.get("dt")): row
            for row in rows
            if self._to_date(row.get("dt")) is not None
        }

        daily_rows: list[dict[str, Any]] = []

        for dt_value in period_days:
            source_row = rows_by_date.get(dt_value, {})

            cells: list[dict[str, Any]] = []
            main_feeder_total = 0.0
            submeter_total = 0.0
            has_any_raw_data = False

            for column in meter_columns:
                raw_value = source_row.get(column)

                if isinstance(raw_value, (int, float)):
                    value = float(raw_value)
                    has_any_raw_data = True

                    if column in main_feeder_columns:
                        main_feeder_total += value
                    elif column in submeter_columns:
                        submeter_total += value

            official_daily_total = area_daily_energy_lookup.get(dt_value)
            official_daily_total_value = (
                float(official_daily_total) if official_daily_total is not None else None
            )

            if official_daily_total_value is None and not has_any_raw_data:
                unknown_load = None
            else:
                unknown_load = (official_daily_total_value or 0.0) - submeter_total

            row_numeric_map: dict[str, float] = {}

            for column in base_meter_columns:
                raw_value = source_row.get(column)
                if isinstance(raw_value, (int, float)):
                    row_numeric_map[column] = float(raw_value)

            if unknown_load is not None:
                row_numeric_map[unknown_load_key] = float(unknown_load)

            positive_values = [value for value in row_numeric_map.values() if value > 0]
            row_max_value = max(positive_values) if positive_values else None
            ranked_positive_values = sorted(set(positive_values), reverse=True)

            def _build_cell_visual_meta(raw_numeric_value: Any) -> dict[str, Any]:
                cell_class = ""
                heat_class = ""
                is_row_max = False
                fill_pct = 0.0
                rank_class = "rank-none"
                rank_order = None

                if not isinstance(raw_numeric_value, (int, float)):
                    return {
                        "cell_class": cell_class,
                        "heat_class": heat_class,
                        "is_row_max": is_row_max,
                        "fill_pct": fill_pct,
                        "rank_class": rank_class,
                        "rank_order": rank_order,
                    }

                numeric_value = float(raw_numeric_value)

                if numeric_value == 0:
                    cell_class = "value-zero"
                    rank_class = "rank-zero"
                    return {
                        "cell_class": cell_class,
                        "heat_class": heat_class,
                        "is_row_max": is_row_max,
                        "fill_pct": fill_pct,
                        "rank_class": rank_class,
                        "rank_order": rank_order,
                    }

                if row_max_value is not None and numeric_value == row_max_value and numeric_value > 0:
                    is_row_max = True

                if row_max_value is not None and row_max_value > 0 and numeric_value > 0:
                    ratio = numeric_value / row_max_value
                    fill_pct = max(4.0, min(100.0, ratio * 100.0))

                    if ratio >= 0.85:
                        heat_class = "heat-4"
                    elif ratio >= 0.60:
                        heat_class = "heat-3"
                    elif ratio >= 0.35:
                        heat_class = "heat-2"
                    elif ratio >= 0.15:
                        heat_class = "heat-1"

                    try:
                        rank_order = ranked_positive_values.index(numeric_value) + 1
                    except ValueError:
                        rank_order = None

                    if rank_order == 1:
                        rank_class = "rank-top"
                    elif rank_order is not None and rank_order <= 3:
                        rank_class = "rank-high"
                    elif ratio >= 0.45:
                        rank_class = "rank-mid"
                    elif ratio >= 0.18:
                        rank_class = "rank-low"
                    else:
                        rank_class = "rank-minor"

                return {
                    "cell_class": cell_class,
                    "heat_class": heat_class,
                    "is_row_max": is_row_max,
                    "fill_pct": round(fill_pct, 2),
                    "rank_class": rank_class,
                    "rank_order": rank_order,
                }

            for column in base_meter_columns:
                raw_value = source_row.get(column)
                visual_meta = _build_cell_visual_meta(raw_value)
                meter_role = "main_feeder" if column in main_feeder_columns else "submeter"

                cells.append({
                    "key": column,
                    "raw_value": raw_value,
                    "display": self._fmt_or_dash(raw_value),
                    "cell_class": visual_meta["cell_class"],
                    "heat_class": visual_meta["heat_class"],
                    "is_row_max": visual_meta["is_row_max"],
                    "fill_pct": visual_meta["fill_pct"],
                    "rank_class": visual_meta["rank_class"],
                    "rank_order": visual_meta["rank_order"],
                    "meter_role": meter_role,
                })

            unknown_visual_meta = _build_cell_visual_meta(unknown_load)

            cells.append({
                "key": unknown_load_key,
                "raw_value": unknown_load,
                "display": self._fmt_or_dash(unknown_load),
                "cell_class": unknown_visual_meta["cell_class"],
                "heat_class": unknown_visual_meta["heat_class"],
                "is_row_max": unknown_visual_meta["is_row_max"],
                "fill_pct": unknown_visual_meta["fill_pct"],
                "rank_class": unknown_visual_meta["rank_class"],
                "rank_order": unknown_visual_meta["rank_order"],
                "meter_role": "unknown",
            })

            daily_rows.append({
                "date": dt_value,
                "date_display": self._format_date_with_weekday(dt_value),
                "official_daily_total": official_daily_total_value,
                "main_feeder_total": main_feeder_total if has_any_raw_data else None,
                "submeter_total": submeter_total if has_any_raw_data else None,
                "unknown_load": unknown_load,
                "unknown_load_key": unknown_load_key,
                "cells": cells,
            })

        table_positive_values: list[float] = []
        for row in daily_rows:
            for cell in row.get("cells", []):
                raw_value = cell.get("raw_value")
                if not isinstance(raw_value, (int, float)):
                    continue
                numeric_value = float(raw_value)
                if numeric_value <= 0:
                    continue
                table_positive_values.append(numeric_value)

        table_max_value = max(table_positive_values) if table_positive_values else None
        table_ranked_values = sorted(set(table_positive_values), reverse=True)

        def _build_period_table_visual_meta(raw_numeric_value: Any) -> dict[str, Any]:
            cell_class = ""
            heat_class = ""
            is_table_max = False
            fill_pct = 0.0
            rank_class = "rank-none"
            rank_order = None

            if not isinstance(raw_numeric_value, (int, float)):
                return {
                    "cell_class": cell_class,
                    "heat_class": heat_class,
                    "is_table_max": is_table_max,
                    "fill_pct": fill_pct,
                    "rank_class": rank_class,
                    "rank_order": rank_order,
                }

            numeric_value = float(raw_numeric_value)
            if numeric_value == 0:
                cell_class = "value-zero"
                rank_class = "rank-zero"
                return {
                    "cell_class": cell_class,
                    "heat_class": heat_class,
                    "is_table_max": is_table_max,
                    "fill_pct": fill_pct,
                    "rank_class": rank_class,
                    "rank_order": rank_order,
                }

            if table_max_value is not None and numeric_value == table_max_value and numeric_value > 0:
                is_table_max = True

            if table_max_value is not None and table_max_value > 0 and numeric_value > 0:
                ratio = numeric_value / table_max_value
                fill_pct = min(100.0, ratio * 100.0)
                if 0 < fill_pct < 2.0:
                    fill_pct = 2.0

                if ratio >= 0.80:
                    heat_class = "heat-4"
                elif ratio >= 0.55:
                    heat_class = "heat-3"
                elif ratio >= 0.25:
                    heat_class = "heat-2"
                elif ratio >= 0.10:
                    heat_class = "heat-1"

                try:
                    rank_order = table_ranked_values.index(numeric_value) + 1
                except ValueError:
                    rank_order = None

                if rank_order == 1:
                    rank_class = "rank-top"
                elif rank_order is not None and rank_order <= 3:
                    rank_class = "rank-high"
                elif ratio >= 0.45:
                    rank_class = "rank-mid"
                elif ratio >= 0.15:
                    rank_class = "rank-low"
                else:
                    rank_class = "rank-minor"

            return {
                "cell_class": cell_class,
                "heat_class": heat_class,
                "is_table_max": is_table_max,
                "fill_pct": round(fill_pct, 2),
                "rank_class": rank_class,
                "rank_order": rank_order,
            }

        for row in daily_rows:
            for cell in row.get("cells", []):
                period_visual_meta = _build_period_table_visual_meta(
                    cell.get("raw_value"),
                )
                cell["period_cell_class"] = period_visual_meta["cell_class"]
                cell["period_heat_class"] = period_visual_meta["heat_class"]
                cell["period_is_table_max"] = period_visual_meta["is_table_max"]
                cell["period_fill_pct"] = period_visual_meta["fill_pct"]
                cell["period_rank_class"] = period_visual_meta["rank_class"]
                cell["period_rank_order"] = period_visual_meta["rank_order"]

        area_display_name = str(area_meta.get("display_name") or area_key.upper())

        return {
            "area_key": area_key,
            "title": f"{area_display_name} Daily Energy Detail",
            "columns": columns,
            "rows": daily_rows,
            "meter_columns": base_meter_columns + [unknown_load_key],
            "main_feeder_columns": main_feeder_columns,
            "submeter_columns": submeter_columns,
            "exclude_from_top10": exclude_from_top10,
            "exclude_from_detail": exclude_from_detail,
            "meter_count": len(base_meter_columns) + 1,
            "submeter_count": len(submeter_columns) + 1,
        }

    def build_energy_summary(
        self,
        area_tables: dict[str, dict[str, Any]],
        official_summary: dict[str, Any],
    ) -> dict[str, Any]:
        """Build per-area summary with feeder/submeter/unknown breakdown."""
        result: dict[str, Any] = {}

        official_areas = official_summary.get("areas", {})
        official_plant = official_summary.get("plant", {})

        plant_main_feeder_total = 0.0
        plant_submeter_total = 0.0
        plant_unknown_total = 0.0

        for area_key, table in area_tables.items():
            official_total = (
                official_areas.get(area_key, {})
                .get("energy")
            )

            main_feeder_total = sum(
                float(row.get("main_feeder_total") or 0.0)
                for row in table["rows"]
            )

            submeter_total = sum(
                float(row.get("submeter_total") or 0.0)
                for row in table["rows"]
            )

            unknown_total = sum(
                float(row.get("unknown_load") or 0.0)
                for row in table["rows"]
            )

            plant_main_feeder_total += main_feeder_total
            plant_submeter_total += submeter_total
            plant_unknown_total += unknown_total

            result[area_key] = {
                "total_energy": round(float(official_total), 4) if official_total is not None else None,
                "main_feeder_total": round(main_feeder_total, 4),
                "submeter_total": round(submeter_total, 4),
                "unknown_load_total": round(unknown_total, 4),
                "meter_count": table["meter_count"],
                "submeter_count": table["submeter_count"],
                "row_count": len(table["rows"]),
            }

        result["plant"] = {
            "total_energy": round(float(official_plant.get("total_energy")), 4)
            if official_plant.get("total_energy") is not None else None,
            "main_feeder_total": round(plant_main_feeder_total, 4),
            "submeter_total": round(plant_submeter_total, 4),
            "unknown_load_total": round(plant_unknown_total, 4),
            "meter_count": 0,
            "submeter_count": 0,
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
            has_numeric_data = False

            for row in table["rows"]:
                for cell in row["cells"]:
                    if cell["key"] == column and isinstance(cell["raw_value"], (int, float)):
                        total += float(cell["raw_value"])
                        has_numeric_data = True

            if not has_numeric_data:
                continue

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
        previous_total_energy_rows: list[dict[str, Any]],
        area_columns: dict[str, list[str]],
        report_start: date,
        report_end: date,
    ) -> list[dict[str, Any]]:
        """Attach previous-period values to current top 10 meters."""
        previous_daily_lookup = self._build_total_energy_daily_lookup_from_rows(
            total_energy_rows=previous_total_energy_rows,
            report_start=report_start,
            report_end=report_end,
        )

        period_days = sorted(previous_daily_lookup.keys())

        previous_tables = {
            area: self.build_daily_energy_table(
                area_key=area,
                rows=self._filter_rows_in_period(rows, report_start, report_end),
                area_daily_energy_lookup={
                    dt_value: daily_item.get(area)
                    for dt_value, daily_item in previous_daily_lookup.items()
                },
                period_days=period_days,
                meter_columns=area_columns.get(area, []),
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
        daily_energy_lookup: dict[date, dict[str, float | None]],
    ) -> list[dict[str, Any]]:
        """Build one daily energy summary table across all three areas."""
        rows_by_date: dict[date, list[tuple[str, float]]] = {}

        for table in area_tables.values():
            main_feeder_columns = set(table.get("exclude_from_top10", []))

            for row in table["rows"]:
                dt_value = row["date"]
                rows_by_date.setdefault(dt_value, [])

                for cell in row["cells"]:
                    cell_key = cell.get("key")
                    meter_role = cell.get("meter_role")

                    # Exclude main feeders from top-1 daily meter logic
                    if meter_role == "main_feeder" or cell_key in main_feeder_columns:
                        continue

                    raw_value = cell["raw_value"]
                    numeric_value = float(raw_value) if isinstance(raw_value, (int, float)) else 0.0
                    rows_by_date[dt_value].append((cell_key, numeric_value))

        result: list[dict[str, Any]] = []

        for dt_value in sorted(rows_by_date.keys()):
            meter_values = rows_by_date[dt_value]

            plant_daily_total = (
                daily_energy_lookup.get(dt_value, {}).get("plant_total_energy")
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