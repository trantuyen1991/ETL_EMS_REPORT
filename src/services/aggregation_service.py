# -*- coding: utf-8 -*-

"""
Aggregation service for energy report datasets.

This module transforms raw repository output into a clean report context
for HTML rendering and file export.

Args:
    repo: EnergyDataRepository instance.
    config: Loaded application configuration.

Returns:
    AggregationService: Service instance for building report datasets.

Example:
    service = AggregationService(repo, config)
    report_context = service.build_report(start_date, end_date)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


class AggregationService:
    """
    Build reusable report datasets from repository output.

    Args:
        repo: Repository used to query source data.
        config: Loaded application configuration.

    Returns:
        AggregationService: Aggregation service instance.

    Example:
        service = AggregationService(repo, config)
        report = service.build_report(date(2025, 7, 1), date(2025, 7, 7))
    """

    def __init__(self, repo, config: dict[str, Any]) -> None:
        """
        Initialize aggregation service.

        Args:
            repo: Energy data repository instance.
            config: Loaded application configuration.

        Returns:
            None
        """
        self._repo = repo
        self._config = config

    def build_report(self, start_date: date, end_date: date) -> dict[str, Any]:
        """
        Build the full report context.

        Args:
            start_date: Inclusive start date.
            end_date: Inclusive end date.

        Returns:
            dict[str, Any]: Full report context for template rendering and export.

        Example:
            report = service.build_report(date(2025, 7, 1), date(2025, 7, 7))
        """
        raw_detail_rows = self._repo.get_daily_detail_rows(start_date, end_date)
        top_meters = self._repo.get_top_n_meters(start_date, end_date, top_n=10)
        meter_columns = self._repo.get_meter_columns()

        total_meter_count = len(meter_columns)
        total_energy = self._calculate_total_energy(raw_detail_rows)

        daily_summary_rows = self._build_daily_summary_rows(
            detail_rows=raw_detail_rows,
            total_meter_count=total_meter_count,
        )

        bar_chart_data = self._build_bar_chart(daily_summary_rows)
        comparison = self._build_period_comparison(start_date, end_date, current_total=total_energy)

        summary = {
            "total_days": len(raw_detail_rows),
            "avg_daily": round(total_energy / len(raw_detail_rows), 2) if raw_detail_rows else 0,
            "total_meter_count": total_meter_count,
        }

        return {
            "report_period": self._format_period(start_date, end_date),
            "start_date": start_date,
            "end_date": end_date,
            "total_energy": total_energy,
            "top_meters": top_meters,
            "bar_chart_data": bar_chart_data,
            "daily_summary_rows": daily_summary_rows,
            "raw_detail_rows": raw_detail_rows,
            "comparison": comparison,
            "summary": summary,
            "meta": {
                "workshop_name": self._config["env"].get("WORKSHOP_NAME", ""),
                "energy_unit": self._config["env"].get("ENERGY_UNIT", "kWh"),
            },
        }

    def _calculate_total_energy(self, detail_rows: list[dict[str, Any]]) -> float:
        """
        Calculate total energy across all rows and all meter columns.

        Args:
            detail_rows: Raw detail rows from repository.

        Returns:
            float: Total energy rounded to 2 decimals.

        Example:
            total = self._calculate_total_energy(detail_rows)
        """
        total = 0.0

        for row in detail_rows:
            for key, value in row.items():
                if key == "dt":
                    continue
                total += value if isinstance(value, (int, float)) else 0

        return round(total, 2)

    def _build_daily_summary_rows(
        self,
        detail_rows: list[dict[str, Any]],
        total_meter_count: int,
    ) -> list[dict[str, Any]]:
        """
        Build compact daily summary rows for the PDF report.

        Each row contains:
        - Date
        - Total Energy
        - Top 1 Meter
        - Top 1 Value
        - Active Meter Count
        - Average per Active Meter
        - Total Meter Count
        - Inactive Meter Count

        Args:
            detail_rows: Raw detail rows from repository.
            total_meter_count: Total number of meter columns in the source.

        Returns:
            list[dict[str, Any]]: Daily summary rows ordered by date ascending.

        Example:
            rows = self._build_daily_summary_rows(detail_rows, total_meter_count=52)
        """
        summary_rows: list[dict[str, Any]] = []

        sorted_rows = sorted(detail_rows, key=lambda x: x.get("dt"))

        for row in sorted_rows:
            dt_value = row.get("dt")

            total_energy = 0.0
            active_meter_count = 0
            top_meter_name = ""
            top_meter_value = 0.0

            for key, value in row.items():
                if key == "dt":
                    continue

                numeric_value = value if isinstance(value, (int, float)) else 0.0
                total_energy += numeric_value

                if numeric_value > 0:
                    active_meter_count += 1

                if numeric_value > top_meter_value:
                    top_meter_value = numeric_value
                    top_meter_name = key

            inactive_meter_count = total_meter_count - active_meter_count
            avg_per_active_meter = (
                round(total_energy / active_meter_count, 2) if active_meter_count > 0 else 0
            )

            summary_rows.append(
                {
                    "dt": dt_value,
                    "total_energy": round(total_energy, 2),
                    "top_meter_name": top_meter_name,
                    "top_meter_value": round(top_meter_value, 2),
                    "active_meter_count": active_meter_count,
                    "avg_per_active_meter": avg_per_active_meter,
                    "total_meter_count": total_meter_count,
                    "inactive_meter_count": inactive_meter_count,
                }
            )

        return summary_rows

    def _build_bar_chart(self, daily_summary_rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
        """
        Build daily bar chart data from daily summary rows.

        Args:
            daily_summary_rows: Daily summary rows.

        Returns:
            dict[str, list[Any]]: Chart labels and values.

        Example:
            chart = self._build_bar_chart(daily_summary_rows)
        """
        sorted_rows = sorted(daily_summary_rows, key=lambda x: x.get("dt"))

        labels = [str(row["dt"]) for row in sorted_rows]
        values = [row["total_energy"] for row in sorted_rows]

        return {
            "labels": labels,
            "values": values,
        }

    def _get_previous_period_range(self, start_date: date, end_date: date) -> tuple[date, date]:
        """
        Calculate the immediately previous period with the same inclusive duration.

        Args:
            start_date: Current period inclusive start date.
            end_date: Current period inclusive end date.

        Returns:
            tuple[date, date]: Previous period inclusive start and end dates.

        Example:
            current: 2025-07-01 -> 2025-07-07
            previous: 2025-06-24 -> 2025-06-30
        """
        duration_days = (end_date - start_date).days + 1
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - timedelta(days=duration_days - 1)
        return prev_start_date, prev_end_date

    def _build_period_comparison(
        self,
        start_date: date,
        end_date: date,
        current_total: float,
    ) -> dict[str, Any]:
        """
        Build comparison metrics versus the immediately previous period.

        Args:
            start_date: Current period inclusive start date.
            end_date: Current period inclusive end date.
            current_total: Total energy for the current period.

        Returns:
            dict[str, Any]: Comparison metrics for reporting.

        Example:
            comparison = self._build_period_comparison(start_date, end_date, 1234.56)
        """
        prev_start_date, prev_end_date = self._get_previous_period_range(start_date, end_date)

        previous_rows = self._repo.get_daily_detail_rows(prev_start_date, prev_end_date)
        previous_total = self._calculate_total_energy(previous_rows)

        delta = round(current_total - previous_total, 2)

        if previous_total > 0:
            delta_pct = round((delta / previous_total) * 100, 2)
        else:
            delta_pct = 0.0

        if delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        else:
            trend = "flat"

        return {
            "current_period": self._format_period(start_date, end_date),
            "previous_period": self._format_period(prev_start_date, prev_end_date),
            "current_total": round(current_total, 2),
            "previous_total": round(previous_total, 2),
            "delta": delta,
            "delta_pct": delta_pct,
            "trend": trend,
            "has_previous_data": len(previous_rows) > 0,
        }

    def _format_period(self, start_date: date, end_date: date) -> str:
        """
        Format report period string.

        Args:
            start_date: Inclusive start date.
            end_date: Inclusive end date.

        Returns:
            str: Human-readable period string.

        Example:
            period = self._format_period(date(2025, 7, 1), date(2025, 7, 7))
        """
        return f"{start_date} → {end_date}"