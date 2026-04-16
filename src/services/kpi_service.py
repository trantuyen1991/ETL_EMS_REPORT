# -*- coding: utf-8 -*-
"""
KPI service for raw KPI dataset processing.

This module prepares raw KPI rows before they are consumed by higher-level
aggregation/report services.

Current scope:
- deduplicate KPI rows by report period
- keep the latest row using dt_lastupdate
- resolve the best KPI rows for a report period using block coverage rules

Args:
    None

Returns:
    None

Example:
    service = KPIService()
    latest_rows = service.select_latest_kpi_rows(raw_rows)
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


class KPIService:
    """Service for KPI raw row preparation."""

    _TIMEFRAME_PRIORITY = {
        "day": 1,
        "week": 2,
        "month": 3,
        "year": 4,
    }

    def select_latest_kpi_rows(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Select the latest KPI row for each unique period and timeframe.

        Rows are grouped by:
        - dt_start
        - dt_end
        - time_frame

        For each group, the row with the latest dt_lastupdate is kept.

        Args:
            rows: Raw KPI rows fetched from energy_kpi.

        Returns:
            list[dict[str, Any]]: Deduplicated KPI rows ordered by period ascending.

        Example:
            service = KPIService()
            latest_rows = service.select_latest_kpi_rows(raw_rows)
        """
        latest_by_period: dict[tuple[Any, Any, Any], dict[str, Any]] = {}

        for row in rows:
            period_key = (
                row.get("dt_start"),
                row.get("dt_end"),
                self._normalize_time_frame(row.get("time_frame")),
            )
            current_updated_at = self._parse_datetime(row.get("dt_lastupdate"))

            if period_key not in latest_by_period:
                latest_by_period[period_key] = row
                continue

            existing_row = latest_by_period[period_key]
            existing_updated_at = self._parse_datetime(
                existing_row.get("dt_lastupdate")
            )

            if current_updated_at > existing_updated_at:
                latest_by_period[period_key] = row

        latest_rows = list(latest_by_period.values())
        latest_rows.sort(
            key=lambda item: (
                self._to_date(item.get("dt_start")),
                self._to_date(item.get("dt_end")),
                self._timeframe_priority(item.get("time_frame")),
            )
        )
        return latest_rows

    def resolve_kpi_rows_for_period(
        self,
        rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> dict[str, Any]:
        """Resolve the best KPI rows for a report period.

        Policy:
        - deduplicate first by latest dt_lastupdate
        - only consider rows fully contained in the report period
        - prefer finer granularity: Day > Week > Month > Year
        - never prorate or split a block across days
        - only accept a row if its full range is still uncovered

        Args:
            rows: Raw KPI rows fetched from energy_kpi.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            dict[str, Any]: KPI resolution result for the requested period.

        Example:
            result = service.resolve_kpi_rows_for_period(
                rows=raw_rows,
                report_start=date(2025, 4, 10),
                report_end=date(2025, 4, 20),
            )
        """
        latest_rows = self.select_latest_kpi_rows(rows)
        report_days = self._build_day_set(report_start, report_end)

        contained_rows = [
            row
            for row in latest_rows
            if self._is_fully_contained(row, report_start, report_end)
        ]

        contained_rows.sort(
            key=lambda row: (
                self._timeframe_priority(row.get("time_frame")),
                self._to_date(row.get("dt_start")),
                self._to_date(row.get("dt_end")),
            )
        )

        covered_days: set[date] = set()
        selected_rows: list[dict[str, Any]] = []

        for row in contained_rows:
            row_days = self._build_row_day_set(row)

            # Only accept a block if its full range is still uncovered.
            if row_days and row_days.isdisjoint(covered_days):
                selected_rows.append(row)
                covered_days.update(row_days)

        uncovered_days = sorted(report_days - covered_days)
        uncovered_ranges = self._compress_missing_days(uncovered_days)

        messages: list[str] = []
        coverage_note = "full"

        if uncovered_days:
            coverage_note = "partial_or_not_applicable"
            messages.append(
                "KPI data does not fully cover the current report period."
            )
            messages.append(
                "Some uncovered days may be non-working days or may have been entered using a different KPI time frame."
            )
            messages.append(
                "For best accuracy, enter KPI daily or for the exact report period."
            )

        return {
            "selected_rows": selected_rows,
            "coverage_days": len(covered_days),
            "report_total_days": len(report_days),
            "is_full_coverage": covered_days == report_days,
            "uncovered_ranges": uncovered_ranges,
            "messages": messages,
            "coverage_note": coverage_note,
        }

    def build_kpi_summary(
        self,
        selected_rows: list[dict[str, Any]],
        coverage_days: int,
        report_total_days: int,
        is_full_coverage: bool,
        uncovered_ranges: list[dict[str, date]],
        coverage_note: str,
        messages: list[str],
    ) -> dict[str, Any]:
        """Build KPI summary from resolved KPI rows.

        Rules:
        - Production is taken directly from KPI rows
        - Energy is taken directly from KPI rows
        - KPI is taken directly from KPI rows
        - No KPI recalculation is applied
        - Covered rows may come from Day/Week/Month/Year blocks
        - No prorating is applied

        Args:
            selected_rows: KPI rows selected by resolve_kpi_rows_for_period().
            coverage_days: Number of covered days in the report period.
            report_total_days: Total inclusive days in the report period.
            is_full_coverage: Whether KPI rows fully cover the report period.
            uncovered_ranges: Uncovered date ranges for the report period.
            coverage_note: Coverage status label.
            messages: KPI coverage messages for report rendering.

        Returns:
            dict[str, Any]: KPI summary object.
        """
        plant_prod = self._sum_numeric(selected_rows, "Total_prod")
        plant_energy = self._sum_numeric(selected_rows, "Total_engy")
        plant_kpi = self._sum_numeric(selected_rows, "Total_kpi")

        ico_prod = self._sum_numeric(selected_rows, "ICO_prod")
        diode_prod = self._sum_numeric(selected_rows, "DIODE_prod")
        sakari_prod = self._sum_numeric(selected_rows, "SAKARI_prod")

        ico_energy = self._sum_numeric(selected_rows, "ICO_engy")
        diode_energy = self._sum_numeric(selected_rows, "DIODE_engy")
        sakari_energy = self._sum_numeric(selected_rows, "SAKARI_engy")

        ico_kpi = self._sum_numeric(selected_rows, "ICO_kpi")
        diode_kpi = self._sum_numeric(selected_rows, "DIODE_kpi")
        sakari_kpi = self._sum_numeric(selected_rows, "SAKARI_kpi")

        return {
            "plant": {
                "total_prod": plant_prod,
                "total_energy": plant_energy,
                "total_kpi": plant_kpi,
            },
            "areas": {
                "ico": {
                    "prod": ico_prod,
                    "energy": ico_energy,
                    "kpi": ico_kpi,
                },
                "diode": {
                    "prod": diode_prod,
                    "energy": diode_energy,
                    "kpi": diode_kpi,
                },
                "sakari": {
                    "prod": sakari_prod,
                    "energy": sakari_energy,
                    "kpi": sakari_kpi,
                },
            },
            "coverage": {
                "coverage_days": coverage_days,
                "report_total_days": report_total_days,
                "is_full_coverage": is_full_coverage,
                "coverage_note": coverage_note,
                "uncovered_ranges": uncovered_ranges,
                "messages": messages,
            },
            "selected_rows": selected_rows,
        }

    def build_kpi_daily_presentation_rows(
        self,
        selected_rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> list[dict[str, Any]]:
        """Build day-by-day KPI presentation rows for report tables.

        Rules:
        - Always create one row per report day
        - If a Day KPI row exists for that date, display its raw values
        - If the date is covered by a larger block (Week/Month/Year), do not prorate;
        only mark the day as covered by a period block
        - If the date is not covered at all, keep values empty and mark as uncovered

        Args:
            selected_rows: KPI rows selected by resolve_kpi_rows_for_period().
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            list[dict[str, Any]]: Daily presentation rows for KPI detail display.

        Example:
            rows = service.build_kpi_daily_presentation_rows(
                selected_rows=result["selected_rows"],
                report_start=date(2025, 1, 1),
                report_end=date(2025, 1, 15),
            )
        """
        presentation_rows: list[dict[str, Any]] = []
        current_day = report_start

        while current_day <= report_end:
            matched_day_row = self._find_exact_day_row(selected_rows, current_day)

            if matched_day_row is not None:
                presentation_rows.append(
                    {
                        "dt": current_day,
                        "coverage_status": "covered",
                        "time_frame_source": matched_day_row.get("time_frame"),
                        "prod": matched_day_row.get("Total_prod"),
                        "energy": matched_day_row.get("Total_engy"),
                        "kpi": matched_day_row.get("Total_kpi"),
                        "ico_prod": matched_day_row.get("ICO_prod"),
                        "ico_energy": matched_day_row.get("ICO_engy"),
                        "ico_kpi": matched_day_row.get("ICO_kpi"),
                        "diode_prod": matched_day_row.get("DIODE_prod"),
                        "diode_energy": matched_day_row.get("DIODE_engy"),
                        "diode_kpi": matched_day_row.get("DIODE_kpi"),
                        "sakari_prod": matched_day_row.get("SAKARI_prod"),
                        "sakari_energy": matched_day_row.get("SAKARI_engy"),
                        "sakari_kpi": matched_day_row.get("SAKARI_kpi"),
                        "note": "",
                    }
                )
                current_day += timedelta(days=1)
                continue

            matched_block_row = self._find_covering_block_row(selected_rows, current_day)

            if matched_block_row is not None:
                presentation_rows.append(
                    {
                        "dt": current_day,
                        "coverage_status": "covered_by_period_block",
                        "time_frame_source": matched_block_row.get("time_frame"),
                        "prod": None,
                        "energy": None,
                        "kpi": None,
                        "ico_prod": None,
                        "ico_energy": None,
                        "ico_kpi": None,
                        "diode_prod": None,
                        "diode_energy": None,
                        "diode_kpi": None,
                        "sakari_prod": None,
                        "sakari_energy": None,
                        "sakari_kpi": None,
                        "note": "Covered by KPI period block. See selected KPI rows below.",
                    }
                )
                current_day += timedelta(days=1)
                continue

            presentation_rows.append(
                {
                    "dt": current_day,
                    "coverage_status": "uncovered",
                    "time_frame_source": None,
                    "prod": None,
                    "energy": None,
                    "kpi": None,
                    "ico_prod": None,
                    "ico_energy": None,
                    "ico_kpi": None,
                    "diode_prod": None,
                    "diode_energy": None,
                    "diode_kpi": None,
                    "sakari_prod": None,
                    "sakari_energy": None,
                    "sakari_kpi": None,
                    "note": "No KPI row selected for this day.",
                }
            )
            current_day += timedelta(days=1)

        return presentation_rows

    def build_kpi_report_object(
        self,
        rows: list[dict[str, Any]],
        report_start: date,
        report_end: date,
    ) -> dict[str, Any]:
        """Build the complete KPI object for report consumption.

        This method orchestrates:
        - latest-row selection
        - coverage-based row resolution
        - KPI summary building
        - daily presentation row building

        Args:
            rows: Raw KPI rows fetched from energy_kpi.
            report_start: Inclusive report start date.
            report_end: Inclusive report end date.

        Returns:
            dict[str, Any]: Complete KPI object for report usage.

        Example:
            kpi_object = service.build_kpi_report_object(
                rows=raw_rows,
                report_start=date(2025, 1, 1),
                report_end=date(2025, 1, 15),
            )
        """
        resolution = self.resolve_kpi_rows_for_period(
            rows=rows,
            report_start=report_start,
            report_end=report_end,
        )

        summary = self.build_kpi_summary(
            selected_rows=resolution["selected_rows"],
            coverage_days=resolution["coverage_days"],
            report_total_days=resolution["report_total_days"],
            is_full_coverage=resolution["is_full_coverage"],
            uncovered_ranges=resolution["uncovered_ranges"],
            coverage_note=resolution["coverage_note"],
            messages=resolution["messages"],
        )

        daily_rows = self.build_kpi_daily_presentation_rows(
            selected_rows=resolution["selected_rows"],
            report_start=report_start,
            report_end=report_end,
        )

        return {
            "summary": summary,
            "coverage": summary["coverage"],
            "selected_rows": resolution["selected_rows"],
            "daily_rows": daily_rows,
        }

    def _normalize_time_frame(self, value: Any) -> str:
        """Normalize the KPI time frame string."""
        if value is None:
            return ""
        return str(value).strip().lower()

    def _timeframe_priority(self, value: Any) -> int:
        """Return priority for one KPI block."""
        normalized = self._normalize_time_frame(value)
        return self._TIMEFRAME_PRIORITY.get(normalized, 99)

    def _parse_datetime(self, value: Any) -> datetime:
        """Parse a datetime-like value into a datetime object.

        Args:
            value: Input datetime value from MySQL row.

        Returns:
            datetime: Parsed datetime object.

        Example:
            parsed = self._parse_datetime("2025-01-15 10:48:11")
        """
        if isinstance(value, datetime):
            return value

        if value is None:
            return datetime.min

        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")

        raise TypeError(f"Unsupported dt_lastupdate type: {type(value)!r}")

    def _to_date(self, value: Any) -> date:
        """Convert a date/datetime-like value into a date."""
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()

        raise TypeError(f"Unsupported date type: {type(value)!r}")

    def _build_day_set(self, start_date: date, end_date: date) -> set[date]:
        """Build a set of all inclusive dates between start and end."""
        days: set[date] = set()
        current = start_date

        while current <= end_date:
            days.add(current)
            current += timedelta(days=1)

        return days

    def _build_row_day_set(self, row: dict[str, Any]) -> set[date]:
        """Build the full covered day set for a KPI row."""
        dt_start = self._to_date(row.get("dt_start"))
        dt_end = self._to_date(row.get("dt_end"))
        return self._build_day_set(dt_start, dt_end)

    def _is_fully_contained(
        self,
        row: dict[str, Any],
        report_start: date,
        report_end: date,
    ) -> bool:
        """Check whether one KPI block is fully inside the report period."""
        dt_start = self._to_date(row.get("dt_start"))
        dt_end = self._to_date(row.get("dt_end"))
        return dt_start >= report_start and dt_end <= report_end

    def _compress_missing_days(
        self,
        missing_days: list[date],
    ) -> list[dict[str, date]]:
        """Compress missing dates into contiguous ranges."""
        if not missing_days:
            return []

        ranges: list[dict[str, date]] = []
        range_start = missing_days[0]
        previous_day = missing_days[0]

        for current_day in missing_days[1:]:
            if current_day == previous_day + timedelta(days=1):
                previous_day = current_day
                continue

            ranges.append(
                {
                    "start_date": range_start,
                    "end_date": previous_day,
                }
            )
            range_start = current_day
            previous_day = current_day

        ranges.append(
            {
                "start_date": range_start,
                "end_date": previous_day,
            }
        )

        return ranges

    def _sum_numeric(
        self,
        rows: list[dict[str, Any]],
        key: str,
    ) -> float:
        """Sum one numeric field across KPI rows.

        Args:
            rows: KPI rows.
            key: Numeric field name.

        Returns:
            float: Rounded sum value.
        """
        total = 0.0

        for row in rows:
            value = row.get(key)

            if value is None:
                continue

            if isinstance(value, (int, float)):
                total += float(value)

        return round(total, 4)

    def _find_exact_day_row(
        self,
        rows: list[dict[str, Any]],
        target_day: date,
    ) -> dict[str, Any] | None:
        """Find one exact Day row for the target day."""
        for row in rows:
            time_frame = self._normalize_time_frame(row.get("time_frame"))
            dt_start = self._to_date(row.get("dt_start"))
            dt_end = self._to_date(row.get("dt_end"))

            if time_frame == "day" and dt_start == target_day and dt_end == target_day:
                return row

        return None


    def _find_covering_block_row(
        self,
        rows: list[dict[str, Any]],
        target_day: date,
    ) -> dict[str, Any] | None:
        """Find one non-Day KPI block that covers the target day."""
        for row in rows:
            time_frame = self._normalize_time_frame(row.get("time_frame"))
            dt_start = self._to_date(row.get("dt_start"))
            dt_end = self._to_date(row.get("dt_end"))

            if time_frame == "day":
                continue

            if dt_start <= target_day <= dt_end:
                return row

        return None