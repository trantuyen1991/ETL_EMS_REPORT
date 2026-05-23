#!/usr/bin/env python3
"""Lightweight HTTP smoke checks for the machine-facing report API routes."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


REPORT_CASES = [
    ("daily", "2026-03-31"),
    ("weekly", "2026-03-29"),
    ("monthly", "2026-03-31"),
]


def fetch_json(base_url: str, path: str, *, expected_status: int, timeout: float) -> dict[str, Any]:
    """Fetch one JSON payload and enforce the expected HTTP status."""
    url = f"{base_url.rstrip('/')}{path}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        body = exc.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise AssertionError(f"Request failed for {url}: {exc}") from exc

    if status_code != expected_status:
        raise AssertionError(f"Unexpected status for {url}: expected {expected_status}, got {status_code}, body={body}")

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Non-JSON body returned from {url}: {body}") from exc


def assert_snapshot_payload(payload: dict[str, Any], *, period_type: str) -> None:
    """Validate one snapshot payload contract."""
    assert payload["meta"]["contract"] == {"name": "report_snapshot", "version": 2}
    assert payload["period"]["period_type"] == period_type
    assert isinstance(payload["availability"]["warning_count"], int)
    assert payload["artifacts"]["artifact_manifest_url"].startswith("/api/v1/report/artifacts?")

    for section_key in ("electricity", "utility", "kpi"):
        section = payload["sections"][section_key]
        assert section["section_key"] == section_key
        assert isinstance(section["card_count"], int)
        assert isinstance(section["table_count"], int)
        assert isinstance(section["chart_count"], int)
        assert section["card_count"] == len(section["cards"])
        assert section["table_count"] == len(section["tables"])
        assert section["chart_count"] == len(section["charts"])
        for table in section["tables"]:
            assert isinstance(table["columns"], list)
            assert table["row_count"] == len(table["rows"])
        for chart in section["charts"]:
            assert isinstance(chart["series_count"], int)
            assert chart["series_count"] == len(chart["series"])


def assert_artifact_payload(payload: dict[str, Any], *, period_type: str) -> None:
    """Validate one artifact manifest payload contract."""
    assert payload["meta"]["contract"] == {"name": "report_artifact_manifest", "version": 2}
    assert payload["period"]["period_type"] == period_type
    summary = payload["artifacts"]["summary"]
    assert summary["artifact_count"] >= 3
    assert summary["artifact_count"] == summary["available_count"] + summary["stale_count"] + summary["missing_count"]

    for artifact_key in ("interactive", "pdf_preview", "pdf_source_html", "zip_package"):
        artifact = payload["artifacts"][artifact_key]
        assert artifact["artifact_key"] == artifact_key
        assert artifact["status"] in {"available", "stale", "missing"}
        assert "artifact_type" in artifact
        assert "media_type" in artifact
        assert "filename" in artifact
        assert isinstance(artifact["exists"], bool)

    if period_type == "daily":
        assert "excel" in payload["artifacts"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the machine-facing report API routes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for the local Web GUI server.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    health = fetch_json(args.base_url, "/health", expected_status=200, timeout=args.timeout)
    assert health["status"] == "ok"

    for period_type, anchor_date in REPORT_CASES:
        query = urllib.parse.urlencode({
            "period_type": period_type,
            "anchor_date": anchor_date,
        })
        snapshot_payload = fetch_json(
            args.base_url,
            f"/api/v1/report/snapshot?{query}",
            expected_status=200,
            timeout=args.timeout,
        )
        assert_snapshot_payload(snapshot_payload, period_type=period_type)

        artifact_payload = fetch_json(
            args.base_url,
            f"/api/v1/report/artifacts?{query}",
            expected_status=200,
            timeout=args.timeout,
        )
        assert_artifact_payload(artifact_payload, period_type=period_type)

    invalid_payload = fetch_json(
        args.base_url,
        "/api/v1/report/snapshot?period_type=custom&anchor_date=2026-03-31",
        expected_status=400,
        timeout=args.timeout,
    )
    assert invalid_payload["status"] == "bad_request"

    invalid_artifact_payload = fetch_json(
        args.base_url,
        "/api/v1/report/artifacts?period_type=custom&anchor_date=2026-03-31",
        expected_status=400,
        timeout=args.timeout,
    )
    assert invalid_artifact_payload["status"] == "bad_request"

    print("PASS report API smoke checks")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL report API smoke checks: {exc}", file=sys.stderr)
        raise SystemExit(1)
