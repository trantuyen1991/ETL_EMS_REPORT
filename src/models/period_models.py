# -*- coding: utf-8 -*-
"""
Period models for report generation.

This module defines canonical request and resolved-period objects used across
the service and data layers.

Args:
    None

Returns:
    None

Example:
    request = PeriodRequest(
        period_type="weekly",
        anchor_date=date(2025, 7, 7),
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional


PeriodType = Literal["daily", "weekly", "monthly", "custom"]
PeriodGrain = Literal["day"]


@dataclass(frozen=True)
class PeriodRequest:
    """User/config-driven period selection request.

    Args:
        period_type: Requested period type.
        anchor_date: Reference date for daily/weekly/monthly periods.
        custom_start_date: Inclusive custom start date.
        custom_end_date: Inclusive custom end date.

    Returns:
        PeriodRequest: Immutable request object.

    Example:
        request = PeriodRequest(
            period_type="monthly",
            anchor_date=date(2025, 7, 15),
        )
    """

    period_type: PeriodType
    anchor_date: Optional[date] = None
    custom_start_date: Optional[date] = None
    custom_end_date: Optional[date] = None


@dataclass(frozen=True)
class ResolvedPeriod:
    """Canonical resolved report period.

    Args:
        period_type: Final resolved period type.
        grain: Query/storage grain used by the repository.
        start_date: Inclusive current period start date.
        end_date: Inclusive current period end date.
        total_days: Inclusive number of days in the current period.
        previous_start_date: Inclusive previous comparison start date.
        previous_end_date: Inclusive previous comparison end date.
        label: Human-readable label for the current period.
        comparison_label: Human-readable label for the previous period.
        file_suffix: File-safe suffix for export names.

    Returns:
        ResolvedPeriod: Immutable canonical period object.

    Example:
        period.start_date
        period.end_date
        period.label
    """

    period_type: PeriodType
    grain: PeriodGrain
    start_date: date
    end_date: date
    total_days: int
    previous_start_date: date
    previous_end_date: date
    label: str
    comparison_label: str
    file_suffix: str
    anchor_date: Optional[date] = None
    previous_anchor_date: Optional[date] = None
