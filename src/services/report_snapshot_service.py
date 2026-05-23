# -*- coding: utf-8 -*-
"""Serializer for machine-facing report snapshot payloads."""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from src.models.period_models import ResolvedPeriod


class ReportSnapshotService:
    """Build stable machine-facing payloads from shared report context and artifacts."""

    def build_snapshot(
        self,
        *,
        period: ResolvedPeriod,
        report_context: dict[str, Any],
        cache_hit: bool,
        cache_fingerprint: str,
    ) -> dict[str, Any]:
        """Return a JSON-safe machine-facing report snapshot payload."""
        return {
            "meta": {
                "api_version": "v1",
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "report_generated_at": self._sanitize_json_value(report_context.get("generated_at")),
                "source": "report_engine_service",
                "cache": {
                    "hit": bool(cache_hit),
                    "fingerprint": str(cache_fingerprint or ""),
                },
            },
            "period": self._build_period_payload(period=period, report_context=report_context),
            "availability": self._build_availability_payload(report_context=report_context),
            "summary": self._build_summary_payload(report_context=report_context),
            "sections": self._build_sections_payload(report_context=report_context),
            "artifacts": self._build_artifact_payload(period=period),
        }

    def build_artifact_manifest(
        self,
        *,
        period: ResolvedPeriod,
        artifact_state: dict[str, Any],
        cache_fingerprint: str,
    ) -> dict[str, Any]:
        """Return one JSON-safe artifact manifest payload."""
        return {
            "meta": {
                "api_version": "v1",
                "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "source": "report_engine_service",
                "cache": {
                    "fingerprint": str(cache_fingerprint or ""),
                },
            },
            "period": self._build_period_payload(period=period, report_context={}),
            "artifacts": self._sanitize_json_value(artifact_state),
        }

    def _build_period_payload(
        self,
        *,
        period: ResolvedPeriod,
        report_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the canonical period payload."""
        context_period = report_context.get("period") if isinstance(report_context.get("period"), dict) else {}
        return {
            "period_type": str(period.period_type),
            "anchor_date": self._sanitize_json_value(getattr(period, "anchor_date", None)),
            "start_date": self._sanitize_json_value(period.start_date),
            "end_date": self._sanitize_json_value(period.end_date),
            "previous_start_date": self._sanitize_json_value(period.previous_start_date),
            "previous_end_date": self._sanitize_json_value(period.previous_end_date),
            "label": self._sanitize_json_value(period.label),
            "comparison_label": self._sanitize_json_value(period.comparison_label),
            "total_days": int(period.total_days),
            "current_period_title": self._sanitize_json_value(context_period.get("current_period_title")),
            "previous_period_title": self._sanitize_json_value(context_period.get("previous_period_title")),
        }

    def _build_availability_payload(self, *, report_context: dict[str, Any]) -> dict[str, Any]:
        """Build coarse availability and warning metadata."""
        summary = report_context.get("summary") if isinstance(report_context.get("summary"), dict) else {}
        kpi_section = ((report_context.get("sections") or {}).get("kpi") or {}) if isinstance(report_context.get("sections"), dict) else {}
        coverage_summary = summary.get("coverage") if isinstance(summary.get("coverage"), dict) else {}
        coverage_detail = kpi_section.get("coverage") if isinstance(kpi_section.get("coverage"), dict) else {}

        warnings: list[str] = []
        message = str(coverage_summary.get("message") or "").strip()
        coverage_note = str(coverage_detail.get("coverage_note") or "").strip()
        if bool(coverage_summary.get("has_warning")) and message:
            warnings.append(message)
        if coverage_note and coverage_note not in warnings:
            warnings.append(coverage_note)

        is_complete = bool(coverage_detail.get("is_complete"))
        uncovered_ranges = coverage_detail.get("uncovered_ranges")
        has_uncovered_ranges = bool(uncovered_ranges) if isinstance(uncovered_ranges, list) else False
        coverage_status = "complete" if is_complete else "partial" if (warnings or has_uncovered_ranges) else "unknown"

        return {
            "has_report": True,
            "coverage_status": coverage_status,
            "warnings": warnings,
        }

    def _build_summary_payload(self, *, report_context: dict[str, Any]) -> dict[str, Any]:
        """Build the top-level summary block."""
        summary = report_context.get("summary") if isinstance(report_context.get("summary"), dict) else {}
        return {
            "coverage": self._sanitize_json_value(summary.get("coverage") or {}),
            "electricity_snapshot": self._sanitize_json_value(summary.get("electricity_snapshot") or {}),
            "utility_snapshot_rows": self._sanitize_json_value(summary.get("utility_snapshot_rows") or []),
            "kpi_snapshot": self._sanitize_json_value(summary.get("kpi_snapshot") or {}),
            "kpi_area_snapshot_rows": self._sanitize_json_value(summary.get("kpi_area_snapshot_rows") or []),
        }

    def _build_sections_payload(self, *, report_context: dict[str, Any]) -> dict[str, Any]:
        """Build normalized section payloads."""
        sections = report_context.get("sections") if isinstance(report_context.get("sections"), dict) else {}
        electricity = sections.get("electricity") if isinstance(sections.get("electricity"), dict) else {}
        utility = sections.get("utility") if isinstance(sections.get("utility"), dict) else {}
        kpi = sections.get("kpi") if isinstance(sections.get("kpi"), dict) else {}

        return {
            "electricity": self._build_electricity_section(electricity),
            "utility": self._build_utility_section(utility),
            "kpi": self._build_kpi_section(kpi),
        }

    def _build_electricity_section(self, section: dict[str, Any]) -> dict[str, Any]:
        """Build the Electricity section payload."""
        cards: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []

        totals = section.get("totals") if isinstance(section.get("totals"), dict) else {}
        daily_summary = section.get("daily_summary") if isinstance(section.get("daily_summary"), dict) else {}
        top10 = section.get("top10") if isinstance(section.get("top10"), dict) else {}
        shutdown_analysis = section.get("shutdown_analysis") if isinstance(section.get("shutdown_analysis"), dict) else {}

        self._extend_cards(cards, totals.get("cards"), source_key="totals")
        self._append_rows_table(tables, table_key="daily_summary", title=daily_summary.get("title"), rows=daily_summary.get("rows"))
        self._append_rows_table(tables, table_key="daily_summary_by_area", title="Daily summary by area", rows=daily_summary.get("area_rows"))
        self._append_rows_table(tables, table_key="top10", title="Top 10 meters", rows=top10.get("rows"))
        self._append_named_table_list(tables, top10.get("area_tables"), source_key="top10_area")
        self._append_named_table_list(tables, section.get("daily_detail_tables"), source_key="daily_detail")
        self._append_named_table_list(tables, section.get("daily_vertical_detail_tables"), source_key="daily_vertical_detail")
        self._append_rows_table(tables, table_key="shutdown_analysis", title=shutdown_analysis.get("title") or "Shutdown analysis", rows=shutdown_analysis.get("rows"))

        return {
            "title": self._sanitize_json_value(section.get("title")),
            "subtitle": self._sanitize_json_value(section.get("subtitle")),
            "cards": cards,
            "tables": tables,
            "charts": self._deduplicate_charts(self._collect_chart_nodes(section.get("charts"), prefix="electricity")),
        }

    def _build_utility_section(self, section: dict[str, Any]) -> dict[str, Any]:
        """Build the Utility section payload."""
        cards: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []

        energy = section.get("energy") if isinstance(section.get("energy"), dict) else {}
        sensor_monitoring = section.get("sensor_monitoring") if isinstance(section.get("sensor_monitoring"), dict) else {}

        self._extend_cards(cards, energy.get("overview_cards"), source_key="energy_overview")
        self._extend_cards(cards, sensor_monitoring.get("overview_cards"), source_key="sensor_monitoring")

        self._append_rows_table(tables, table_key="utility_energy_detail", title=energy.get("title") or "Utility energy detail", rows=energy.get("detail_rows"))
        self._append_rows_table(tables, table_key="sensor_health_snapshot", title="Sensor health snapshot", rows=sensor_monitoring.get("health_snapshot"))
        self._append_rows_table(tables, table_key="sensor_top_issues", title="Sensor top issues", rows=sensor_monitoring.get("top_issues_preview"))
        self._append_rows_table(tables, table_key="sensor_anomaly_rows", title="Sensor anomaly rows", rows=sensor_monitoring.get("anomaly_rows"))
        self._append_rows_table(tables, table_key="sensor_daily_rows", title="Sensor daily rows", rows=sensor_monitoring.get("daily_rows"))
        self._append_named_table_list(tables, sensor_monitoring.get("period_detail_tables"), source_key="sensor_period_detail")

        charts = self._collect_chart_nodes(section.get("charts"), prefix="utility")
        charts.extend(self._collect_chart_nodes(energy.get("charts"), prefix="utility.energy"))
        charts.extend(self._collect_chart_nodes(sensor_monitoring.get("charts"), prefix="utility.sensor_monitoring"))

        return {
            "title": self._sanitize_json_value(section.get("title")),
            "subtitle": self._sanitize_json_value(section.get("subtitle")),
            "cards": cards,
            "tables": tables,
            "charts": self._deduplicate_charts(charts),
        }

    def _build_kpi_section(self, section: dict[str, Any]) -> dict[str, Any]:
        """Build the KPI section payload."""
        cards: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []

        chart_dashboard = ((section.get("charts") or {}).get("daily_dashboard") or {}) if isinstance(section.get("charts"), dict) else {}
        product_context = section.get("product_context") if isinstance(section.get("product_context"), dict) else {}
        summary_matrix = section.get("summary_matrix") if isinstance(section.get("summary_matrix"), dict) else {}
        daily_detail = section.get("daily_detail") if isinstance(section.get("daily_detail"), dict) else {}
        coverage = section.get("coverage") if isinstance(section.get("coverage"), dict) else {}

        self._extend_cards(cards, chart_dashboard.get("cards"), source_key="daily_dashboard")
        if not cards:
            self._extend_cards(cards, section.get("totals"), source_key="totals")

        self._append_rows_table(tables, table_key="kpi_summary_matrix", title=summary_matrix.get("title") or "KPI summary matrix", rows=summary_matrix.get("rows"))
        self._append_rows_table(tables, table_key="kpi_daily_detail", title=daily_detail.get("title") or "KPI daily detail", rows=daily_detail.get("rows"))
        self._append_rows_table(tables, table_key="kpi_product_context", title=product_context.get("title") or "Production context", rows=product_context.get("rows"))
        self._append_rows_table(tables, table_key="kpi_uncovered_ranges", title="KPI uncovered ranges", rows=coverage.get("uncovered_ranges"))

        return {
            "title": self._sanitize_json_value(section.get("title")),
            "subtitle": self._sanitize_json_value(section.get("subtitle")),
            "cards": cards,
            "tables": tables,
            "charts": self._deduplicate_charts(self._collect_chart_nodes(section.get("charts"), prefix="kpi")),
        }

    def _build_artifact_payload(self, *, period: ResolvedPeriod) -> dict[str, str]:
        """Build URLs for human-facing report artifacts."""
        query = {
            "period_type": str(period.period_type),
        }
        anchor_date = getattr(period, "anchor_date", None)
        if anchor_date is not None:
            query["anchor_date"] = anchor_date.isoformat()

        interactive_query = dict(query)
        interactive_query.update({
            "template_mode": "view",
            "_embed": "1",
        })

        pdf_query = dict(query)
        pdf_query["template_mode"] = "pdf_source"

        return {
            "interactive_url": f"/reports?{urlencode(interactive_query)}",
            "pdf_preview_url": f"/reports/preview-pdf?{urlencode(pdf_query)}",
            "zip_download_url": f"/reports/download-zip?{urlencode(query)}",
        }

    def _collect_chart_nodes(self, node: Any, *, prefix: str) -> list[dict[str, Any]]:
        """Collect chart descriptors recursively from one context branch."""
        collected: list[dict[str, Any]] = []

        if isinstance(node, dict):
            option = node.get("option")
            if isinstance(option, dict):
                collected.append(self._serialize_chart_node(chart_key=prefix, chart_node=node))
                return collected

            for child_key, child_value in node.items():
                if not isinstance(child_value, (dict, list)):
                    continue
                next_prefix = f"{prefix}.{child_key}" if prefix else str(child_key)
                collected.extend(self._collect_chart_nodes(child_value, prefix=next_prefix))
        elif isinstance(node, list):
            for index, item in enumerate(node):
                next_prefix = f"{prefix}.{index}" if prefix else str(index)
                collected.extend(self._collect_chart_nodes(item, prefix=next_prefix))

        return collected

    def _serialize_chart_node(self, *, chart_key: str, chart_node: dict[str, Any]) -> dict[str, Any]:
        """Serialize one chart node into a renderer-agnostic schema."""
        option = chart_node.get("option") if isinstance(chart_node.get("option"), dict) else {}
        x_axis = self._extract_axis_values(option.get("xAxis"))
        legend = self._extract_legend(option.get("legend"), option.get("series"))
        series_payload = self._serialize_chart_series(option.get("series"), has_x_axis=bool(x_axis.get("values")))
        first_series = series_payload[0] if series_payload else {}

        notes: list[str] = []
        for key in ("note", "notes"):
            value = chart_node.get(key)
            if isinstance(value, str) and value.strip():
                notes.append(value.strip())
            elif isinstance(value, list):
                notes.extend(str(item).strip() for item in value if str(item).strip())

        return {
            "chart_key": str(chart_key),
            "chart_type": str(first_series.get("style") or first_series.get("chart_type") or "unknown"),
            "title": self._sanitize_json_value(chart_node.get("title")),
            "subtitle": self._sanitize_json_value(chart_node.get("subtitle")),
            "x_axis": x_axis,
            "series": series_payload,
            "legend": legend,
            "notes": notes,
        }

    def _serialize_chart_series(self, raw_series: Any, *, has_x_axis: bool) -> list[dict[str, Any]]:
        """Serialize one list of chart series entries."""
        if not isinstance(raw_series, list):
            return []

        serialized: list[dict[str, Any]] = []
        for index, item in enumerate(raw_series):
            if not isinstance(item, dict):
                continue

            label = str(item.get("name") or f"series_{index + 1}")
            data = item.get("data") if isinstance(item.get("data"), list) else []
            points = self._build_series_points(data)
            entry = {
                "key": str(item.get("id") or item.get("key") or label.lower().replace(" ", "_")),
                "label": label,
                "style": self._sanitize_json_value(item.get("type") or "unknown"),
                "axis": "secondary" if int(item.get("yAxisIndex") or 0) > 0 else "primary",
            }

            if has_x_axis:
                entry["values"] = [point.get("value") for point in points]
            else:
                entry["points"] = points

            if "stack" in item:
                entry["stack"] = self._sanitize_json_value(item.get("stack"))
            serialized.append(entry)

        return serialized

    def _build_series_points(self, data: list[Any]) -> list[dict[str, Any]]:
        """Normalize one chart-series data list into label/value pairs."""
        points: list[dict[str, Any]] = []
        for index, item in enumerate(data):
            if isinstance(item, dict):
                points.append({
                    "label": self._sanitize_json_value(item.get("name") or item.get("label") or str(index + 1)),
                    "value": self._sanitize_json_value(item.get("value")),
                })
                continue

            if isinstance(item, (list, tuple)) and len(item) >= 2:
                points.append({
                    "label": self._sanitize_json_value(item[0]),
                    "value": self._sanitize_json_value(item[1]),
                })
                continue

            points.append({
                "label": str(index + 1),
                "value": self._sanitize_json_value(item),
            })
        return points

    def _extract_axis_values(self, raw_axis: Any) -> dict[str, Any]:
        """Extract a normalized x-axis payload."""
        axis = raw_axis[0] if isinstance(raw_axis, list) and raw_axis else raw_axis
        if not isinstance(axis, dict):
            return {
                "label": "",
                "values": [],
            }

        values = axis.get("data") if isinstance(axis.get("data"), list) else []
        return {
            "label": self._sanitize_json_value(axis.get("name") or ""),
            "values": self._sanitize_json_value(values),
        }

    def _extract_legend(self, raw_legend: Any, raw_series: Any) -> list[str]:
        """Extract legend labels from the chart option."""
        legend = raw_legend[0] if isinstance(raw_legend, list) and raw_legend else raw_legend
        if isinstance(legend, dict) and isinstance(legend.get("data"), list):
            return [str(item) for item in legend.get("data") if str(item).strip()]

        labels: list[str] = []
        if isinstance(raw_series, list):
            for item in raw_series:
                if not isinstance(item, dict):
                    continue
                label = str(item.get("name") or "").strip()
                if label and label not in labels:
                    labels.append(label)
        return labels

    def _extend_cards(self, target: list[dict[str, Any]], raw_cards: Any, *, source_key: str) -> None:
        """Append normalized card entries from dict/list shapes."""
        if isinstance(raw_cards, list):
            for index, item in enumerate(raw_cards):
                card = self._serialize_card(item, fallback_key=f"{source_key}_{index + 1}")
                if card:
                    target.append(card)
            return

        if isinstance(raw_cards, dict):
            if self._looks_like_card(raw_cards):
                card = self._serialize_card(raw_cards, fallback_key=source_key)
                if card:
                    target.append(card)
                return

            for item_key, item_value in raw_cards.items():
                if not isinstance(item_value, dict):
                    continue
                card = self._serialize_card(item_value, fallback_key=str(item_key))
                if card:
                    target.append(card)

    def _serialize_card(self, raw_card: Any, *, fallback_key: str) -> dict[str, Any] | None:
        """Serialize one card object when it looks card-like enough."""
        if not isinstance(raw_card, dict):
            return None
        if not self._looks_like_card(raw_card):
            return None

        payload = self._sanitize_json_value(raw_card)
        if isinstance(payload, dict):
            payload.setdefault("card_key", str(payload.get("key") or fallback_key))
            return payload
        return None

    def _looks_like_card(self, raw_card: dict[str, Any]) -> bool:
        """Return True when one dict looks like a card payload."""
        card_markers = {
            "label",
            "value_display",
            "current_display",
            "badge_label",
            "delta_display",
            "is_total",
        }
        return any(marker in raw_card for marker in card_markers)

    def _append_rows_table(
        self,
        target: list[dict[str, Any]],
        *,
        table_key: str,
        title: Any,
        rows: Any,
    ) -> None:
        """Append one normalized table when rows are present."""
        if not isinstance(rows, list) or not rows:
            return

        target.append({
            "table_key": str(table_key),
            "title": self._sanitize_json_value(title or table_key.replace("_", " ").title()),
            "row_count": len(rows),
            "rows": self._sanitize_json_value(rows),
        })

    def _append_named_table_list(
        self,
        target: list[dict[str, Any]],
        raw_tables: Any,
        *,
        source_key: str,
    ) -> None:
        """Append table descriptors from a list of named table blocks."""
        if not isinstance(raw_tables, list):
            return

        for index, item in enumerate(raw_tables):
            if not isinstance(item, dict):
                continue
            rows = item.get("rows") if isinstance(item.get("rows"), list) else []
            if not rows:
                continue
            table_key = str(item.get("key") or item.get("table_key") or f"{source_key}_{index + 1}")
            title = item.get("title") or item.get("label") or table_key.replace("_", " ").title()
            target.append({
                "table_key": table_key,
                "title": self._sanitize_json_value(title),
                "row_count": len(rows),
                "rows": self._sanitize_json_value(rows),
            })

    def _deduplicate_charts(self, charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop duplicate chart keys while preserving order."""
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for chart in charts:
            chart_key = str(chart.get("chart_key") or "").strip()
            if not chart_key or chart_key in seen:
                continue
            seen.add(chart_key)
            unique.append(chart)
        return unique

    def _sanitize_json_value(self, value: Any) -> Any:
        """Convert nested context values into JSON-safe payloads."""
        if value is None or isinstance(value, (str, bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {
                str(key): self._sanitize_json_value(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [self._sanitize_json_value(item) for item in value]
        return str(value)
