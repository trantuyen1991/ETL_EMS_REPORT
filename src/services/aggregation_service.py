# -*- coding: utf-8 -*-

from datetime import date
from typing import Dict, List, Any


class AggregationService:
    """
    Aggregates raw energy data into a structured report context.

    Args:
        repo: EnergyDataRepository instance
        config: Global configuration dict

    Returns:
        Dict[str, Any]: Report context for rendering

    Example:
        service = AggregationService(repo, config)
        ctx = service.build_report(start_date, end_date)
    """

    def __init__(self, repo, config: dict):
        self._repo = repo
        self._config = config

    def build_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Build full report dataset.

        Args:
            start_date (date): Start date
            end_date (date): End date

        Returns:
            dict: Report context
        """

        detail_rows = self._repo.get_daily_detail_rows(start_date, end_date)
        top_meters = self._repo.get_top_n_meters(start_date, end_date)

        total_energy = self._calculate_total_energy(detail_rows)
        bar_chart = self._build_bar_chart(detail_rows)
        summary = {
            "total_days": len(detail_rows),
            "avg_daily": round(total_energy / len(detail_rows), 2) if detail_rows else 0,
        }

        return {
            "report_period": self._format_period(start_date, end_date),
            "start_date": start_date,
            "end_date": end_date,

            "total_energy": total_energy,

            "detail_rows": detail_rows,
            "top_meters": top_meters,
            "bar_chart_data": bar_chart,

            "summary": summary,
            "meta": {
                "workshop_name": self._config["env"].get("WORKSHOP_NAME", ""),
                "energy_unit": self._config["env"].get("ENERGY_UNIT", "kWh"),
            },
        }

    def _calculate_total_energy(self, detail_rows: List[Dict[str, Any]]) -> float:
        """
        Calculate total energy from all meters.

        Args:
            detail_rows (list): Raw rows

        Returns:
            float: Total energy
        """
        total = 0.0

        for row in detail_rows:
            for key, value in row.items():
                if key != "dt" and isinstance(value, (int, float)):
                    total += value if isinstance(value, (int, float)) else 0

        return round(total, 2)

    def _build_bar_chart(self, detail_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build bar chart dataset.

        Args:
            detail_rows (list): Raw rows

        Returns:
            dict: Chart data
        """

        labels = []
        values = []

        sorted_rows = sorted(detail_rows, key=lambda x: x["dt"])

        for row in sorted_rows:
            dt = row.get("dt")
            total = 0.0

            for key, value in row.items():
                if key != "dt" and isinstance(value, (int, float)):
                    total += value if isinstance(value, (int, float)) else 0

            labels.append(str(dt))
            values.append(round(total, 2))

        return {
            "labels": labels,
            "values": values,
        }

    def _format_period(self, start_date: date, end_date: date) -> str:
        """
        Format report period.

        Args:
            start_date (date)
            end_date (date)

        Returns:
            str
        """
        return f"{start_date} → {end_date}"