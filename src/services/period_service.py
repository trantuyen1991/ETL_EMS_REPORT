# -*- coding: utf-8 -*-
"""
Period resolution service for report generation.

This module converts user/config period input into a canonical ResolvedPeriod
object that can be reused consistently across service and data layers.

Args:
    None

Returns:
    None

Example:
    service = PeriodService()
    period = service.resolve(
        PeriodRequest(period_type="monthly", anchor_date=date(2025, 7, 15))
    )
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any

from src.models.period_models import PeriodRequest, PeriodType, ResolvedPeriod


class PeriodService:
    """Resolve reporting periods from request or configuration."""

    def resolve_anchor_date_from_config(
        self,
        config: dict[str, Any],
        today: date | None = None,
    ) -> date:
        """Resolve the effective anchor date from config or fallback today."""
        env_cfg = config.get("env", {})
        fallback_today = today or date.today()
        return self._parse_optional_date(env_cfg.get("REPORT_ANCHOR_DATE")) or fallback_today

    def resolve_scheduled_periods_from_config(
        self,
        config: dict[str, Any],
        today: date | None = None,
    ) -> list[ResolvedPeriod]:
        """Build the list of report periods that should be exported for one run."""
        anchor_date = self.resolve_anchor_date_from_config(config=config, today=today)
        include_cfg = config.get("config", {}).get("report", {}).get("include", {})

        period_types: list[PeriodType] = []
        if bool(include_cfg.get("daily", True)):
            period_types.append("daily")

        if bool(include_cfg.get("weekly", True)) and self._is_sunday(anchor_date):
            period_types.append("weekly")

        if bool(include_cfg.get("monthly", True)) and self._is_month_end(anchor_date):
            period_types.append("monthly")

        return [
            self.resolve(
                PeriodRequest(period_type=period_type, anchor_date=anchor_date),
                today=anchor_date,
            )
            for period_type in period_types
        ]

    def resolve(self, request: PeriodRequest, today: date | None = None) -> ResolvedPeriod:
        """Resolve a period request into a canonical period object.

        Args:
            request: Requested period definition.
            today: Optional fallback date when anchor_date is missing.

        Returns:
            ResolvedPeriod: Canonical resolved period object.

        Example:
            service = PeriodService()
            period = service.resolve(
                PeriodRequest(period_type="weekly", anchor_date=date(2025, 7, 7))
            )
        """
        today = today or date.today()

        if request.period_type == "daily":
            anchor = request.anchor_date or today
            start_date = anchor
            end_date = anchor
            previous_start_date = anchor - timedelta(days=1)
            previous_end_date = anchor - timedelta(days=1)
            previous_anchor_date = previous_start_date

        elif request.period_type == "weekly":
            anchor = request.anchor_date or today
            start_date = anchor - timedelta(days=anchor.weekday())
            end_date = start_date + timedelta(days=6)
            previous_start_date = start_date - timedelta(days=7)
            previous_end_date = end_date - timedelta(days=7)
            previous_anchor_date = anchor - timedelta(days=7)

        elif request.period_type == "monthly":
            anchor = request.anchor_date or today
            start_date = date(anchor.year, anchor.month, 1)
            end_day = monthrange(anchor.year, anchor.month)[1]
            end_date = date(anchor.year, anchor.month, end_day)

            if anchor.month == 1:
                prev_year = anchor.year - 1
                prev_month = 12
            else:
                prev_year = anchor.year
                prev_month = anchor.month - 1

            previous_start_date = date(prev_year, prev_month, 1)
            previous_end_date = date(
                prev_year,
                prev_month,
                monthrange(prev_year, prev_month)[1],
            )
            previous_anchor_date = date(
                prev_year,
                prev_month,
                min(anchor.day, monthrange(prev_year, prev_month)[1]),
            )

        elif request.period_type == "custom":
            if request.custom_start_date is None or request.custom_end_date is None:
                raise ValueError(
                    "custom_start_date and custom_end_date are required for custom period."
                )

            if request.custom_start_date > request.custom_end_date:
                raise ValueError("custom_start_date must be <= custom_end_date.")

            start_date = request.custom_start_date
            end_date = request.custom_end_date

            duration_days = (end_date - start_date).days + 1
            previous_end_date = start_date - timedelta(days=1)
            previous_start_date = previous_end_date - timedelta(days=duration_days - 1)
            anchor = end_date
            previous_anchor_date = previous_end_date

        else:
            raise ValueError(f"Unsupported period_type: {request.period_type}")

        total_days = (end_date - start_date).days + 1

        return ResolvedPeriod(
            period_type=request.period_type,
            grain="day",
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            previous_start_date=previous_start_date,
            previous_end_date=previous_end_date,
            label=self._build_label(request.period_type, start_date, end_date),
            comparison_label=self._build_label(
                request.period_type,
                previous_start_date,
                previous_end_date,
            ),
            file_suffix=self._build_file_suffix(
                request.period_type,
                start_date,
                end_date,
            ),
            anchor_date=anchor,
            previous_anchor_date=previous_anchor_date,
        )

    def resolve_from_config(
        self,
        config: dict[str, Any],
        today: date | None = None,
    ) -> ResolvedPeriod:
        """Resolve a report period from loaded application config.

        Expected config source:
        - config["env"]["REPORT_PERIOD_TYPE"]
        - config["env"]["REPORT_ANCHOR_DATE"]
        - config["env"]["REPORT_CUSTOM_START_DATE"]
        - config["env"]["REPORT_CUSTOM_END_DATE"]

        Args:
            config: Loaded application config.
            today: Optional fallback date when anchor_date is missing.

        Returns:
            ResolvedPeriod: Canonical resolved period object.

        Example:
            period = service.resolve_from_config(config)
        """
        env_cfg = config.get("env", {})

        period_type_raw = str(env_cfg.get("REPORT_PERIOD_TYPE", "monthly")).strip().lower()
        anchor_date = self._parse_optional_date(env_cfg.get("REPORT_ANCHOR_DATE"))
        custom_start_date = self._parse_optional_date(env_cfg.get("REPORT_CUSTOM_START_DATE"))
        custom_end_date = self._parse_optional_date(env_cfg.get("REPORT_CUSTOM_END_DATE"))

        allowed_period_types = {"daily", "weekly", "monthly", "custom"}
        if period_type_raw not in allowed_period_types:
            raise ValueError(
                "REPORT_PERIOD_TYPE must be one of: daily, weekly, monthly, custom."
            )

        if period_type_raw == "custom":
            if custom_start_date is None or custom_end_date is None:
                raise ValueError(
                    "REPORT_CUSTOM_START_DATE and REPORT_CUSTOM_END_DATE are required "
                    "when REPORT_PERIOD_TYPE=custom."
                )

            request = PeriodRequest(
                period_type="custom",
                custom_start_date=custom_start_date,
                custom_end_date=custom_end_date,
            )
        else:
            request = PeriodRequest(
                period_type=period_type_raw,  # type: ignore[arg-type]
                anchor_date=anchor_date,
            )

        return self.resolve(request=request, today=today)

    def _parse_optional_date(self, value: Any) -> date | None:
        """Parse an optional YYYY-MM-DD string into a date.

        Args:
            value: Raw config value.

        Returns:
            date | None: Parsed date or None if empty.

        Example:
            parsed = self._parse_optional_date("2025-01-07")
        """
        if value is None:
            return None

        text = str(value).strip()
        if not text:
            return None

        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format: '{text}'. Expected YYYY-MM-DD."
            ) from exc

    def _is_sunday(self, value: date) -> bool:
        """Return True when the date falls on Sunday."""
        return value.weekday() == 6

    def _is_month_end(self, value: date) -> bool:
        """Return True when the date is the last day of its month."""
        return value.day == monthrange(value.year, value.month)[1]

    def _build_label(
        self,
        period_type: PeriodType,
        start_date: date,
        end_date: date,
    ) -> str:
        """Build a user-facing label for a period.

        Args:
            period_type: Resolved period type.
            start_date: Inclusive period start date.
            end_date: Inclusive period end date.

        Returns:
            str: Human-readable period label.

        Example:
            label = self._build_label("weekly", date(2025, 7, 7), date(2025, 7, 13))
        """
        if period_type == "daily":
            return start_date.strftime("%Y-%m-%d")

        if period_type == "weekly":
            return f"{start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}"

        if period_type == "monthly":
            return start_date.strftime("%Y-%m")

        return f"{start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}"

    def _build_file_suffix(
        self,
        period_type: PeriodType,
        start_date: date,
        end_date: date,
    ) -> str:
        """Build a file-safe suffix for export naming.

        Args:
            period_type: Resolved period type.
            start_date: Inclusive period start date.
            end_date: Inclusive period end date.

        Returns:
            str: File-safe suffix string.

        Example:
            suffix = self._build_file_suffix("monthly", date(2025, 7, 1), date(2025, 7, 31))
        """
        if period_type == "daily":
            return f"daily_{start_date.strftime('%Y%m%d')}"

        if period_type == "weekly":
            return (
                f"weekly_{start_date.strftime('%Y%m%d')}_"
                f"{end_date.strftime('%Y%m%d')}"
            )

        if period_type == "monthly":
            return f"monthly_{start_date.strftime('%Y%m')}"

        return (
            f"custom_{start_date.strftime('%Y%m%d')}_"
            f"{end_date.strftime('%Y%m%d')}"
        )
