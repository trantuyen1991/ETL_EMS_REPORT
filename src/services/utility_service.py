# -*- coding: utf-8 -*-
"""
Utility service for aggregating utility usage data for reporting.

This module prepares utility data from the utility_usage source.

Important:
- Utility columns may have different physical units
- The service does not compute one grand total across different utilities
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from src.config.utility_metadata import (
    get_utility_metadata,
    get_utility_sensor_group_labels,
    get_utility_sensor_group_order,
    get_utility_sensor_metadata,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UtilityService:
    """Service for utility usage aggregation."""

    def build_utility_report_object(
        self,
        rows: List[Dict[str, Any]],
        report_start: date,
        report_end: date,
        sensor_monitoring: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Build full utility object for report usage.

        Args:
            rows: Raw rows fetched from utility source.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            dict: Utility report object with metadata, summary, and timeseries.

        Example:
            result = service.build_utility_report_object(rows, start, end)
        """
        filtered_rows = self._filter_rows_in_period(rows, report_start, report_end)
        metadata = get_utility_metadata()
        utility_columns = list(metadata.keys())

        timeseries = self._build_timeseries(
            rows=filtered_rows,
            utility_columns=utility_columns,
            report_start=report_start,
            report_end=report_end,
        )

        summary = self._build_summary(
            timeseries=timeseries,
            metadata=metadata,
        )

        return {
            "metadata": metadata,
            "summary": summary,
            "timeseries": timeseries,
            "sensor_monitoring": sensor_monitoring or {
                "enabled": False,
                "metric_columns": [],
                "daily_rows": [],
            },
        }

    def build_utility_comparison(
        self,
        current_summary: dict,
        previous_summary: dict,
    ) -> dict:
        """
        Build comparison between current and previous utility summaries.

        Args:
            current_summary: Current period utility summary.
            previous_summary: Previous period utility summary.

        Returns:
            dict: Comparison per utility metric including delta and delta_pct.
        """

        comparison: dict = {}

        all_keys = set(current_summary.keys()) | set(previous_summary.keys())

        for key in all_keys:
            curr_obj = current_summary.get(key)
            prev_obj = previous_summary.get(key)

            curr = curr_obj["total"] if curr_obj else None
            prev = prev_obj["total"] if prev_obj else None

            if curr is None and prev is None:
                delta = None
                delta_pct = None
            else:
                curr_val = curr or 0.0
                prev_val = prev or 0.0

                delta = curr_val - prev_val

                if prev_val != 0:
                    delta_pct = round(delta / prev_val, 4)
                else:
                    delta_pct = None

            comparison[key] = {
                "current": curr,
                "previous": prev,
                "delta": delta,
                "delta_pct": delta_pct,
            }

        return comparison

    def build_full_utility_object(
        self,
        current_rows: list[dict],
        previous_rows: list[dict],
        report_start,
        report_end,
        previous_start,
        previous_end,
        current_sensor_monitoring: Dict[str, Any] | None = None,
        previous_sensor_monitoring: Dict[str, Any] | None = None,
    ) -> dict:
        """
        Build full utility object including current, previous and comparison.

        Args:
            current_rows: Raw rows for current period.
            previous_rows: Raw rows for previous period.
            report_start: Current period start date.
            report_end: Current period end date.
            previous_start: Previous period start date.
            previous_end: Previous period end date.

        Returns:
            dict: Full utility object.
        """
        current_obj = self.build_utility_report_object(
            rows=current_rows,
            report_start=report_start,
            report_end=report_end,
            sensor_monitoring=current_sensor_monitoring,
        )

        previous_obj = self.build_utility_report_object(
            rows=previous_rows,
            report_start=previous_start,
            report_end=previous_end,
            sensor_monitoring=previous_sensor_monitoring,
        )

        comparison = self.build_utility_comparison(
            current_summary=current_obj["summary"],
            previous_summary=previous_obj["summary"],
        )

        return {
            "current": current_obj,
            "previous": previous_obj,
            "comparison": comparison,
        }

    def _filter_rows_in_period(
        self,
        rows: List[Dict[str, Any]],
        start: date,
        end: date,
    ) -> List[Dict[str, Any]]:
        """Filter rows within report period."""
        result: List[Dict[str, Any]] = []

        for row in rows:
            dt = self._to_date(row.get("dt"))
            if dt is not None and start <= dt <= end:
                result.append(row)

        return result

    def _build_timeseries(
        self,
        rows: List[Dict[str, Any]],
        utility_columns: List[str],
        report_start: date,
        report_end: date,
    ) -> List[Dict[str, Any]]:
        """Build dense daily timeseries preserving each utility column.

        Args:
            rows: Filtered raw rows in period.
            utility_columns: Ordered utility columns from metadata.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            List[Dict[str, Any]]: Dense daily timeseries rows for the whole period.
        """
        rows_by_date: Dict[date, Dict[str, Any]] = {}

        for row in rows:
            dt = self._to_date(row.get("dt"))
            if dt is None:
                continue
            rows_by_date[dt] = row

        timeseries: List[Dict[str, Any]] = []

        current_day = report_start
        while current_day <= report_end:
            source_row = rows_by_date.get(current_day, {})

            timeseries_row: Dict[str, Any] = {"dt": current_day}

            for column in utility_columns:
                raw_value = source_row.get(column)
                timeseries_row[column] = (
                    self._safe_number(raw_value)
                    if raw_value is not None
                    else None
                )

            timeseries.append(timeseries_row)
            current_day = current_day.fromordinal(current_day.toordinal() + 1)

        return timeseries

    def _build_summary(
        self,
        timeseries: List[Dict[str, Any]],
        metadata: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        """Build per-utility summary for the report period."""
        summary: Dict[str, Dict[str, Any]] = {}

        for column, column_meta in metadata.items():
            total = 0.0

            for row in timeseries:
                total += self._safe_number(row.get(column))

            summary[column] = {
                "display_name": column_meta["display_name"],
                "category": column_meta["category"],
                "unit": column_meta["unit"],
                "description": column_meta["description"],
                "total": round(total, 4),
            }

        return summary

    def _to_date(self, value: Any) -> date | None:
        """Convert a date/datetime-like value to a date."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return None

    def _safe_number(self, value: Any) -> float:
        """Convert input value to float safely."""
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(value)
        except Exception:
            return 0.0

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

    def _get_sensor_monitoring_metric_config(self) -> list[dict[str, str]]:
        """Return business-level metric mapping for utility sensor monitoring.

        Returns:
            list[dict[str, str]]: Ordered metric configuration for utility section.
        """
        return [
            {
                "key": "domestic_water",
                "display_name": "Domestic Water",
                "unit": "m³/h",
                "source_sensor": "dom_waterflow",
            },
            {
                "key": "ico_chilled_water",
                "display_name": "ICO Chilled Water",
                "unit": "kg/h",
                "source_sensor": "ich_supflow",
            },
            {
                "key": "diode_chilled_water",
                "display_name": "DIODE Chilled Water",
                "unit": "kg/h",
                "source_sensor": "dch_supflow",
            },
            {
                "key": "ico_air",
                "display_name": "ICO Air",
                "unit": "m³/h",
                "source_sensor": "iac_airflow",
            },
            {
                "key": "diode_air",
                "display_name": "DIODE Air",
                "unit": "m³/h",
                "source_sensor": "dac_airflow",
            },
            {
                "key": "steam",
                "display_name": "Steam",
                "unit": "m³/h",
                "source_sensor": "boi_steamflow",
            },
            {
                "key": "sakari_water",
                "display_name": "Sakari Water",
                "unit": "m³/h",
                "source_sensor": "sak_waterflow",
            },
        ]

    def build_sensor_monitoring_context(
        self,
        daily_stats: dict[date, dict[str, dict[str, float | None]]],
        report_start: date,
        report_end: date,
    ) -> dict[str, Any]:
        """Build backend context for utility sensor monitoring.

        This context is designed to be UI-flexible and keeps both average and
        maximum daily values for future rendering options.

        Args:
            daily_stats: Daily aggregated sensor stats from ProcessValueService.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            dict[str, Any]: Sensor monitoring context under utility section.
        """
        metric_config = self._get_sensor_monitoring_metric_config()
        sensor_metadata = get_utility_sensor_metadata()
        group_order = get_utility_sensor_group_order()
        group_labels = get_utility_sensor_group_labels()
        group_visuals = self._get_sensor_group_visuals()
        focus_date = report_end

        metric_columns = [
            {
                "key": item["key"],
                "display_name": item["display_name"],
                "unit": item["unit"],
                "source_sensor": item["source_sensor"],
            }
            for item in metric_config
        ]

        period_days: list[date] = []
        current_day = report_start
        while current_day <= report_end:
            period_days.append(current_day)
            current_day = current_day.fromordinal(current_day.toordinal() + 1)

        daily_rows: list[dict[str, Any]] = []

        for dt_value in period_days:
            day_stats = daily_stats.get(dt_value, {})
            metrics: dict[str, Any] = {}

            for item in metric_config:
                metric_key = item["key"]
                sensor_key = item["source_sensor"]
                sensor_stats = day_stats.get(sensor_key, {})

                avg_value = sensor_stats.get("avg")
                max_value = sensor_stats.get("max")

                metrics[metric_key] = {
                    "key": metric_key,
                    "display_name": item["display_name"],
                    "unit": item["unit"],
                    "source_sensor": sensor_key,
                    "avg": avg_value,
                    "max": max_value,
                    "avg_display": self._fmt_or_dash(avg_value),
                    "max_display": self._fmt_or_dash(max_value),
                }

            daily_rows.append({
                "date": dt_value,
                "date_display": self._format_date_with_weekday(dt_value),
                "metrics": metrics,
            })

        focus_day_stats = daily_stats.get(focus_date, {})
        total_sensor_count = 0
        active_sensor_count = 0
        sensor_groups: list[dict[str, Any]] = []
        anomaly_rows: list[dict[str, Any]] = []

        for group_key in group_order:
            group_label = group_labels.get(group_key, group_key.replace("_", " ").title())
            visual = group_visuals.get(group_key, group_visuals["default"])
            sensor_rows: list[dict[str, Any]] = []

            for sensor_key, meta in sensor_metadata.items():
                if meta.get("group") != group_key:
                    continue

                row = self._build_sensor_detail_row(
                    sensor_key=sensor_key,
                    meta=meta,
                    sensor_stats=focus_day_stats.get(sensor_key, {}),
                )
                sensor_rows.append(row)
                total_sensor_count += 1

                if row["has_data"]:
                    active_sensor_count += 1

                if row["has_alert"]:
                    anomaly_rows.append({
                        "sensor_key": sensor_key,
                        "display_name": row["display_name"],
                        "group_key": group_key,
                        "group_label": group_label,
                        "measurement_type": row["measurement_type_label"],
                        "flag_summary": row["flag_summary"],
                        "severity_label": row["severity_label"],
                        "severity_class": row["severity_class"],
                        "min_display": row["min_display"],
                        "avg_display": row["avg_display"],
                        "max_display": row["max_display"],
                        "latest_display": row["latest_display"],
                    })

            sensor_rows.sort(key=lambda item: (item["measurement_type_label"], item["display_name"]))

            sensor_groups.append({
                "key": group_key,
                "label": group_label,
                "accent_color": visual["accent_color"],
                "accent_tint": visual["accent_tint"],
                "sensor_count": len(sensor_rows),
                "active_sensor_count": sum(1 for item in sensor_rows if item["has_data"]),
                "anomaly_count": sum(1 for item in sensor_rows if item["has_alert"]),
                "sensors": sensor_rows,
            })

        anomaly_rows.sort(
            key=lambda item: (
                0 if item["severity_class"] == "is-critical" else 1,
                item["group_label"],
                item["display_name"],
            )
        )

        return {
            "enabled": True,
            "title": "Sensor monitoring",
            "subtitle": "Daily range, average, and anomaly scan by sensor group.",
            "focus_date": focus_date,
            "focus_date_display": self._format_date_with_weekday(focus_date),
            "sensor_count": total_sensor_count,
            "active_sensor_count": active_sensor_count,
            "overview_cards": [
                {
                    "label": group["label"],
                    "accent_color": group["accent_color"],
                    "accent_tint": group["accent_tint"],
                    "sensor_count": group["sensor_count"],
                    "active_sensor_count": group["active_sensor_count"],
                    "anomaly_count": group["anomaly_count"],
                }
                for group in sensor_groups
            ],
            "groups": sensor_groups,
            "anomaly_rows": anomaly_rows,
            "metric_columns": metric_columns,
            "daily_rows": daily_rows,
        }

    def _build_sensor_detail_row(
        self,
        *,
        sensor_key: str,
        meta: dict[str, Any],
        sensor_stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Build one daily sensor detail row for UI rendering."""
        min_value = sensor_stats.get("min")
        avg_value = sensor_stats.get("avg")
        max_value = sensor_stats.get("max")
        latest_value = sensor_stats.get("latest")
        sample_count = int(sensor_stats.get("sample_count") or 0)
        non_null_count = int(sensor_stats.get("non_null_count") or 0)
        zero_count = int(sensor_stats.get("zero_count") or 0)
        negative_count = int(sensor_stats.get("negative_count") or 0)

        has_data = non_null_count > 0
        range_span = None
        avg_position_pct = 50.0

        if isinstance(min_value, (int, float)) and isinstance(max_value, (int, float)):
            range_span = round(float(max_value) - float(min_value), 4)
            if range_span > 0 and isinstance(avg_value, (int, float)):
                avg_position_pct = max(
                    0.0,
                    min(100.0, ((float(avg_value) - float(min_value)) / range_span) * 100.0),
                )

        flags = self._build_sensor_flags(
            has_data=has_data,
            zero_count=zero_count,
            negative_count=negative_count,
            non_null_count=non_null_count,
            range_span=range_span,
        )

        severity_class = "is-normal"
        severity_label = "Normal"
        if flags:
            if any(flag["severity"] == "critical" for flag in flags):
                severity_class = "is-critical"
                severity_label = "Critical"
            else:
                severity_class = "is-warning"
                severity_label = "Warning"

        return {
            "key": sensor_key,
            "display_name": meta.get("display_name") or sensor_key,
            "description": meta.get("description") or "",
            "unit": meta.get("unit") or "",
            "group": meta.get("group") or "",
            "measurement_type": meta.get("measurement_type") or "unknown",
            "measurement_type_label": self._format_measurement_type_label(meta.get("measurement_type")),
            "has_data": has_data,
            "has_alert": bool(flags),
            "severity_class": severity_class,
            "severity_label": severity_label,
            "flag_summary": ", ".join(flag["label"] for flag in flags) if flags else "Normal",
            "flags": flags,
            "sample_count": sample_count,
            "non_null_count": non_null_count,
            "zero_count": zero_count,
            "negative_count": negative_count,
            "min": min_value,
            "avg": avg_value,
            "max": max_value,
            "latest": latest_value,
            "min_display": self._fmt_or_dash(min_value),
            "avg_display": self._fmt_or_dash(avg_value),
            "max_display": self._fmt_or_dash(max_value),
            "latest_display": self._fmt_or_dash(latest_value),
            "avg_position_pct": round(avg_position_pct, 2),
        }

    def _build_sensor_flags(
        self,
        *,
        has_data: bool,
        zero_count: int,
        negative_count: int,
        non_null_count: int,
        range_span: float | None,
    ) -> list[dict[str, str]]:
        """Build lightweight anomaly flags for one sensor."""
        flags: list[dict[str, str]] = []

        if not has_data:
            return [{"label": "No data", "severity": "critical"}]

        if negative_count > 0:
            flags.append({"label": "Negative value", "severity": "critical"})

        if non_null_count > 0 and zero_count == non_null_count:
            flags.append({"label": "All zero", "severity": "warning"})

        if non_null_count > 1 and range_span == 0:
            flags.append({"label": "Flat signal", "severity": "warning"})

        return flags

    def _format_measurement_type_label(self, measurement_type: Any) -> str:
        """Return friendly label for sensor measurement type."""
        mapping = {
            "temperature": "Temperature",
            "pressure": "Pressure",
            "flow": "Flow",
            "capacity": "Capacity",
        }
        return mapping.get(str(measurement_type or "").strip().lower(), "Other")

    def _get_sensor_group_visuals(self) -> dict[str, dict[str, str]]:
        """Return visual accents for sensor monitoring group cards."""
        return {
            "ico_chiller": {
                "accent_color": "#84cc16",
                "accent_tint": "rgba(132, 204, 22, 0.16)",
            },
            "diode_chiller": {
                "accent_color": "#2563eb",
                "accent_tint": "rgba(37, 99, 235, 0.16)",
            },
            "ico_air": {
                "accent_color": "#0f766e",
                "accent_tint": "rgba(15, 118, 110, 0.14)",
            },
            "diode_air": {
                "accent_color": "#7c3aed",
                "accent_tint": "rgba(124, 58, 237, 0.14)",
            },
            "boiler": {
                "accent_color": "#ef4444",
                "accent_tint": "rgba(239, 68, 68, 0.14)",
            },
            "domestic_water": {
                "accent_color": "#f59e0b",
                "accent_tint": "rgba(245, 158, 11, 0.14)",
            },
            "default": {
                "accent_color": "#64748b",
                "accent_tint": "rgba(100, 116, 139, 0.12)",
            },
        }
