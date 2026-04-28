# -*- coding: utf-8 -*-

"""
PDF export service using Chrome headless.

Primary path:
- launch Chrome/Chromium with remote debugging enabled
- control printing through Chrome DevTools Protocol `Page.printToPDF`
- lock important print parameters such as `scale` and `preferCSSPageSize`

Fallback path:
- use legacy `--print-to-pdf` CLI mode when CDP printing fails
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class _CDPWebSocketClient:
    """Very small WebSocket client for Chrome DevTools Protocol."""

    def __init__(self, websocket_url: str, timeout: float = 10.0) -> None:
        self._url = websocket_url
        self._timeout = timeout
        self._sock = self._connect()
        self._next_id = 0

    def _connect(self) -> socket.socket:
        parsed = urllib.parse.urlparse(self._url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        raw_sock = socket.create_connection((host, port), timeout=self._timeout)
        raw_sock.settimeout(self._timeout)

        if parsed.scheme == "wss":
            context = ssl.create_default_context()
            sock: socket.socket = context.wrap_socket(raw_sock, server_hostname=host)
        else:
            sock = raw_sock

        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("ascii"))

        response = self._read_http_response(sock)
        status_line, _, header_block = response.partition("\r\n")
        if "101" not in status_line:
            raise RuntimeError(f"WebSocket handshake failed: {status_line}")

        headers: dict[str, str] = {}
        for line in header_block.split("\r\n"):
            if not line or ":" not in line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()

        expected_accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        actual_accept = headers.get("sec-websocket-accept", "")
        if actual_accept != expected_accept:
            raise RuntimeError("WebSocket handshake validation failed.")

        return sock

    def _read_http_response(self, sock: socket.socket) -> str:
        buffer = bytearray()
        while b"\r\n\r\n" not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer.extend(chunk)
        return buffer.decode("utf-8", errors="replace")

    def _recv_exact(self, length: int) -> bytes:
        data = bytearray()
        while len(data) < length:
            chunk = self._sock.recv(length - len(data))
            if not chunk:
                raise RuntimeError("WebSocket connection closed unexpectedly.")
            data.extend(chunk)
        return bytes(data)

    def _send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        frame = bytearray()
        frame.append(0x81)

        payload_length = len(payload)
        mask_key = os.urandom(4)

        if payload_length <= 125:
            frame.append(0x80 | payload_length)
        elif payload_length <= 65535:
            frame.append(0x80 | 126)
            frame.extend(payload_length.to_bytes(2, "big"))
        else:
            frame.append(0x80 | 127)
            frame.extend(payload_length.to_bytes(8, "big"))

        frame.extend(mask_key)
        masked = bytes(b ^ mask_key[index % 4] for index, b in enumerate(payload))
        frame.extend(masked)
        self._sock.sendall(frame)

    def _recv_text(self, timeout: float | None = None) -> str:
        if timeout is not None:
            self._sock.settimeout(timeout)

        fragments: list[bytes] = []

        while True:
            header = self._recv_exact(2)
            first_byte, second_byte = header[0], header[1]
            opcode = first_byte & 0x0F
            is_final = bool(first_byte & 0x80)
            is_masked = bool(second_byte & 0x80)
            payload_length = second_byte & 0x7F

            if payload_length == 126:
                payload_length = int.from_bytes(self._recv_exact(2), "big")
            elif payload_length == 127:
                payload_length = int.from_bytes(self._recv_exact(8), "big")

            mask_key = self._recv_exact(4) if is_masked else b""
            payload = self._recv_exact(payload_length) if payload_length else b""

            if is_masked:
                payload = bytes(b ^ mask_key[index % 4] for index, b in enumerate(payload))

            if opcode == 0x8:
                raise RuntimeError("WebSocket closed by remote peer.")
            if opcode == 0x9:
                self._send_pong(payload)
                continue
            if opcode == 0xA:
                continue
            if opcode not in (0x0, 0x1):
                continue

            fragments.append(payload)
            if is_final:
                return b"".join(fragments).decode("utf-8")

    def _send_pong(self, payload: bytes) -> None:
        frame = bytearray()
        frame.append(0x8A)
        mask_key = os.urandom(4)
        payload_length = len(payload)

        if payload_length <= 125:
            frame.append(0x80 | payload_length)
        elif payload_length <= 65535:
            frame.append(0x80 | 126)
            frame.extend(payload_length.to_bytes(2, "big"))
        else:
            frame.append(0x80 | 127)
            frame.extend(payload_length.to_bytes(8, "big"))

        frame.extend(mask_key)
        frame.extend(bytes(b ^ mask_key[index % 4] for index, b in enumerate(payload)))
        self._sock.sendall(frame)

    def send_command(self, method: str, params: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
        self._next_id += 1
        message_id = self._next_id
        payload = {
            "id": message_id,
            "method": method,
            "params": params or {},
        }
        self._send_text(json.dumps(payload))

        while True:
            response = json.loads(self._recv_text(timeout=timeout))
            if response.get("id") != message_id:
                continue
            if "error" in response:
                raise RuntimeError(f"CDP command failed: {response['error']}")
            return response

    def close(self) -> None:
        try:
            frame = bytearray([0x88, 0x80])
            frame.extend(os.urandom(4))
            self._sock.sendall(frame)
        except Exception:
            pass
        try:
            self._sock.close()
        except Exception:
            pass


class PDFService:
    """Export PDF using Chrome headless."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    def _find_browser(self) -> str:
        """Find Chrome/Edge executable path."""
        browser = self._config.get("config", {}).get("pdf", {}).get("browser_path")
        if browser:
            logger.info("Using browser from config: %s", browser)
            return browser

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

    def _allocate_debug_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _launch_debug_browser(self, browser: str, port: int, profile_dir: str) -> subprocess.Popen[str]:
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-extensions",
            "--run-all-compositor-stages-before-draw",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile_dir}",
            f"--remote-debugging-port={port}",
            "about:blank",
        ]
        logger.debug("Launching Chrome DevTools PDF session: %s", " ".join(cmd))
        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def _get_page_target(self, port: int, timeout_seconds: float = 10.0) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        url = f"http://127.0.0.1:{port}/json/list"

        while time.time() < deadline:
            try:
                with urllib.request.urlopen(url, timeout=2.0) as response:
                    targets = json.loads(response.read().decode("utf-8"))
                for target in targets:
                    if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return target
            except (urllib.error.URLError, json.JSONDecodeError):
                time.sleep(0.1)
                continue
            time.sleep(0.1)

        raise RuntimeError("Timed out waiting for Chrome DevTools page target.")

    def _wait_for_ready(self, client: _CDPWebSocketClient, timeout_seconds: float = 60.0) -> None:
        deadline = time.time() + timeout_seconds
        expression = """
            JSON.stringify({
                readyState: document.readyState,
                windowStatus: window.status || "",
                bodyWidth: document.body ? document.body.getBoundingClientRect().width : 0,
                scrollWidth: document.documentElement ? document.documentElement.scrollWidth : 0
            })
        """

        last_state: dict[str, Any] | None = None

        while time.time() < deadline:
            response = client.send_command(
                "Runtime.evaluate",
                {
                    "expression": expression,
                    "returnByValue": True,
                },
                timeout=5.0,
            )
            value = response.get("result", {}).get("result", {}).get("value")
            if isinstance(value, str):
                try:
                    last_state = json.loads(value)
                except json.JSONDecodeError:
                    last_state = None

            if last_state and last_state.get("readyState") == "complete" and last_state.get("windowStatus") == "ready":
                logger.info(
                    "PDF page ready for print. body_width=%s scroll_width=%s",
                    last_state.get("bodyWidth"),
                    last_state.get("scrollWidth"),
                )
                return

            time.sleep(0.25)

        raise RuntimeError(f"Timed out waiting for page readiness. last_state={last_state}")

    def _build_print_options(self) -> dict[str, Any]:
        pdf_cfg = self._config.get("config", {}).get("pdf", {})
        orientation = str(pdf_cfg.get("orientation") or "portrait").strip().lower()
        landscape = orientation == "landscape"

        return {
            "landscape": landscape,
            "printBackground": True,
            "preferCSSPageSize": True,
            "scale": 1.0,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "transferMode": "ReturnAsBase64",
        }

    def _export_via_cdp(self, browser: str, html_path: Path, output_pdf: Path) -> None:
        html_url = html_path.resolve().as_uri()
        debug_port = self._allocate_debug_port()

        with tempfile.TemporaryDirectory(prefix="report-pdf-browser-") as profile_dir:
            process = self._launch_debug_browser(browser=browser, port=debug_port, profile_dir=profile_dir)
            client: _CDPWebSocketClient | None = None

            try:
                target = self._get_page_target(debug_port)
                client = _CDPWebSocketClient(target["webSocketDebuggerUrl"], timeout=10.0)

                client.send_command("Page.enable")
                client.send_command("Runtime.enable")
                client.send_command(
                    "Emulation.setEmulatedMedia",
                    {"media": "print"},
                )
                client.send_command(
                    "Page.navigate",
                    {"url": html_url},
                )

                self._wait_for_ready(client)

                pdf_response = client.send_command(
                    "Page.printToPDF",
                    self._build_print_options(),
                    timeout=60.0,
                )
                pdf_base64 = pdf_response.get("result", {}).get("data")
                if not pdf_base64:
                    raise RuntimeError("CDP print returned empty PDF data.")

                output_pdf.write_bytes(base64.b64decode(pdf_base64))
            finally:
                if client is not None:
                    client.close()
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    def _export_via_legacy_cli(self, browser: str, html_path: Path, output_pdf: Path) -> None:
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=45000",
            "--window-status=ready",
            f"--print-to-pdf={str(output_pdf.resolve())}",
            f"file://{html_path.resolve()}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.debug("Legacy PDF export command: %s", " ".join(cmd))
            logger.error("STDOUT: %s", result.stdout)
            logger.error("STDERR: %s", result.stderr)
            raise RuntimeError("Legacy PDF export failed.")

    def export(self, html_path: Path, output_pdf: Path) -> None:
        """Export HTML file to PDF."""
        try:
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            browser = self._find_browser()

            try:
                self._export_via_cdp(browser=browser, html_path=html_path, output_pdf=output_pdf)
                if not output_pdf.exists():
                    raise RuntimeError(f"CDP export finished but file was not created: {output_pdf}")
                logger.info("PDF exported successfully via CDP: %s", output_pdf)
                return
            except Exception as exc:
                logger.warning("CDP PDF export failed, falling back to legacy CLI mode: %s", exc)

            self._export_via_legacy_cli(browser=browser, html_path=html_path, output_pdf=output_pdf)

            if not output_pdf.exists():
                raise RuntimeError(
                    f"PDF export command finished but file was not created: {output_pdf}"
                )

            logger.info("Using browser: %s", browser)
            logger.info("PDF exported successfully via legacy CLI: %s", output_pdf)

        except Exception as exc:
            logger.exception("Failed to export PDF.")
            raise RuntimeError("PDF export failed.") from exc
