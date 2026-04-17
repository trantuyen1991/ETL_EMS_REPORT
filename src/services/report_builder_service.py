# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportBuilderService:
    """Service to assemble full report context (V2)."""

    def build_report_context(
        self,
        *,
        meta: Dict[str, Any],
        period: Dict[str, Any],
        energy_object: Dict[str, Any] | None,
        kpi_object: Dict[str, Any] | None,
        utility_object: Dict[str, Any] | None,
    ) -> Dict[str, Any]:

        flags = self._build_flags(kpi_object, utility_object)

        summary = self._build_summary(
            kpi_object=kpi_object,
            utility_object=utility_object,
        )

        sections = {
            "kpi": self._build_kpi_section(kpi_object),
            "utility": self._build_utility_section(utility_object),
        }

        notes = self._build_notes(kpi_object, utility_object)

        context = {
            "meta": meta,
            "period": period,
            "flags": flags,
            "summary": summary,
            "sections": sections,
            "notes": notes,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "v2",
        }

        logger.info("Report context V2 built successfully")

        return context

    def _build_flags(self, kpi_object, utility_object) -> dict:
        """Build UI flags."""

        has_kpi = bool(kpi_object)
        has_utility = bool(utility_object)

        has_coverage_warning = False

        if kpi_object:
            cov = kpi_object["current"]["coverage"]
            if not cov["is_full_coverage"]:
                has_coverage_warning = True

        return {
            "has_kpi_section": has_kpi,
            "has_utility_section": has_utility,
            "has_daily_detail": True,
            "has_coverage_warning": has_coverage_warning,
        }

    def _build_kpi_snapshot(self, kpi_object) -> dict:
        comp = kpi_object["comparison"]["plant"]

        return {
            "current_display": self._fmt(comp["current"]),
            "previous_display": self._fmt(comp["previous"]),
            "delta_display": self._fmt(comp["delta"]),
            "delta_pct_display": self._fmt_pct(comp["delta_pct"]),
            "delta_class": self._trend_class(comp["delta"]),
            "delta_pct_class": self._trend_class(comp["delta_pct"]),
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
                "delta_class": self._trend_class(comp.get("delta")),
                "delta_pct_class": self._trend_class(comp.get("delta_pct")),
            })

        return result

    def _build_summary(self, kpi_object, utility_object) -> dict:
        return {
            "kpi_snapshot": self._build_kpi_snapshot(kpi_object),
            "kpi_area_snapshot_rows": self._build_kpi_area_snapshot_rows(kpi_object),
            "utility_snapshot_rows": self._build_utility_snapshot(utility_object),
            "coverage": self._build_global_coverage(kpi_object),
        }

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

    def _build_kpi_section(self, kpi_object) -> dict:
        """Build KPI section for report rendering."""
        curr = kpi_object["current"]
        comp = kpi_object["comparison"]

        plant = comp["plant"]

        return {
            "title": "KPI Performance",
            "subtitle": "Current period versus previous period comparison.",
            "coverage": {
                "coverage_display": f"{curr['coverage']['coverage_days']}/{curr['coverage']['report_total_days']}",
                "coverage_note": self._map_kpi_coverage_note(curr["coverage"].get("coverage_note")),
                "uncovered_ranges": self._build_kpi_uncovered_ranges(
                    curr["coverage"].get("uncovered_ranges", [])
                ),
                "is_complete": curr["coverage"]["is_full_coverage"],
            },
            "plant_summary": {
                "level_name": "Plant",
                "current_display": self._fmt(plant["current"]),
                "previous_display": self._fmt(plant["previous"]),
                "delta_display": self._fmt(plant["delta"]),
                "delta_pct_display": self._fmt_pct(plant["delta_pct"]),
                "delta_class": self._trend_class(plant["delta"]),
                "delta_pct_class": self._trend_class(plant["delta_pct"]),
                "coverage_display": f"{curr['coverage']['coverage_days']}/{curr['coverage']['report_total_days']}",
            },
            "area_rows": self._build_kpi_area_rows(comp["areas"]),
            "daily_rows": self._build_kpi_daily_rows(kpi_object),
        }

    def _build_kpi_area_rows(self, areas: dict) -> list:
        rows = []

        for area, val in areas.items():
            rows.append({
                "area_name": area.upper(),
                "current_display": self._fmt(val["current"]),
                "previous_display": self._fmt(val["previous"]),
                "delta_display": self._fmt(val["delta"]),
                "delta_pct_display": self._fmt_pct(val["delta_pct"]),
                "delta_class": self._trend_class(val["delta"]),
                "delta_pct_class": self._trend_class(val["delta_pct"]),
                "coverage_note": "",
            })

        return rows

    def _build_utility_section(self, utility_object) -> dict:
        coverage = self._build_utility_coverage(utility_object)

        return {
            "title": "Utility Consumption",
            "coverage": coverage,
            "summary_rows": self._build_utility_snapshot(utility_object),
            "daily_columns": self._build_daily_columns(utility_object),
            "daily_rows": self._build_daily_rows(utility_object),
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
                "date_display": str(row["dt"]),
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
                "delta_class": self._trend_class(area_obj.get("delta")),
                "delta_pct_class": self._trend_class(area_obj.get("delta_pct")),
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
                "date_display": str(row.get("dt")),
                "time_frame_source": row.get("time_frame_source"),
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