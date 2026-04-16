# -*- coding: utf-8 -*-

"""
Logging utility module.

Provides:
- setup_logging(): initialize logging from YAML config
- get_logger(): get logger instance by name

Usage:
    from src.utils.logger import setup_logging, get_logger

    setup_logging(...)
    logger = get_logger(__name__)
"""

from __future__ import annotations

import logging
import logging.config
from pathlib import Path
from typing import Any

import yaml


def setup_logging(
    logging_config_path: str | Path,
    log_file_path: str | Path | None = None,
) -> None:
    """
    Initialize logging from YAML configuration.

    Args:
        logging_config_path: Path to logging YAML file.
        log_file_path: Optional override for log file location.

    Returns:
        None
    """
    config_path = Path(logging_config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Logging config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    # Override log file path if provided
    handlers = config.get("handlers", {})
    file_handler = handlers.get("file")

    if file_handler:
        if log_file_path:
            log_path = Path(log_file_path)
        else:
            log_path = Path(file_handler.get("filename", "logs/app.log"))

        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler["filename"] = str(log_path)

    logging.config.dictConfig(config)

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized successfully.")


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger
    """
    return logging.getLogger(name)