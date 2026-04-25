# -*- coding: utf-8 -*-

"""
PDF export service using Chrome headless.

Convert HTML file into PDF using Chrome/Edge.

Args:
    config: Application config dict.

Returns:
    PDFService instance.

Example:
    pdf_service = PDFService(config)
    pdf_service.export(html_path, pdf_path)
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PDFService:
    """
    Export PDF using Chrome headless.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def _find_browser(self) -> str:
        """
        Find Chrome/Edge executable path.
        Priority:
            1. browser_path from config
            2. auto-detect system browser

        Returns:
            Browser executable path.

        Raises:
            RuntimeError: If browser not found.
        """
        # 1. Check config override
        browser = self._config.get("config", {}).get("pdf", {}).get("browser_path")
        if browser:
            logger.info("Using browser from config: %s", browser)
            return browser
        # 2. Auto detect
        candidates = [
            "google-chrome",
            "chromium-browser",
            "chromium",
            "microsoft-edge",
            "msedge",
            "chrome",
        ]

        for cmd in candidates:
            try:
                subprocess.run([cmd, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Using browser: %s", cmd)
                return cmd
            except Exception:
                continue

        raise RuntimeError("No Chrome/Edge browser found on system.")

    def export(self, html_path: Path, output_pdf: Path) -> None:
        """
        Export HTML file to PDF.
        """
        try:
            output_pdf.parent.mkdir(parents=True, exist_ok=True)

            browser = self._find_browser()

            cmd = [
                browser,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--hide-scrollbars",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=45000",
                f"--print-to-pdf={str(output_pdf.resolve())}",
                f"file://{html_path.resolve()}",
            ]

            logger.info("Running PDF export command: %s", " ".join(cmd))

            result = subprocess.run(cmd, capture_output=True, text=True)

            print("PDF CMD:", " ".join(cmd))
            print("PDF RETURN CODE:", result.returncode)
            print("PDF STDOUT:", result.stdout)
            print("PDF STDERR:", result.stderr)

            if result.returncode != 0:
                logger.error("STDOUT: %s", result.stdout)
                logger.error("STDERR: %s", result.stderr)
                raise RuntimeError("PDF export failed.")

            if not output_pdf.exists():
                raise RuntimeError(
                    f"PDF export command finished but file was not created: {output_pdf}"
                )

            logger.info("Using browser: %s", browser)
            logger.info("PDF exported successfully: %s", output_pdf)

        except Exception as exc:
            logger.exception("Failed to export PDF.")
            raise RuntimeError("PDF export failed.") from exc
