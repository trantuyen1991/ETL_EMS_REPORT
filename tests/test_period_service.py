from __future__ import annotations

from datetime import date

from src.models.period_models import PeriodRequest
from src.services.period_service import PeriodService


def test_resolve_scheduled_periods_includes_daily_weekly_monthly_on_sunday_month_end() -> None:
    service = PeriodService()
    config = {
        "env": {"REPORT_ANCHOR_DATE": "2025-08-31"},
        "config": {"report": {"include": {"daily": True, "weekly": True, "monthly": True}}},
    }

    periods = service.resolve_scheduled_periods_from_config(config)

    assert [period.period_type for period in periods] == ["daily", "weekly", "monthly"]
    assert all(period.anchor_date == date(2025, 8, 31) for period in periods)


def test_resolve_custom_period_builds_previous_block_with_same_duration() -> None:
    service = PeriodService()

    period = service.resolve(
        PeriodRequest(
            period_type="custom",
            custom_start_date=date(2025, 4, 10),
            custom_end_date=date(2025, 4, 12),
        )
    )

    assert period.start_date == date(2025, 4, 10)
    assert period.end_date == date(2025, 4, 12)
    assert period.total_days == 3
    assert period.previous_start_date == date(2025, 4, 7)
    assert period.previous_end_date == date(2025, 4, 9)
    assert period.anchor_date == date(2025, 4, 12)


def test_resolve_from_config_rejects_custom_period_without_dates() -> None:
    service = PeriodService()
    config = {
        "env": {
            "REPORT_PERIOD_TYPE": "custom",
            "REPORT_CUSTOM_START_DATE": "2025-04-10",
            "REPORT_CUSTOM_END_DATE": "",
        }
    }

    try:
        service.resolve_from_config(config)
    except ValueError as exc:
        assert "REPORT_CUSTOM_START_DATE and REPORT_CUSTOM_END_DATE" in str(exc)
    else:
        raise AssertionError("Expected ValueError for incomplete custom period config")
