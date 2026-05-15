# -*- coding: utf-8 -*-
"""CLI entrypoint for the scheduled batch report flow.

This module intentionally stays thin so systemd/service-timer can keep using
`python -m src.main` while the shared execution path lives in ReportEngineService.
"""

from src.services.report_engine_service import ReportEngineService


def run_production() -> None:
    """Run production flow through the shared report engine service."""
    ReportEngineService().run_production()


if __name__ == "__main__":
    run_production()
