# -*- coding: utf-8 -*-
"""
Report builder service.

This module combines all domain data (energy, KPI, utility)
into a unified report context object for rendering or exporting.
"""

from __future__ import annotations

from typing import Any, Dict
from datetime import date

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportBuilderService:
    """Service to assemble full report context."""

    def build_report_context(
        self,
        *,
        meta: Dict[str, Any],
        period: Dict[str, Any],
        energy_object: Dict[str, Any] | None,
        kpi_object: Dict[str, Any] | None,
        utility_object: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """Build final report context.

        Args:
            meta: Global metadata (workshop, unit, etc.)
            period: Period info (start_date, end_date, type)
            energy_object: Energy domain data
            kpi_object: KPI domain data
            utility_object: Utility domain data

        Returns:
            dict: Unified report context

        Example:
            context = builder.build_report_context(...)
        """

        context = {
            "meta": meta,
            "period": period,
            "sections": {
                "energy": energy_object,
                "kpi": kpi_object,
                "utility": utility_object,
            },
        }

        logger.info(
            "Report context built successfully | sections=%s",
            list(context["sections"].keys()),
        )

        return context