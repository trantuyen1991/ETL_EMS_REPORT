from pathlib import Path
from textwrap import wrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

COLORS = {
    "blue": "#005496",
    "green": "#2E7D32",
    "orange": "#B26A00",
    "gray": "#4B5563",
    "light_blue": "#EAF3FB",
    "light_green": "#ECF7EE",
    "light_orange": "#FFF4E2",
    "light_gray": "#F3F4F6",
    "line": "#475569",
    "border": "#94A3B8",
    "text": "#1F2937",
    "muted": "#6B7280",
    "note": "#FFF8DB",
}


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def measure(draw, text, f):
    box = draw.multiline_textbbox((0, 0), text, font=f, spacing=6)
    return box[2] - box[0], box[3] - box[1]


def wrap_by_px(draw, text, f, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if measure(draw, trial, f)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, xy, text, f, max_width, fill=COLORS["text"], spacing=8):
    lines = wrap_by_px(draw, text, f, max_width)
    draw.multiline_text(xy, "\n".join(lines), font=f, fill=fill, spacing=spacing)
    _, h = measure(draw, "\n".join(lines), f)
    return h


def draw_bullets(draw, xy, items, f, max_width, fill=COLORS["text"], bullet_indent=30, line_gap=10):
    x, y = xy
    for item in items:
        bullet = "•"
        bullet_w, _ = measure(draw, bullet, f)
        draw.text((x, y), bullet, font=f, fill=fill)
        lines = wrap_by_px(draw, item, f, max_width - bullet_indent)
        text = "\n".join(lines)
        draw.multiline_text((x + bullet_indent, y), text, font=f, fill=fill, spacing=6)
        _, h = measure(draw, text, f)
        y += h + line_gap
    return y


def rounded_box(draw, rect, header_text, body_lines, header_color, body_color, header_font, body_font):
    x1, y1, x2, y2 = rect
    radius = 22
    draw.rounded_rectangle(rect, radius=radius, fill=body_color, outline=COLORS["border"], width=3)
    header_h = 54
    draw.rounded_rectangle((x1, y1, x2, y1 + header_h), radius=radius, fill=header_color, outline=header_color)
    draw.rectangle((x1, y1 + header_h - radius, x2, y1 + header_h), fill=header_color, outline=header_color)
    draw.text((x1 + 22, y1 + 11), header_text, font=header_font, fill="white")
    draw_bullets(draw, (x1 + 24, y1 + header_h + 18), body_lines, body_font, x2 - x1 - 48)


def note_bar(draw, rect, text, fill):
    draw.rounded_rectangle(rect, radius=18, fill=fill, outline="#E5E7EB", width=2)
    draw_wrapped(draw, (rect[0] + 18, rect[1] + 14), text, font(24), rect[2] - rect[0] - 36, fill=COLORS["muted"])


def arrow_head(draw, tip, direction, color=COLORS["line"], size=16):
    x, y = tip
    if direction == "down":
        pts = [(x, y), (x - size, y - size), (x + size, y - size)]
    elif direction == "up":
        pts = [(x, y), (x - size, y + size), (x + size, y + size)]
    elif direction == "left":
        pts = [(x, y), (x + size, y - size), (x + size, y + size)]
    else:
        pts = [(x, y), (x - size, y - size), (x - size, y + size)]
    draw.polygon(pts, fill=color)


def polyline_arrow(draw, points, color=COLORS["line"], width=6):
    draw.line(points, fill=color, width=width)
    (x1, y1), (x2, y2) = points[-2], points[-1]
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = "right" if x2 > x1 else "left"
    else:
        direction = "down" if y2 > y1 else "up"
    arrow_head(draw, (x2, y2), direction, color=color)


def centered_text(draw, y, text, f, fill=COLORS["text"]):
    w, h = measure(draw, text, f)
    x = (2400 - w) // 2
    draw.text((x, y), text, font=f, fill=fill)
    return y + h


def make_architecture():
    img = Image.new("RGB", (2400, 2100), "white")
    draw = ImageDraw.Draw(img)

    y = 44
    y = centered_text(draw, y, "ENERGY REPORTING SYSTEM ARCHITECTURE", font(52, bold=True)) + 8
    y = centered_text(draw, y, "Current project runtime, data ownership, report context, and artifact flow", font(26), fill=COLORS["muted"]) + 24
    note_bar(draw, (240, y, 2160, y + 64), "Daily run orchestration in main.py. Weekly runs are added on Sunday; monthly runs are added at month-end.", COLORS["light_gray"])

    top_y = y + 110
    left_top = (240, top_y, 1100, top_y + 250)
    right_top = (1300, top_y, 2160, top_y + 250)
    repo = (240, top_y + 320, 2160, top_y + 500)
    service = (240, top_y + 580, 2160, top_y + 820)
    unified = (420, top_y + 900, 1980, top_y + 1080)
    left_out = (240, top_y + 1240, 1080, top_y + 1450)
    right_out = (1320, top_y + 1240, 2160, top_y + 1450)
    canonical = (420, top_y + 1570, 1980, top_y + 1715)

    rounded_box(draw, left_top, "Runtime and Configuration Inputs", [
        "main.py bootstrap loads .env / app.yaml and configures logging and MySQL access.",
        "PeriodService resolves daily, weekly, and monthly runs plus canonical output naming.",
        "report_style.json, output location, and staging rules are applied before rendering.",
    ], COLORS["blue"], COLORS["light_blue"], font(28, bold=True), font(22))

    rounded_box(draw, right_top, "Source Data Ownership", [
        "total_energy holds Electricity official totals, while energy_kpi holds KPI values and production-linked reporting rows.",
        "utility_usage plus area-energy sources feed utility and electricity detail sections.",
        "processvalue provides raw utility sensor rows for monitoring, aggregation, and anomaly checks.",
    ], COLORS["green"], COLORS["light_green"], font(28, bold=True), font(22))

    rounded_box(draw, repo, "Repository Layer", [
        "EnergyDataRepository reads configured energy, KPI, and utility sources for current and previous periods.",
        "ProcessValueRepository fetches raw sensor rows by time range and selected sensor columns.",
    ], COLORS["gray"], COLORS["light_gray"], font(28, bold=True), font(22))

    rounded_box(draw, service, "Service Layer", [
        "KPIService and EnergyService enforce KPI coverage rules, official totals logic, comparisons, Top 10 handling, and detail aggregation.",
        "ProcessValueService and UtilityService compute sensor statistics, anomaly-ready metrics, utility dashboards, and sensor-monitoring context.",
        "ReportStyleService injects render-ready presentation tokens from config/report_style.json.",
    ], COLORS["blue"], COLORS["light_blue"], font(28, bold=True), font(22))

    rounded_box(draw, unified, "Unified report_context", [
        "ReportBuilderService.build_report_context_v3 creates meta, period, summary, flags, labels, notes, version, and sections for electricity, utility, and KPI.",
    ], COLORS["orange"], COLORS["light_orange"], font(28, bold=True), font(22))

    rounded_box(draw, left_out, "Rendering Path", [
        "TemplateRenderingService selects the daily or periodic template bundle.",
        "The system renders view_html and pdf_source_html from the same report_context.",
        "PDFService prints the final PDF through a staging HTML path.",
    ], COLORS["blue"], COLORS["light_blue"], font(28, bold=True), font(22))

    rounded_box(draw, right_out, "Excel Export Path", [
        "ExcelExportService builds the daily workbook only.",
        "Workbook sheets are derived from stable tabular structures in report_context.",
    ], COLORS["green"], COLORS["light_green"], font(28, bold=True), font(22))

    rounded_box(draw, canonical, "Canonical Outputs", [
        "OUTPUT_DIR/YYYY_MM/ -> view_html, pdf_source_html, pdf, excel -> 01_monthly / 02_weekly / 03_daily naming",
        "If OUTPUT_DIR is blank, runtime falls back to project-local output/reports/YYYY_MM/.",
    ], COLORS["gray"], COLORS["light_gray"], font(28, bold=True), font(22))

    # vertical connectors
    polyline_arrow(draw, [((left_top[0] + left_top[2]) // 2, left_top[3]), ((left_top[0] + left_top[2]) // 2, repo[1])])
    polyline_arrow(draw, [((right_top[0] + right_top[2]) // 2, right_top[3]), ((right_top[0] + right_top[2]) // 2, repo[1])])
    polyline_arrow(draw, [((repo[0] + repo[2]) // 2, repo[3]), ((repo[0] + repo[2]) // 2, service[1])])
    polyline_arrow(draw, [((service[0] + service[2]) // 2, service[3]), ((service[0] + service[2]) // 2, unified[1])])

    # orthogonal split from unified to both output paths
    stem_x = (unified[0] + unified[2]) // 2
    stem_y1 = unified[3]
    bus_y = left_out[1] - 70
    left_x = (left_out[0] + left_out[2]) // 2
    right_x = (right_out[0] + right_out[2]) // 2
    draw.text((1330, bus_y - 44), "Artifacts are grouped by month and then split by output type.", font=font(21), fill=COLORS["muted"])
    polyline_arrow(draw, [(stem_x, stem_y1), (stem_x, bus_y)])
    draw.line([(left_x, bus_y), (right_x, bus_y)], fill=COLORS["line"], width=6)
    polyline_arrow(draw, [(left_x, bus_y), (left_x, left_out[1])])
    polyline_arrow(draw, [(right_x, bus_y), (right_x, right_out[1])])

    # orthogonal merge from outputs to canonical outputs
    lower_bus_y = left_out[3] + 90
    draw.line([(left_x, lower_bus_y), (right_x, lower_bus_y)], fill=COLORS["line"], width=6)
    polyline_arrow(draw, [(left_x, left_out[3]), (left_x, lower_bus_y)])
    polyline_arrow(draw, [(right_x, right_out[3]), (right_x, lower_bus_y)])
    polyline_arrow(draw, [(stem_x, lower_bus_y), (stem_x, canonical[1])])

    img.save(ROOT / "hinh1_1.png")


def make_flow():
    img = Image.new("RGB", (2400, 2000), "white")
    draw = ImageDraw.Draw(img)

    y = 42
    y = centered_text(draw, y, "REPORT GENERATION AND EXPORT DATA FLOW", font(50, bold=True)) + 8
    y = centered_text(draw, y, "Source retrieval, object building, rendering, and month-grouped artifact storage", font(26), fill=COLORS["muted"]) + 22
    note_bar(draw, (200, y, 2200, y + 72), "Scheduling rule: daily always runs; weekly is added on Sunday; monthly is added at month-end when the anchor date is the last day of the month.", COLORS["note"])

    box_x1, box_x2 = 560, 2000
    box_w = box_x2 - box_x1
    start_y = y + 120
    box_h = 120
    gap = 76
    colors = [
        (COLORS["blue"], COLORS["light_blue"]),
        (COLORS["gray"], COLORS["light_gray"]),
        (COLORS["blue"], COLORS["light_blue"]),
        (COLORS["green"], COLORS["light_green"]),
        (COLORS["blue"], COLORS["light_blue"]),
        (COLORS["orange"], COLORS["light_orange"]),
        (COLORS["green"], COLORS["light_green"]),
        (COLORS["gray"], COLORS["light_gray"]),
    ]
    steps = [
        ("1. Bootstrap runtime", "Initialize config, MySQL client, repositories, and runtime logging in main.py."),
        ("2. Resolve periods for this run", "PeriodService determines anchor date, report types, and canonical export stems for the batch."),
        ("3. Fetch source rows", "Repositories pull total_energy, energy_kpi, utility_usage, area-energy, and selected sensor rows for current and comparison windows."),
        ("4. Aggregate utility sensor statistics", "ProcessValueService and UtilityService compute min/avg/max, anomaly-ready metrics, and monitoring structures."),
        ("5. Build domain objects", "EnergyService, KPIService, and UtilityService produce electricity, KPI, and utility blocks ready for rendering."),
        ("6. Assemble unified report_context", "ReportBuilderService and ReportStyleService merge meta, sections, flags, labels, notes, and presentation tokens."),
        ("7. Render and export artifacts", "Render view_html, render pdf_source_html, print PDF, and write the daily Excel workbook when the period is daily."),
        ("8. Store canonical outputs", "Write files into OUTPUT_DIR/YYYY_MM/ and keep filename ordering with 01_monthly / 02_weekly / 03_daily prefixes. If OUTPUT_DIR is blank, fallback to project-local output/reports/YYYY_MM/."),
    ]

    rects = []
    for idx, ((header_color, body_color), (title, body)) in enumerate(zip(colors, steps)):
        y1 = start_y + idx * (box_h + gap)
        rect = (box_x1, y1, box_x2, y1 + box_h)
        rects.append(rect)
        rounded_box(draw, rect, title, [body], header_color, body_color, font(27, bold=True), font(22))

    center_x = (box_x1 + box_x2) // 2
    for upper, lower in zip(rects, rects[1:]):
        polyline_arrow(draw, [(center_x, upper[3]), (center_x, lower[1])])

    # loop note with orthogonal connector to step 4
    loop_box = (120, rects[3][1] + 24, 450, rects[6][3] - 24)
    draw.rounded_rectangle(loop_box, radius=18, fill="#F8FAFC", outline="#CBD5E1", width=3)
    loop_text = "Loop for each\nscheduled period"
    tw, th = measure(draw, loop_text, font(26, bold=True))
    draw.multiline_text((loop_box[0] + 40, loop_box[1] + 34), loop_text, font=font(26, bold=True), fill=COLORS["gray"], spacing=8)
    draw.text((loop_box[0] + 40, loop_box[1] + 140), "Steps 4 to 7 repeat for each resolved daily, weekly, or monthly period in the run batch.", font=font(21), fill=COLORS["muted"])
    mid_y = (rects[3][1] + rects[6][3]) // 2
    draw.line([(loop_box[2] - 24, mid_y), (box_x1 - 70, mid_y)], fill=COLORS["line"], width=6)
    polyline_arrow(draw, [(box_x1 - 70, mid_y), (box_x1 - 70, rects[3][1] + 40), (box_x1, rects[3][1] + 40)])

    note_bar(draw, (220, 1900, 2180, 1960), "Documentation PDF rebuild is a separate workflow and should be triggered only when documentation source files change.", COLORS["light_gray"])
    img.save(ROOT / "hinh1_2.png")


if __name__ == "__main__":
    make_architecture()
    make_flow()
