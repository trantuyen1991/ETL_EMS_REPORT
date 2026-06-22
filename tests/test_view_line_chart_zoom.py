from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_template(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_base_view_defines_line_chart_zoom_helper() -> None:
    base_view = _read_template("src/templates/report/base/base_view.html")

    assert "window.__enhanceReportLineChartOption = function (option, context)" in base_view
    assert 'String(series.type || "").toLowerCase() === "line"' in base_view
    assert 'type: "inside"' in base_view
    assert 'type: "slider"' in base_view
    assert "start: 0" in base_view
    assert "end: 100" in base_view
    assert 'filterMode: "filter"' in base_view
    assert "showDataShadow: false" in base_view
    assert "showDetail: false" in base_view
    assert "brushSelect: false" in base_view
    assert "grid.bottom = minGridBottom" in base_view
    assert "axisDateMode !== \"monthly\"" in base_view
    assert "dateFromAxisIndex(index)" in base_view
    assert 'toLocaleDateString("en-US", { day: "2-digit" })' in base_view
    assert "labelIndex === 0 || labelIndex === total - 1" in base_view
    assert 'String(chartContext.axisLabelDensity || "").toLowerCase() === "full"' in base_view
    assert "nextAxisLabel.rotate = forceFullLabels ? 32 : 0" in base_view


def test_base_view_applies_electricity_tooltip_before_line_only_zoom_logic() -> None:
    base_view = _read_template("src/templates/report/base/base_view.html")

    tooltip_index = base_view.index('applyElectricityDeltaTooltip("electricityAreaComparison")')
    line_only_return_index = base_view.index("if (!hasLineSeries)", tooltip_index)

    assert tooltip_index < line_only_return_index
    assert "Delta: <strong>" in base_view
    assert "Delta %: <strong>" in base_view
    assert 'tooltip.reportFormatter !== "electricityPeriodAreaDelta"' in base_view
    assert "customData.deltaPct" in base_view
    assert 'tooltip.reportFormatter !== "electricityDailyTotalHeatmap"' in base_view
    assert "Period MAX: <strong>" in base_view
    assert "% of MAX: <strong>" in base_view
    assert "formatReportSharePercent(percentOfPeriodMax)" in base_view
    assert "currentBottom < 40" in base_view
    assert "grid.bottom = 40" in base_view
    assert 'Category: <strong>' not in base_view
    assert "applyElectricityDailyTotalHeatmapTooltipAndZoom();" in base_view


def test_view_chart_initializers_apply_line_chart_zoom_helper() -> None:
    electricity_view = _read_template("src/templates/report/view/sections/electricity.html")
    utility_view = _read_template("src/templates/report/view/sections/utility.html")
    kpi_view = _read_template("src/templates/report/view/sections/kpi.html")

    assert "__enhanceReportLineChartOption(baseOption, {" in electricity_view
    assert "periodStartDate: config.periodStartDate" in electricity_view
    assert "periodEndDate: config.periodEndDate" in electricity_view
    assert 'axisLabelDensity: "full"' in electricity_view
    assert "__enhanceReportLineChartOption(Object.assign({ animation: false }, baseOption), {" in utility_view
    assert "__enhanceReportLineChartOption(baseOption, {" in kpi_view


def test_pdf_templates_do_not_apply_interactive_line_chart_zoom_helper() -> None:
    base_pdf = _read_template("src/templates/report/base/base_pdf.html")
    electricity_pdf = _read_template("src/templates/report/pdf/sections/electricity.html")
    utility_pdf = _read_template("src/templates/report/pdf/sections/utility.html")
    kpi_pdf = _read_template("src/templates/report/pdf/sections/kpi.html")

    assert "__enhanceReportLineChartOption" not in base_pdf
    assert "__enhanceReportLineChartOption" not in electricity_pdf
    assert "__enhanceReportLineChartOption" not in utility_pdf
    assert "__enhanceReportLineChartOption" not in kpi_pdf
