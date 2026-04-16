# -*- coding: utf-8 -*-

"""
CSV export service for raw report detail rows.

This module exports raw detail rows to a CSV file so the PDF report can
stay clean while full source-level data remains available separately.

Args:
    None

Returns:
    CsvExportService: Reusable CSV export service.

Example:
    exporter = CsvExportService()
    exporter.export_rows(rows, "/tmp/raw_detail.csv")
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class CsvExportService:
    """
    Export raw detail rows to CSV.

    Returns:
        CsvExportService: CSV export service instance.

    Example:
        exporter = CsvExportService()
        output_path = exporter.export_rows(rows, "output/reports/raw_detail.csv")
    """

    def export_rows(
        self,
        rows: list[dict[str, Any]],
        output_path: str | Path,
    ) -> Path:
        """
        Export rows to CSV.

        Args:
            rows: Raw detail rows to export.
            output_path: Target CSV file path.

        Returns:
            Path: Final CSV file path.

        Raises:
            ValueError: If rows are empty.
            RuntimeError: If export fails.

        Example:
            exporter.export_rows(rows, "output/reports/report_raw_detail.csv")
        """
        if not rows:
            raise ValueError("Cannot export CSV because rows are empty.")

        final_path = Path(output_path)
        final_path.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = list(rows[0].keys())

        try:
            with final_path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    sanitized_row = {
                        key: (0 if value is None else value)
                        for key, value in row.items()
                    }
                    writer.writerow(sanitized_row)

            return final_path

        except Exception as exc:
            raise RuntimeError(f"Failed to export CSV file: {final_path}") from exc