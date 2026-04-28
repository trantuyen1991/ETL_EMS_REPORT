# -*- coding: utf-8 -*-

"""Style configuration service for inline report presentation tokens.

This service loads the centralized JSON style config, applies safe defaults,
validates the minimum required shape, and builds render-ready inline CSS
variables plus inline ECharts theme context.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


DEFAULT_REPORT_STYLE: dict[str, Any] = {
    "meta": {
        "name": "default",
        "version": "1.0.0",
        "description": "Central presentation tokens for the current report system.",
    },
    "font": {
        "family": "Arial, Helvetica, sans-serif",
        "sizeBase": "12px",
        "sizeSmall": "11px",
        "sizeLarge": "13px",
        "sizeTitle": "24px",
        "sizeSectionTitle": "18px",
        "sizeSectionSubtitle": "12px",
        "weightNormal": "400",
        "weightMedium": "500",
        "weightSemibold": "600",
        "weightBold": "700",
        "lineHeightBase": "1.5",
        "lineHeightDense": "1.35",
    },
    "color": {
        "pageBackground": "#f4f6f8",
        "cardBackground": "#ffffff",
        "headerBackground": "#f8fafc",
        "headerBackgroundStrong": "#f3f4f6",
        "tableStripeBackground": "#fafafa",
        "tableHeaderBackground": "#f8fafc",
        "textPrimary": "#1f2937",
        "textHeading": "#111827",
        "textMuted": "#6b7280",
        "textSubtle": "#64748b",
        "textInverse": "#ffffff",
        "borderDefault": "#d1d5db",
        "borderSoft": "#d9e1ea",
        "borderRow": "#e5e7eb",
        "brandPrimary": "#2563eb",
        "brandAccent": "#7c3aed",
        "trendUp": "#0f7b35",
        "trendDown": "#b42318",
        "trendNeutral": "#666666",
        "statusSuccess": "#0f7b35",
        "statusSuccessBackground": "#dcfce7",
        "statusWarning": "#b45309",
        "statusWarningBackground": "#fef3c7",
        "statusDanger": "#b42318",
        "statusDangerBackground": "#fee2e2",
        "statusNeutral": "#6b7280",
        "statusNeutralBackground": "#f3f4f6",
    },
    "layout": {
        "pageMaxWidth": "1480px",
        "pagePadding": "0",
        "cardPadding": "16px",
        "cardGap": "16px",
        "sectionMarginTop": "24px",
        "tableCellPadding": "8px 10px",
        "tableCellPaddingDense": "4px 6px",
        "chartHeightDefault": "320px",
        "chartHeightCompact": "260px",
    },
    "radius": {
        "medium": "8px",
        "large": "10px",
        "pill": "999px",
    },
    "shadow": {
        "soft": "0 10px 24px rgba(15, 23, 42, 0.05)",
        "card": "0 4px 12px rgba(15, 23, 42, 0.04)",
    },
    "spacing": {
        "xs": "4px",
        "sm": "8px",
        "md": "12px",
        "lg": "16px",
        "xl": "24px",
    },
    "components": {
        "page": {
            "background": "#f4f6f8",
            "textColor": "#1f2937",
        },
        "reportContainer": {
            "maxWidth": "1480px",
        },
        "reportTitle": {
            "fontSize": "24px",
            "fontWeight": "700",
            "color": "#111827",
            "letterSpacing": "0",
        },
        "reportSubtitle": {
            "fontSize": "12px",
            "fontWeight": "500",
            "color": "#64748b",
        },
        "reportMetadata": {
            "fontSize": "11px",
            "fontWeight": "500",
            "color": "#6b7280",
        },
        "reportHeader": {
            "background": {
                "width": "100%",
                "height": "100%",
                "objectFit": "cover",
                "objectPosition": "center center",
            },
            "overlay": {
                "minHeight": "132px",
                "gridTemplateColumns": "420px minmax(0, 1fr)",
                "padding": "0 300px 0 0",
            },
            "logoSlot": {
                "alignItems": "center",
                "justifyContent": "flex-start",
                "paddingLeft": "34px",
            },
            "logoCrop": {
                "width": "202px",
                "height": "36px",
            },
            "pdf": {
                "overlay": {
                    "minHeight": "122px",
                    "gridTemplateColumns": "330px minmax(0, 1fr)",
                    "padding": "0 182px 0 0",
                },
                "logoSlot": {
                    "paddingLeft": "22px",
                },
                "logoCrop": {
                    "width": "140px",
                    "height": "24px",
                },
            },
        },
        "sectionHeader": {
            "titleFontSize": "18px",
            "titleFontWeight": "700",
            "titleColor": "#111827",
            "subtitleFontSize": "12px",
            "subtitleColor": "#64748b",
            "background": "#f8fafc",
            "borderColor": "#d1d5db",
            "accentColor": "#2563eb",
        },
        "card": {
            "background": "#ffffff",
            "borderColor": "#d1d5db",
            "borderRadius": "10px",
            "padding": "16px",
            "shadow": "0 4px 12px rgba(15, 23, 42, 0.04)",
        },
        "table": {
            "headerBackground": "#f8fafc",
            "stripeBackground": "#fafafa",
            "borderColor": "#e5e7eb",
            "textColor": "#1f2937",
            "headerTextColor": "#111827",
            "cellPadding": "8px 10px",
            "denseCellPadding": "4px 6px",
        },
        "statusBadge": {
            "success": {
                "textColor": "#0f7b35",
                "background": "#dcfce7",
                "borderColor": "#86efac",
            },
            "warning": {
                "textColor": "#b45309",
                "background": "#fef3c7",
                "borderColor": "#fcd34d",
            },
            "danger": {
                "textColor": "#b42318",
                "background": "#fee2e2",
                "borderColor": "#fca5a5",
            },
            "neutral": {
                "textColor": "#6b7280",
                "background": "#f3f4f6",
                "borderColor": "#d1d5db",
            },
            "info": {
                "textColor": "#0369a1",
                "background": "#e0f2fe",
                "borderColor": "#bae6fd",
            },
        },
        "badge": {
            "textColor": "#475569",
            "background": "#e2e8f0",
            "borderColor": "#cbd5e1",
            "fontSize": "10px",
            "fontWeight": "800",
        },
        "trend": {
            "up": {"color": "#0f7b35"},
            "down": {"color": "#b42318"},
            "neutral": {"color": "#666666"},
        },
        "coverageNotice": {
            "background": "#f8fafc",
            "borderColor": "#d9e1ea",
            "textColor": "#64748b",
        },
        "footer": {
            "textColor": "#6b7280",
            "borderColor": "#d1d5db",
        },
        "chartCard": {
            "background": "#ffffff",
            "borderColor": "#d9e1ea",
            "borderRadius": "10px",
            "padding": "16px",
            "height": "320px",
            "titleColor": "#111827",
            "subtitleColor": "#64748b",
        },
        "chartNote": {
            "fontSize": "12px",
            "fontWeight": "500",
            "textColor": "#64748b",
        },
        "chartLegend": {
            "fontSize": "11px",
            "fontWeight": "700",
            "textColor": "#64748b",
            "itemGap": "8px",
        },
        "chartMeta": {
            "valueColor": "#0f172a",
            "textColor": "#334155",
            "subtleColor": "#64748b",
            "labelFontSize": "11px",
            "smallFontSize": "9px",
        },
        "chartLayout": {
            "gridGap": "12px",
            "subtitleMarginBottom": "10px",
            "noteMarginTop": "10px",
        },
        "chartHeights": {
            "view": {
                "electricity": {
                    "base": "340px",
                    "periodicBase": "356px",
                    "periodicWeeklyPrimary": "392px",
                    "heatmapBase": "228px",
                    "periodicWeeklySecondary": "252px",
                    "periodicDelta": "252px",
                },
                "utility": {
                    "comparison": "272px",
                    "periodTrend": "326px",
                    "splitSecondary": "292px",
                    "energy": "308px",
                    "sensorTrend": "220px",
                },
                "kpi": {
                    "dashboard": "288px",
                },
            },
            "pdfBase": {
                "electricity": {
                    "base": "384px",
                    "periodicBase": "364px",
                    "periodicWeeklyPrimary": "404px",
                    "heatmapBase": "228px",
                    "periodicWeeklySecondary": "258px",
                    "periodicDelta": "252px",
                },
                "utility": {
                    "comparison": "214px",
                    "periodTrend": "274px",
                    "splitSecondary": "230px",
                    "energy": "272px",
                    "sensorTrend": "220px",
                },
                "kpi": {
                    "dashboard": "288px",
                },
            },
            "pdfCompact": {
                "electricity": {
                    "base": "216px",
                    "periodicBase": "224px",
                    "periodicWeeklyPrimary": "244px",
                    "heatmapBase": "156px",
                    "periodicWeeklySecondary": "184px",
                    "periodicDelta": "178px",
                },
                "utility": {
                    "comparison": "168px",
                    "periodTrend": "228px",
                    "splitSecondary": "186px",
                    "energy": "220px",
                    "sensorTrend": "156px",
                    "sensorTrendSingle": "142px",
                },
                "kpi": {
                    "dashboard": "196px",
                },
            },
        },
        "sections": {
            "electricity": {
                "charts": {
                    "dailyTrend": {
                        "grid": {"left": 26, "right": 12, "top": 36, "bottom": 46, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "areaComparison": {
                        "grid": {"left": 32, "right": 12, "top": 56, "bottom": 38, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "areaShare": {
                        "legend": {"top": "center"}
                    },
                    "periodAreaDelta": {
                        "grid": {"left": 72, "right": 22, "top": 8, "bottom": 10, "containLabel": False}
                    },
                    "periodHeatmap": {
                        "default": {
                            "grid": {"left": 58, "right": 18, "top": 10, "bottom": 44, "containLabel": False}
                        },
                        "dense": {
                            "grid": {"left": 58, "right": 18, "top": 10, "bottom": 62, "containLabel": False}
                        },
                        "monthly": {
                            "grid": {"left": 18, "right": 18, "top": 10, "bottom": 62, "containLabel": False}
                        }
                    },
                    "monthly": {
                        "trend": {"height": "262px"},
                        "areaComparison": {"height": "174px"},
                        "heatmap": {"height": "192px"},
                        "delta": {"height": "178px"}
                    }
                }
            },
            "utility": {
                "charts": {
                    "comparison": {
                        "grid": {"left": 28, "right": 10, "top": 42, "bottom": 32, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "typeTrend": {
                        "grid": {"left": 32, "right": 10, "top": 36, "bottom": 46, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "mix": {
                        "legend": {"bottom": "center"}
                    },
                    "deviation": {
                        "grid": {"left": 118, "right": 24, "top": 18, "bottom": 28}
                    },
                    "energyTrend": {
                        "grid": {"left": 18, "right": 12, "top": 44, "bottom": 52, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "periodSensorTrend": {
                        "grid": {"left": 20, "right": 16, "top": 54, "bottom": 30, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "sensorCluster": {
                        "grid": {"left": 38, "right": 14, "top": 38, "bottom": 28, "containLabel": True},
                        "legend": {"top": "left"}
                    }
                }
            },
            "kpi": {
                "charts": {
                    "dailyGroupedBar": {
                        "grid": {"left": 32, "right": 12, "top": 36, "bottom": 22, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "compareBar": {
                        "grid": {"left": 32, "right": 12, "top": 48, "bottom": 24, "containLabel": True},
                        "legend": {"top": "left"}
                    },
                    "waterfall": {
                        "grid": {"left": 32, "right": 12, "top": 20, "bottom": 34, "containLabel": True}
                    },
                    "variance": {
                        "grid": {"left": 70, "right": 16, "top": 12, "bottom": 18, "containLabel": False}
                    },
                    "contribution": {
                        "legend": {"top": "center"}
                    }
                }
            }
        },
        "summaryCard": {
            "gridGap": "16px",
            "borderRadius": "16px",
            "compareBlockMarginTop": "2px",
            "comparePadding": "7px 8px",
            "compareItemMinHeight": "37px",
            "compareLabelFontSize": "10px",
            "compareLabelFontWeight": "800",
            "compareLabelColor": "#64748b",
            "compareLabelLetterSpacing": "0.05em",
            "compareValueFontSize": "15px",
            "total": {
                "minHeight": "168px",
                "padding": "11px 14px 10px",
                "titleRowGap": "9px",
                "primaryValueFontSize": "20px",
                "footerGap": "6px",
                "footerMarginTop": "8px",
            },
            "utility": {
                "minHeight": "154px",
                "padding": "12px 13px",
                "topGap": "10px",
                "primaryValueFontSize": "20px",
                "deltaPaddingTop": "8px",
            },
            "kpi": {
                "minHeight": "172px",
                "padding": "12px 14px 12px",
                "topGap": "10px",
                "footerMarginTop": "12px",
            },
            "pdf": {
                "total": {
                    "height": "154px",
                    "minHeight": "154px",
                    "padding": "8px 9px",
                    "borderRadius": "10px",
                    "topGap": "6px",
                    "topMarginBottom": "6px",
                    "leadGap": "3px",
                    "titleRowGap": "6px",
                    "iconSize": "28px",
                    "iconGlyphSize": "15px",
                    "titleFontSize": "8px",
                    "primaryGap": "4px",
                    "primaryValueFontSize": "13px",
                    "supportingFontSize": "7px",
                    "metaMarginTop": "6px",
                    "metaMarginBottom": "4px",
                    "metaGap": "6px",
                    "meterValueFontSize": "8.5px",
                    "comparePadding": "5px 6px",
                    "compareItemPadding": "2px 5px",
                    "compareLabelFontSize": "6.2px",
                    "compareValueFontSize": "10px",
                    "footerGap": "10px",
                    "footerMarginTop": "4px",
                    "footerRowGap": "2px",
                    "footerPaddingTop": "2px",
                    "deltaGap": "5px",
                    "footerValueFontSize": "8.5px",
                    "metaRowGap": "6px",
                    "metaValueGap": "4px",
                    "trendRowGap": "3px",
                    "trendNoteFontSize": "6.4px"
                }
            }
        },
    },
    "echartsTheme": {
        "themeName": "report_default",
        "palette": [
            "#2563eb",
            "#7c3aed",
            "#0ea5e9",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#14b8a6",
            "#8b5cf6",
        ],
        "backgroundColor": "rgba(255,255,255,0)",
        "titleColor": "#111827",
        "subtitleColor": "#64748b",
        "legendTextColor": "#6b7280",
        "axisLineColor": "#cbd5e1",
        "axisLabelColor": "#64748b",
        "splitLineColor": "#e5e7eb",
        "toolboxIconBorderColor": "#94a3b8",
        "grid": {
            "left": "10%",
            "right": "10%",
            "top": 60,
            "bottom": 60,
        },
    },
}


class ReportStyleService:
    """Load centralized style tokens and build inline render context."""

    def __init__(self, style_config_path: str | Path | None = None) -> None:
        self._style_config_path = Path(style_config_path or "config/report_style.json")
        self._warnings: list[str] = []

    def build_render_context(self) -> dict[str, Any]:
        """Build render-ready style context for Jinja templates."""
        style_config = self.load_style_config()
        theme = self.build_echarts_theme(style_config)

        return {
            "report_style": style_config,
            "report_style_css": self.build_inline_css(style_config),
            "chart_theme_name": theme["theme_name"],
            "chart_theme": theme["theme"],
            "chart_theme_json": json.dumps(theme["theme"], ensure_ascii=False),
            "report_style_config_path": str(self._style_config_path),
            "report_style_warnings": list(self._warnings),
        }

    def load_style_config(self) -> dict[str, Any]:
        """Load JSON style config and merge it over safe defaults."""
        defaults = deepcopy(DEFAULT_REPORT_STYLE)

        if not self._style_config_path.exists():
            self._warn(
                f"Style config not found at {self._style_config_path}. Falling back to defaults."
            )
            return defaults

        try:
            with self._style_config_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except json.JSONDecodeError as exc:
            self._warn(
                f"Invalid JSON in {self._style_config_path}: {exc}. Falling back to defaults."
            )
            return defaults
        except OSError as exc:
            self._warn(
                f"Failed to read {self._style_config_path}: {exc}. Falling back to defaults."
            )
            return defaults

        raw_style = payload.get("reportStyle")
        if not isinstance(raw_style, dict):
            self._warn(
                f"Top-level key 'reportStyle' is missing or invalid in {self._style_config_path}. Falling back to defaults."
            )
            return defaults

        merged = self._merge_defaults(defaults, raw_style)
        self._validate_minimum_shape(merged)
        return merged

    def build_inline_css(self, style_config: dict[str, Any]) -> str:
        """Convert the style config into inline CSS variables plus compatibility aliases."""
        sections_for_css = [
            "font",
            "color",
            "layout",
            "radius",
            "shadow",
            "spacing",
            "components",
        ]

        var_lines: list[str] = []
        for section_name in sections_for_css:
            section_value = style_config.get(section_name)
            if isinstance(section_value, dict):
                var_lines.extend(
                    self._flatten_css_variables(section_value, [self._to_kebab_case(section_name)])
                )

        alias_lines = self._build_compatibility_aliases()

        blocks = [":root {"]
        blocks.extend(f"    {line}" for line in var_lines)
        blocks.append("")
        blocks.extend(f"    {line}" for line in alias_lines)
        blocks.append("}")
        return "\n".join(blocks)

    def build_echarts_theme(self, style_config: dict[str, Any]) -> dict[str, Any]:
        """Build a Jinja-safe ECharts theme object from style tokens."""
        font_cfg = style_config.get("font", {})
        chart_cfg = style_config.get("echartsTheme", {})

        theme_name = str(chart_cfg.get("themeName") or "report_default")
        palette = chart_cfg.get("palette") or DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
        if not isinstance(palette, list) or not palette:
            palette = DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
            self._warn("Invalid chart palette detected. Falling back to default palette.")

        theme = {
            "color": palette,
            "backgroundColor": chart_cfg.get("backgroundColor"),
            "textStyle": {
                "fontFamily": font_cfg.get("family"),
            },
            "title": {
                "textStyle": {
                    "color": chart_cfg.get("titleColor"),
                    "fontWeight": font_cfg.get("weightBold"),
                },
                "subtextStyle": {
                    "color": chart_cfg.get("subtitleColor"),
                },
            },
            "legend": {
                "textStyle": {
                    "color": chart_cfg.get("legendTextColor"),
                },
            },
            "toolbox": {
                "iconStyle": {
                    "borderColor": chart_cfg.get("toolboxIconBorderColor"),
                },
            },
            "categoryAxis": {
                "axisLine": {
                    "lineStyle": {"color": chart_cfg.get("axisLineColor")},
                },
                "axisTick": {
                    "lineStyle": {"color": chart_cfg.get("axisLineColor")},
                },
                "axisLabel": {
                    "color": chart_cfg.get("axisLabelColor"),
                },
                "splitLine": {
                    "lineStyle": {"color": [chart_cfg.get("splitLineColor")]},
                },
            },
            "valueAxis": {
                "axisLine": {
                    "lineStyle": {"color": chart_cfg.get("axisLineColor")},
                },
                "axisTick": {
                    "lineStyle": {"color": chart_cfg.get("axisLineColor")},
                },
                "axisLabel": {
                    "color": chart_cfg.get("axisLabelColor")},
                "splitLine": {
                    "lineStyle": {"color": [chart_cfg.get("splitLineColor")]},
                },
            },
            "line": {
                "smooth": False,
                "symbol": "circle",
                "symbolSize": 7,
            },
            "bar": {
                "barMaxWidth": 28,
                "itemStyle": {
                    "borderRadius": [6, 6, 0, 0],
                },
            },
            "pie": {
                "label": {
                    "color": chart_cfg.get("axisLabelColor"),
                },
                "labelLine": {
                    "lineStyle": {
                        "color": chart_cfg.get("axisLineColor"),
                    },
                },
            },
            "grid": chart_cfg.get("grid") or deepcopy(DEFAULT_REPORT_STYLE["echartsTheme"]["grid"]),
        }

        return {
            "theme_name": theme_name,
            "theme": theme,
        }

    def _validate_minimum_shape(self, style_config: dict[str, Any]) -> None:
        """Validate a minimal shape and normalize obviously invalid branches."""
        required_dict_sections = [
            "meta",
            "font",
            "color",
            "layout",
            "radius",
            "shadow",
            "spacing",
            "components",
            "echartsTheme",
        ]

        for section_name in required_dict_sections:
            value = style_config.get(section_name)
            if not isinstance(value, dict):
                style_config[section_name] = deepcopy(DEFAULT_REPORT_STYLE[section_name])
                self._warn(
                    f"Section '{section_name}' is invalid in {self._style_config_path}; default values were restored."
                )

        palette = style_config["echartsTheme"].get("palette")
        if not isinstance(palette, list) or not palette:
            style_config["echartsTheme"]["palette"] = deepcopy(
                DEFAULT_REPORT_STYLE["echartsTheme"]["palette"]
            )
            self._warn("Theme palette is missing or invalid; default palette was restored.")

    def _merge_defaults(self, defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """Deep-merge user overrides over defaults without dropping missing branches."""
        merged = deepcopy(defaults)

        for key, value in overrides.items():
            if key not in merged:
                merged[key] = deepcopy(value)
                continue

            default_value = merged[key]
            if isinstance(default_value, dict) and isinstance(value, dict):
                merged[key] = self._merge_defaults(default_value, value)
            elif value is not None:
                merged[key] = deepcopy(value)

        return merged

    def _flatten_css_variables(
        self,
        current: dict[str, Any],
        path: list[str] | None = None,
    ) -> list[str]:
        """Flatten nested dict tokens into CSS variable lines."""
        lines: list[str] = []
        current_path = path or []

        for key, value in current.items():
            next_path = [*current_path, self._to_kebab_case(key)]
            if isinstance(value, dict):
                lines.extend(self._flatten_css_variables(value, next_path))
                continue

            css_var_name = "--report-" + "-".join(next_path)
            lines.append(f"{css_var_name}: {value};")

        return lines

    def _build_compatibility_aliases(self) -> list[str]:
        """Emit bridge variables so rollout can be gradual in existing CSS assets."""
        alias_map = {
            "--bg-page": "var(--report-color-page-background)",
            "--bg-card": "var(--report-color-card-background)",
            "--bg-header": "var(--report-color-header-background)",
            "--bg-header-strong": "var(--report-color-header-background-strong)",
            "--border": "var(--report-color-border-default)",
            "--border-soft": "var(--report-color-border-soft)",
            "--border-row": "var(--report-color-border-row)",
            "--text-main": "var(--report-color-text-primary)",
            "--text-dark": "var(--report-color-text-heading)",
            "--text-muted": "var(--report-color-text-muted)",
            "--text-subtle": "var(--report-color-text-subtle)",
            "--brand": "var(--report-color-brand-primary)",
            "--accent": "var(--report-color-brand-accent)",
            "--trend-up": "var(--report-color-trend-up)",
            "--trend-down": "var(--report-color-trend-down)",
            "--trend-neutral": "var(--report-color-trend-neutral)",
            "--radius-md": "var(--report-radius-medium)",
            "--radius-lg": "var(--report-radius-large)",
            "--space-xs": "var(--report-spacing-xs)",
            "--space-sm": "var(--report-spacing-sm)",
            "--space-md": "var(--report-spacing-md)",
            "--space-lg": "var(--report-spacing-lg)",
            "--space-xl": "var(--report-spacing-xl)",
            "--shadow-soft": "var(--report-shadow-soft)",
            "--shadow-card": "var(--report-shadow-card)",
        }

        return [f"{alias_name}: {source};" for alias_name, source in alias_map.items()]

    def _to_kebab_case(self, value: str) -> str:
        """Convert camelCase or mixedCase text to kebab-case for CSS variable names."""
        with_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", str(value or ""))
        return with_boundaries.replace("_", "-").lower()

    def _warn(self, message: str) -> None:
        """Record and log a non-fatal warning."""
        self._warnings.append(message)
        logger.warning(message)
