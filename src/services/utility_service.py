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
    get_utility_sensor_anomaly_rules,
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
        raw_rows: list[dict[str, Any]] | None = None,
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
        is_intraday_period = report_start == report_end

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
        sensor_rows_by_key: dict[str, dict[str, Any]] = {}

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
                sensor_rows_by_key[sensor_key] = row
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
                        "flag_detail_summary": row["flag_detail_summary"],
                        "flag_count": row["flag_count"],
                        "primary_flag": row["primary_flag"],
                        "severity_label": row["severity_label"],
                        "severity_class": row["severity_class"],
                        "anomaly_score": row["anomaly_score"],
                        "min_display": row["min_display"],
                        "avg_display": row["avg_display"],
                        "max_display": row["max_display"],
                        "latest_display": row["latest_display"],
                    })

            sensor_rows.sort(
                key=lambda item: (
                    item["severity_rank"],
                    item["measurement_type_label"],
                    item["display_name"],
                )
            )

            sensor_groups.append({
                "key": group_key,
                "label": group_label,
                "accent_color": visual["accent_color"],
                "accent_tint": visual["accent_tint"],
                "sensor_count": len(sensor_rows),
                "active_sensor_count": sum(1 for item in sensor_rows if item["has_data"]),
                "anomaly_count": sum(1 for item in sensor_rows if item["has_alert"]),
                "critical_count": sum(1 for item in sensor_rows if item["severity_class"] == "is-critical"),
                "warning_count": sum(1 for item in sensor_rows if item["severity_class"] == "is-warning"),
                "sensors": sensor_rows,
            })

        anomaly_rows.sort(
            key=lambda item: (
                0 if item["severity_class"] == "is-critical" else 1,
                -item["anomaly_score"],
                item["group_label"],
                item["display_name"],
            )
        )

        trend_clusters = self._build_sensor_trend_clusters(
            raw_rows=raw_rows or [],
            sensor_metadata=sensor_metadata,
            sensor_rows_by_key=sensor_rows_by_key,
            group_order=group_order,
            group_labels=group_labels,
            group_visuals=group_visuals,
            focus_date=focus_date,
            enabled=is_intraday_period,
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
                    "critical_count": group["critical_count"],
                    "warning_count": group["warning_count"],
                }
                for group in sensor_groups
            ],
            "groups": sensor_groups,
            "anomaly_rows": anomaly_rows,
            "metric_columns": metric_columns,
            "daily_rows": daily_rows,
            "trend_mode": "intraday" if is_intraday_period else "aggregate_only",
            "trend_clusters": trend_clusters,
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
        missing_count = max(0, sample_count - non_null_count)
        coverage_ratio = (
            round(non_null_count / sample_count, 4)
            if sample_count > 0
            else 0.0
        )
        zero_ratio = (
            round(zero_count / non_null_count, 4)
            if non_null_count > 0
            else None
        )
        negative_ratio = (
            round(negative_count / non_null_count, 4)
            if non_null_count > 0
            else None
        )
        negative_min_value = (
            float(min_value)
            if isinstance(min_value, (int, float)) and float(min_value) < 0.0
            else None
        )

        has_data = non_null_count > 0
        range_span = None
        avg_position_pct = 50.0
        peak_to_avg_ratio = None
        latest_drift_ratio = None
        rules = get_utility_sensor_anomaly_rules(
            measurement_type=str(meta.get("measurement_type") or ""),
            overrides=meta.get("anomaly_rules"),
        )

        if isinstance(min_value, (int, float)) and isinstance(max_value, (int, float)):
            range_span = round(float(max_value) - float(min_value), 4)
            if range_span > 0 and isinstance(avg_value, (int, float)):
                avg_position_pct = max(
                    0.0,
                    min(100.0, ((float(avg_value) - float(min_value)) / range_span) * 100.0),
                )

        peak_to_avg_ratio = self._compute_peak_to_avg_ratio(
            min_value=min_value,
            max_value=max_value,
            avg_value=avg_value,
            floor=float(rules.get("peak_ratio_floor", 1.0) or 1.0),
        )
        latest_drift_ratio = self._compute_latest_drift_ratio(
            latest_value=latest_value,
            avg_value=avg_value,
            floor=float(rules.get("latest_drift_floor", 1.0) or 1.0),
        )
        negative_tolerance_abs = float(rules.get("negative_tolerance_abs", 0.0) or 0.0)
        negative_excess_abs = self._compute_negative_excess_abs(
            negative_min_value=negative_min_value,
            negative_tolerance_abs=negative_tolerance_abs,
        )

        flags = self._build_sensor_flags(
            rules=rules,
            has_data=has_data,
            min_value=min_value,
            max_value=max_value,
            latest_value=latest_value,
            sample_count=sample_count,
            coverage_ratio=coverage_ratio,
            zero_ratio=zero_ratio,
            negative_ratio=negative_ratio,
            zero_count=zero_count,
            negative_count=negative_count,
            non_null_count=non_null_count,
            range_span=range_span,
            peak_to_avg_ratio=peak_to_avg_ratio,
            latest_drift_ratio=latest_drift_ratio,
            negative_tolerance_abs=negative_tolerance_abs,
            negative_excess_abs=negative_excess_abs,
        )

        severity_class = "is-normal"
        severity_label = "Normal"
        severity_rank = 2
        if flags:
            if any(flag["severity"] == "critical" for flag in flags):
                severity_class = "is-critical"
                severity_label = "Critical"
                severity_rank = 0
            else:
                severity_class = "is-warning"
                severity_label = "Warning"
                severity_rank = 1

        anomaly_score = self._score_sensor_flags(flags)

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
            "severity_rank": severity_rank,
            "flag_summary": self._summarize_sensor_flags(flags),
            "flag_detail_summary": self._summarize_sensor_flag_details(flags),
            "primary_flag": flags[0]["label"] if flags else "Normal",
            "flag_count": len(flags),
            "flags": flags,
            "anomaly_score": anomaly_score,
            "sample_count": sample_count,
            "non_null_count": non_null_count,
            "missing_count": missing_count,
            "coverage_ratio": coverage_ratio,
            "coverage_pct_display": f"{coverage_ratio * 100:.0f}%",
            "zero_count": zero_count,
            "zero_ratio": zero_ratio,
            "negative_count": negative_count,
            "negative_ratio": negative_ratio,
            "negative_min_value": negative_min_value,
            "negative_tolerance_abs": negative_tolerance_abs,
            "negative_tolerance_display": f"-{negative_tolerance_abs:,.2f}",
            "negative_excess_abs": negative_excess_abs,
            "show_negative_tolerance_note": bool(
                flags
                and any(flag.get("code") == "negative_exceeds_tolerance" for flag in flags)
            ),
            "min": min_value,
            "avg": avg_value,
            "max": max_value,
            "latest": latest_value,
            "range_span": range_span,
            "peak_to_avg_ratio": peak_to_avg_ratio,
            "latest_drift_ratio": latest_drift_ratio,
            "min_display": self._fmt_or_dash(min_value),
            "avg_display": self._fmt_or_dash(avg_value),
            "max_display": self._fmt_or_dash(max_value),
            "latest_display": self._fmt_or_dash(latest_value),
            "avg_position_pct": round(avg_position_pct, 2),
        }

    def _build_sensor_flags(
        self,
        *,
        rules: dict[str, Any],
        has_data: bool,
        min_value: float | None,
        max_value: float | None,
        latest_value: float | None,
        sample_count: int,
        coverage_ratio: float,
        zero_ratio: float | None,
        negative_ratio: float | None,
        zero_count: int,
        negative_count: int,
        non_null_count: int,
        range_span: float | None,
        peak_to_avg_ratio: float | None,
        latest_drift_ratio: float | None,
        negative_tolerance_abs: float,
        negative_excess_abs: float | None,
    ) -> list[dict[str, str]]:
        """Build lightweight anomaly flags for one sensor."""
        flags: list[dict[str, str]] = []

        if not has_data:
            return [{
                "code": "no_data",
                "label": "Missing data",
                "detail": "No valid samples were captured for this day.",
                "severity": "critical",
                "priority": 100,
            }]

        coverage_warning_ratio = float(rules.get("coverage_warning_ratio", 0.85) or 0.85)
        coverage_critical_ratio = float(rules.get("coverage_critical_ratio", 0.5) or 0.5)
        zero_ratio_warning = float(rules.get("zero_ratio_warning", 0.85) or 0.85)
        flat_range_epsilon = float(rules.get("flat_range_epsilon", 0.0) or 0.0)
        peak_ratio_warning = float(rules.get("peak_ratio_warning", 12.0) or 12.0)
        peak_ratio_critical = float(rules.get("peak_ratio_critical", 20.0) or 20.0)
        latest_drift_warning = float(rules.get("latest_drift_warning", 2.5) or 2.5)
        latest_drift_critical = float(rules.get("latest_drift_critical", 5.0) or 5.0)

        if sample_count > 0 and coverage_ratio < coverage_critical_ratio:
            flags.append({
                "code": "low_coverage",
                "label": "Low coverage",
                "detail": f"Coverage {coverage_ratio * 100:.0f}% is below {coverage_critical_ratio * 100:.0f}%.",
                "severity": "critical",
                "priority": 95,
            })
        elif sample_count > 0 and coverage_ratio < coverage_warning_ratio:
            flags.append({
                "code": "partial_coverage",
                "label": "Partial coverage",
                "detail": f"Coverage {coverage_ratio * 100:.0f}% is below expected {coverage_warning_ratio * 100:.0f}%.",
                "severity": "warning",
                "priority": 70,
            })

        if (
            negative_count > 0
            and not bool(rules.get("allow_negative", False))
            and negative_excess_abs is not None
            and negative_excess_abs > 0.0
        ):
            allowed_floor = -negative_tolerance_abs
            if (
                isinstance(min_value, (int, float))
                and isinstance(max_value, (int, float))
                and float(min_value) < (-negative_tolerance_abs)
                and float(max_value) > negative_tolerance_abs
            ):
                flags.append({
                    "code": "negative_exceeds_tolerance",
                    "label": "Negative beyond tolerance",
                    "detail": f"Min {self._fmt_or_dash(min_value)} is below allowed floor {allowed_floor:,.2f}; signal crosses zero.",
                    "severity": "critical",
                    "priority": 100,
                })
            else:
                flags.append({
                    "code": "negative_exceeds_tolerance",
                    "label": "Negative beyond tolerance",
                    "detail": f"Min {self._fmt_or_dash(min_value)} is below allowed floor {allowed_floor:,.2f}.",
                    "severity": "critical",
                    "priority": 98,
                })

        if non_null_count > 0 and zero_count == non_null_count:
            flags.append({
                "code": "all_zero",
                "label": "All zero",
                "detail": f"All {non_null_count} valid samples are zero.",
                "severity": "warning",
                "priority": 80,
            })
        elif (
            bool(rules.get("track_zero_heavy", True))
            and non_null_count > 0
            and zero_ratio is not None
            and zero_ratio >= zero_ratio_warning
        ):
            flags.append({
                "code": "zero_heavy",
                "label": "Zero-heavy",
                "detail": f"Zero ratio {zero_ratio * 100:.0f}% exceeds {zero_ratio_warning * 100:.0f}%.",
                "severity": "warning",
                "priority": 60,
            })

        if non_null_count > 1 and range_span is not None and range_span <= flat_range_epsilon:
            flags.append({
                "code": "flat_signal",
                "label": "Flat signal",
                "detail": f"Range {range_span:,.2f} is within flat threshold {flat_range_epsilon:,.2f}.",
                "severity": "warning",
                "priority": 55,
            })

        if bool(rules.get("track_peak_dominance", True)) and peak_to_avg_ratio is not None:
            if peak_to_avg_ratio >= peak_ratio_critical:
                flags.append({
                    "code": "peak_dominant",
                    "label": "Peak-dominant",
                    "detail": f"Peak/avg ratio {peak_to_avg_ratio:,.2f} exceeds {peak_ratio_critical:,.2f}.",
                    "severity": "critical",
                    "priority": 85,
                })
            elif peak_to_avg_ratio >= peak_ratio_warning:
                flags.append({
                    "code": "peak_dominant",
                    "label": "Peak-dominant",
                    "detail": f"Peak/avg ratio {peak_to_avg_ratio:,.2f} exceeds {peak_ratio_warning:,.2f}.",
                    "severity": "warning",
                    "priority": 50,
                })

        if (
            bool(rules.get("track_latest_drift", False))
            and latest_value is not None
            and latest_drift_ratio is not None
        ):
            if latest_drift_ratio >= latest_drift_critical:
                flags.append({
                    "code": "latest_drift",
                    "label": "Latest drift",
                    "detail": f"Latest/avg drift ratio {latest_drift_ratio:,.2f} exceeds {latest_drift_critical:,.2f}.",
                    "severity": "critical",
                    "priority": 82,
                })
            elif latest_drift_ratio >= latest_drift_warning:
                flags.append({
                    "code": "latest_drift",
                    "label": "Latest drift",
                    "detail": f"Latest/avg drift ratio {latest_drift_ratio:,.2f} exceeds {latest_drift_warning:,.2f}.",
                    "severity": "warning",
                    "priority": 45,
                })

        return self._dedupe_and_sort_sensor_flags(flags)

    def _dedupe_and_sort_sensor_flags(
        self,
        flags: list[dict[str, str | int]],
    ) -> list[dict[str, str]]:
        """Dedupe repeated labels and return flags sorted by priority."""
        deduped: dict[str, dict[str, str | int]] = {}

        for flag in flags:
            label = str(flag.get("label") or "").strip()
            if not label:
                continue

            existing = deduped.get(label)
            if existing is None or int(flag.get("priority", 0) or 0) > int(existing.get("priority", 0) or 0):
                deduped[label] = flag

        sorted_flags = sorted(
            deduped.values(),
            key=lambda item: (
                0 if item.get("severity") == "critical" else 1,
                -int(item.get("priority", 0) or 0),
                str(item.get("label") or ""),
            ),
        )

        return [
            {
                "code": str(item.get("code") or ""),
                "label": str(item.get("label") or ""),
                "detail": str(item.get("detail") or ""),
                "severity": str(item.get("severity") or "warning"),
            }
            for item in sorted_flags
        ]

    def _summarize_sensor_flags(self, flags: list[dict[str, str]]) -> str:
        """Build compact UI summary from ordered flags."""
        if not flags:
            return "Normal"

        labels = [str(flag.get("label") or "").strip() for flag in flags if flag.get("label")]
        labels = [label for label in labels if label]
        if not labels:
            return "Normal"

        if len(labels) <= 2:
            return ", ".join(labels)

        return f"{', '.join(labels[:2])} +{len(labels) - 2} more"

    def _summarize_sensor_flag_details(self, flags: list[dict[str, str]]) -> str:
        """Build human-readable detail summary for UI helper text."""
        if not flags:
            return ""

        details = [
            str(flag.get("detail") or "").strip()
            for flag in flags
            if str(flag.get("detail") or "").strip()
        ]
        if not details:
            return ""

        if len(details) <= 2:
            return " | ".join(details)

        return " | ".join(details[:2]) + f" | +{len(details) - 2} more"

    def _score_sensor_flags(self, flags: list[dict[str, str]]) -> int:
        """Return sortable anomaly score from ordered flags."""
        score = 0
        for flag in flags:
            if flag.get("severity") == "critical":
                score += 100
            else:
                score += 25
        return score

    def _compute_peak_to_avg_ratio(
        self,
        *,
        min_value: float | None,
        max_value: float | None,
        avg_value: float | None,
        floor: float,
    ) -> float | None:
        """Return absolute peak-to-average ratio for one sensor."""
        numeric_values = [
            float(value)
            for value in [min_value, max_value]
            if isinstance(value, (int, float))
        ]
        if not numeric_values or not isinstance(avg_value, (int, float)):
            return None

        peak_abs = max(abs(value) for value in numeric_values)
        avg_abs = abs(float(avg_value))
        denominator = max(avg_abs, float(floor))
        if denominator <= 0:
            return None

        return round(peak_abs / denominator, 4)

    def _compute_latest_drift_ratio(
        self,
        *,
        latest_value: float | None,
        avg_value: float | None,
        floor: float,
    ) -> float | None:
        """Return drift ratio between latest and average value."""
        if not isinstance(latest_value, (int, float)) or not isinstance(avg_value, (int, float)):
            return None

        denominator = max(abs(float(avg_value)), float(floor))
        if denominator <= 0:
            return None

        return round(abs(float(latest_value) - float(avg_value)) / denominator, 4)

    def _compute_negative_excess_abs(
        self,
        *,
        negative_min_value: float | None,
        negative_tolerance_abs: float,
    ) -> float | None:
        """Return how far a negative minimum exceeds the allowed tolerance."""
        if not isinstance(negative_min_value, (int, float)):
            return None

        excess = abs(float(negative_min_value)) - max(0.0, float(negative_tolerance_abs))
        return round(excess, 4)

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

    def _build_sensor_trend_clusters(
        self,
        *,
        raw_rows: list[dict[str, Any]],
        sensor_metadata: dict[str, dict[str, Any]],
        sensor_rows_by_key: dict[str, dict[str, Any]],
        group_order: list[str],
        group_labels: dict[str, str],
        group_visuals: dict[str, dict[str, str]],
        focus_date: date,
        enabled: bool,
    ) -> list[dict[str, Any]]:
        """Build intraday trend clusters for timestamp-based sensor charts."""
        if not enabled or not raw_rows:
            return []

        rows_for_focus_date = [
            row
            for row in raw_rows
            if self._to_date(row.get("dt")) == focus_date
        ]

        if not rows_for_focus_date:
            return []

        measurement_order = ["temperature", "pressure", "flow", "capacity"]
        measurement_titles = {
            "temperature": "Temperature trend",
            "pressure": "Pressure trend",
            "flow": "Flow trend",
            "capacity": "Capacity trend",
        }

        clusters: list[dict[str, Any]] = []

        for group_key in group_order:
            group_sensors = [
                (sensor_key, meta)
                for sensor_key, meta in sensor_metadata.items()
                if meta.get("group") == group_key
            ]
            if not group_sensors:
                continue

            visual = group_visuals.get(group_key, group_visuals["default"])
            charts: list[dict[str, Any]] = []

            for measurement_type in measurement_order:
                measurement_sensors = [
                    (sensor_key, meta)
                    for sensor_key, meta in group_sensors
                    if str(meta.get("measurement_type") or "").strip().lower() == measurement_type
                ]
                if not measurement_sensors:
                    continue

                series_items: list[dict[str, Any]] = []

                for index, (sensor_key, meta) in enumerate(measurement_sensors):
                    points: list[dict[str, Any]] = []

                    for row in rows_for_focus_date:
                        ts_value = row.get("dt")
                        raw_value = row.get(sensor_key)
                        if not isinstance(raw_value, (int, float)):
                            continue

                        points.append({
                            "ts": self._format_timestamp(ts_value),
                            "value": round(float(raw_value), 4),
                            "is_negative": float(raw_value) < 0.0,
                            "is_zero": float(raw_value) == 0.0,
                        })

                    sensor_row = sensor_rows_by_key.get(sensor_key, {})
                    series_items.append({
                        "sensor_key": sensor_key,
                        "label": meta.get("display_name") or sensor_key,
                        "unit": meta.get("unit") or "",
                        "measurement_type": measurement_type,
                        "measurement_type_label": self._format_measurement_type_label(measurement_type),
                        "color": self._get_sensor_series_color(measurement_type, index),
                        "point_count": len(points),
                        "latest_ts": points[-1]["ts"] if points else "-",
                        "has_alert": bool(sensor_row.get("has_alert")),
                        "severity_class": sensor_row.get("severity_class") or "is-normal",
                        "primary_flag": sensor_row.get("primary_flag") or "Normal",
                        "points": points,
                    })

                first_unit = str(measurement_sensors[0][1].get("unit") or "")
                charts.append({
                    "chart_key": f"{group_key}_{measurement_type}",
                    "title": measurement_titles.get(measurement_type, "Sensor trend"),
                    "measurement_type": measurement_type,
                    "measurement_type_label": self._format_measurement_type_label(measurement_type),
                    "unit": first_unit,
                    "series_count": len(series_items),
                    "series": series_items,
                })

            active_group_rows = [
                sensor_rows_by_key.get(sensor_key, {})
                for sensor_key, _meta in group_sensors
            ]
            clusters.append({
                "cluster_key": group_key,
                "cluster_label": group_labels.get(group_key, group_key.replace("_", " ").title()),
                "focus_date": focus_date.isoformat(),
                "accent_color": visual["accent_color"],
                "accent_tint": visual["accent_tint"],
                "sensor_count": len(group_sensors),
                "active_sensor_count": sum(1 for row in active_group_rows if row.get("has_data")),
                "alert_count": sum(1 for row in active_group_rows if row.get("has_alert")),
                "chart_count": len(charts),
                "charts": charts,
            })

        return clusters

    def _get_sensor_series_color(
        self,
        measurement_type: str,
        index: int,
    ) -> str:
        """Return stable line color for one sensor series."""
        palettes = {
            "temperature": ["#ef4444", "#f97316", "#fb7185"],
            "pressure": ["#7c3aed", "#6366f1", "#a855f7"],
            "flow": ["#0ea5e9", "#14b8a6", "#06b6d4"],
            "capacity": ["#22c55e", "#84cc16", "#65a30d"],
            "default": ["#64748b", "#94a3b8", "#475569"],
        }
        palette = palettes.get(str(measurement_type or "").strip().lower(), palettes["default"])
        return palette[index % len(palette)]

    def _format_timestamp(self, value: Any) -> str:
        """Return compact ISO-like timestamp for chart points."""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            return f"{value.isoformat()} 00:00:00"
        return "-"
