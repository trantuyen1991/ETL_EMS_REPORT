# -*- coding: utf-8 -*-

"""
Template rendering service for HTML report generation.

This module loads a Jinja2 HTML template and renders a report context
into a final HTML string that can later be exported to PDF.

Args:
    template_dir: Directory containing HTML templates.

Returns:
    TemplateRenderingService: Reusable rendering service instance.

Example:
    renderer = TemplateRenderingService(template_dir="src/templates")
    html = renderer.render("report_template.html", report_context)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape


from src.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateRenderingService:
    """
    Render report context into HTML using Jinja2 templates.

    Args:
        template_dir: Directory containing HTML templates.

    Returns:
        TemplateRenderingService: Rendering service instance.

    Example:
        renderer = TemplateRenderingService(template_dir="src/templates")
        html = renderer.render("report_template.html", {"title": "Energy Report"})
    """

    def __init__(self, template_dir: str | Path) -> None:
        """
        Initialize the template rendering service.

        Args:
            template_dir: Directory containing HTML templates.

        Returns:
            None

        Raises:
            FileNotFoundError: If the template directory does not exist.

        Example:
            renderer = TemplateRenderingService(template_dir="src/templates")
        """
        self._template_dir = Path(template_dir)

        if not self._template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self._template_dir}")

        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._env.globals["zip"] = zip

        logger.info("TemplateRenderingService initialized. template_dir=%s", self._template_dir)

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: HTML template filename.
            context: Report context data for rendering.

        Returns:
            str: Rendered HTML content.

        Raises:
            FileNotFoundError: If the template file does not exist.
            RuntimeError: If rendering fails.

        Example:
            html = renderer.render("report_template.html", report_context)
        """
        try:
            logger.info("Rendering template. template_name=%s", template_name)
            template = self._env.get_template(template_name)
            html = template.render(**context)
            logger.info("Template rendered successfully.")
            return html

        except TemplateNotFound as exc:
            logger.exception("Template not found. template_name=%s", template_name)
            raise FileNotFoundError(f"Template not found: {template_name}") from exc
        except Exception as exc:
            logger.exception("Failed to render template. template_name=%s", template_name)
            raise RuntimeError(f"Failed to render template: {template_name}") from exc