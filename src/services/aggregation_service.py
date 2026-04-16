# -*- coding: utf-8 -*-
"""
Aggregation service for energy report datasets.

This module transforms repository output into a clean report context for
HTML rendering and file export. It relies on a resolved period object so
period rules stay outside this service.

Args:
    repo: Period-aware repository adapter.
    config: Loaded application configuration.

Returns:
    AggregationService: Service instance for building report datasets.

Example:
    service = AggregationService(repo, config)
    report = service.build_report(period)
"""

from __future__ import annotations

from typing import Any

from src.models.period_models import ResolvedPeriod


class AggregationService:
    """Build reusable report datasets from repository output.

    Args:
        repo: Repository used to query source data.
        config: Loaded application configuration.

    Returns:
        AggregationService: Aggregation service instance.

    Example:
        service = AggregationService(repo, config)
        report = service.build_report(period)
    """

    def __init__(self, repo, config: dict[str, Any]) -> None:
        """Initialize aggregation service.

        Args:
            repo: Period-aware data repository.
            config: Loaded application configuration.

        Returns:
            None

        Example:
            service = AggregationService(repo, config)
        """
        self._repo = repo
        self._config = config

    def build_report(self, period: ResolvedPeriod) -> dict[str, Any]:
        """Build the full report context.

        Args:
            period: Canonical resolved report period.

        Returns:
            dict[str, Any]: Full report context for template rendering and export.

        Example:
            report = service.build_report(period)
        """
        raw_detail_rows = self._repo.fetch_daily_rows(period)
        top_meters = self._repo.fetch_top_n_meters(period, top_n=10)
        meter_columns = self._repo.get_meter_columns()

        total_meter_count = len(meter_columns)
        total_energy = self._calculate_total_energy(raw_detail_rows)

        daily_summary_rows = self._build_daily_summary_rows(
            detail_rows=raw_detail_rows,
            total_meter_count=total_meter_count,
        )

        bar_chart_data = self._build_bar_chart(daily_summary_rows)

        comparison = self._build_period_comparison(
            period=period,
            current_total=total_energy,
        )

        days_with_data = len(raw_detail_rows)

        summary = {
            "total_days": period.total_days,
            "days_with_data": days_with_data,
            "avg_daily": round(total_energy / days_with_data, 2) if days_with_data else 0,
            "total_meter_count": total_meter_count,
        }

        return {
            "period": period,
            "report_period": period.label,
            "start_date": period.start_date,
            "end_date": period.end_date,
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
        """Calculate total energy across all rows and all meter columns.

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
        """Build compact daily summary rows for the PDF report.

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
                round(total_energy / active_meter_count, 2)
                if active_meter_count > 0
                else 0
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
        """Build daily bar chart data from daily summary rows.

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

    def _build_period_comparison(
        self,
        period: ResolvedPeriod,
        current_total: float,
    ) -> dict[str, Any]:
        """Build comparison metrics versus the resolved previous period.

        Args:
            period: Canonical resolved report period.
            current_total: Total energy for the current period.

        Returns:
            dict[str, Any]: Comparison metrics for reporting.

        Example:
            comparison = self._build_period_comparison(period, 1234.56)
        """
        previous_period = self._create_comparison_period(period)
        previous_rows = self._repo.fetch_daily_rows(previous_period)
        
        previous_total = self._calculate_total_energy(previous_rows)

        delta = round(current_total - previous_total, 2)

        if previous_total > 0:
            delta_pct = round((delta / previous_total) * 100, 2)
        else:
            delta_pct = 0.0

        has_previous_data = len(previous_rows) > 0

        if not has_previous_data:
            delta_pct = None   # hoặc "-"

        if delta > 0:
            trend = "up"
        elif delta < 0:
            trend = "down"
        else:
            trend = "flat"

        return {
            "current_period": period.label,
            "previous_period": period.comparison_label,
            "current_total": round(current_total, 2),
            "previous_total": round(previous_total, 2),
            "delta": delta,
            "delta_pct": delta_pct,
            "trend": trend,
            "has_previous_data": len(previous_rows) > 0,
        }

    def _create_comparison_period(self, period: ResolvedPeriod) -> ResolvedPeriod:
        """Create a lightweight resolved period for the previous comparison range.

        Args:
            period: Canonical resolved report period.

        Returns:
            ResolvedPeriod: Previous comparison period object.

        Example:
            previous_period = self._create_comparison_period(period)
        """
        previous_total_days = (
            period.previous_end_date - period.previous_start_date
        ).days + 1

        return ResolvedPeriod(
            period_type=period.period_type,
            grain=period.grain,
            start_date=period.previous_start_date,
            end_date=period.previous_end_date,
            total_days=previous_total_days,
            previous_start_date=period.previous_start_date,
            previous_end_date=period.previous_end_date,
            label=period.comparison_label,
            comparison_label="",
            file_suffix="",
        )