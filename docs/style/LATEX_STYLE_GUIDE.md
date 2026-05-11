# LATEX STYLE GUIDE

## Purpose

This project uses a standardized LaTeX template for project technical documentation,
including project description, feature documentation, business rules, calculation methods,
architecture documents, SOPs, and deployment manuals.

All AI agents, OpenClaw agents, Codex workflows, and automation scripts MUST follow this guide.



# ENGINE

Use:

- XeLaTeX
- latexmk
- biber

Build command:

```bash
latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex
```

Do NOT use:

. pdflatex
. lualatex
. plain tex



# TEMPLATE LOCATION

Primary template:

docs/latex/templates/project_technical_documentation_template/

Never redesign the document structure unless explicitly requested.



# FONT RULES

Use:

. Times New Roman

Do not change:

. font family
. font size hierarchy
. chapter style
. heading style



# DOCUMENT STYLE

Keep:

. existing paper size
. chapter formatting
. section formatting
. bibliography formatting
. caption formatting

For this template's current target use:

. optimize for screen-first PDF reading and review
. use symmetric left/right margins
. avoid book-style twoside inner/outer asymmetry unless explicitly requested later for print binding
. keep header/footer visually fixed across pages instead of alternating by spread

Do not introduce random styling changes.

When layout issues are found:

. prefer controlled template-level adjustments
. avoid ad-hoc per-page spacing hacks
. fix recurring issues once in the shared template


# CALLOUT / NOTE STYLE

For notes, cautions, internal-review disclaimers, and take-note blocks:

. use a banner-style `tcolorbox` with a colored title bar
. keep the title short, e.g. `Ghi chú`, `Lưu ý`, `Cảnh báo`
. keep the body concise, operational, and professional
. avoid plain floating paragraphs for important callouts when a reusable note block is more appropriate

For long technical paths inside metadata or control boxes:

. do not force long paths onto a single row
. put the label on one line and the path value on the next line when needed
. allow path wrapping cleanly instead of overflowing the box edge


# SPACING AND PAGE CHROME RULES

Header-to-content spacing must be explicitly controlled.

Use:

. compact `headsep`
. compact but safe `footskip`
. controlled chapter/title spacing
. controlled section/subsection spacing where the space before a heading is intentionally larger than the space after it
. controlled caption spacing for tables and figures
. helper macros for title pages and TOC-style pages
. shared page-building rules such as `flushbottom` when bottom whitespace becomes visually inconsistent

Aim for a stable vertical rhythm between:

. paragraph blocks
. section titles
. subsection titles
. table/figure captions
. paragraph-to-list transitions
. list-to-paragraph transitions
. paragraph-to-float transitions
. float-to-paragraph transitions
. the next content block after a float

Avoid:

. large dead zones between the header rule and the first heading/content block
. unusually large gaps between the last content block and the footer rule when the issue can be fixed at template level
. section headings whose top/bottom spacing feels arbitrary from page to page
. table titles that sit noticeably tighter or looser than nearby section headings without a deliberate reason
. manual one-off `\vspace` fixes that only hide the real spacing problem

If spacing is adjusted:

. prefer `geometry`, `titlesec`, `caption`, `enumitem`, float-spacing parameters, or shared helper macro updates
. verify representative pages such as control/info pages, TOC pages, and normal content pages
. verify both header-to-content spacing and content-to-footer spacing after the change
. verify at least one page containing a paragraph -> section -> table transition
. verify at least one page containing a paragraph -> list -> paragraph transition



# TABLE STYLE

Preferred packages:

. booktabs
. tabularx
. longtable

For this template's current screen-first PDF convention, prefer the simplest stable table approach:

. use direct `tabularx` / `tabular` definitions in the chapter source
. use built-in column specs, `|`, and `\hline` when borders are needed
. if a bordered table is used, include the explicit top border line instead of relying on the first row only
. prefer breakable text columns such as `RaggedRight`-style `p{}` / `X` columns over overflow-prone rigid text blocks
. for long file paths or code-like strings inside table cells, prefer breakable forms such as `\nolinkurl{}` or a shared helper macro instead of raw unbreakable `\texttt{}`
. prefer flexible float placement such as `htbp` for normal tables/figures instead of forcing `h` unless there is a very specific layout reason
. avoid custom table wrapper environments unless there is a clear repeated need and they are proven stable
. avoid heavy full-black spreadsheet grids

Use:

. concise headers
. engineering-friendly naming
. light, readable table borders suitable for on-screen PDF review
. cell content that wraps cleanly instead of clipping past the right border



# IMAGE RULES

All charts/images must:

. be high resolution
. use professional engineering style
. avoid excessive colors
. use clean legends and labels

Prefer:

. PNG for screenshots
. PDF/SVG for vector diagrams

For flowcharts and architecture diagrams:

. use straight or orthogonal connectors only
. prefer vertical, horizontal, or L-shaped routing
. avoid diagonal arrows unless there is a very strong reason



# REPORT STRUCTURE

Recommended structure:

1. Cover Page
2. Revision History
3. Table of Contents
4. Executive Summary
5. System Architecture
6. Data Flow
7. ETL Logic
8. KPI Calculation
9. Charts and Analysis
10. Troubleshooting
11. Appendix



# AI AGENT RULES

AI agents MUST:

. preserve formatting consistency
. preserve LaTeX package compatibility
. avoid unnecessary package additions
. avoid changing document class
. avoid changing bibliography style

AI agents SHOULD:

. generate reusable chapters
. separate content from formatting
. keep comments concise and professional



# CHART GENERATION

Charts should preferably be generated by Python
and imported into LaTeX as image assets.

Avoid generating complex charts directly in TikZ unless explicitly requested.



# FILE ORGANIZATION

Use:

docs/
├── latex/
├── style/
├── workflows/
└── conventions/

Keep generated output separated from templates.
Track LaTeX source files and figure assets.
Do not treat generated LaTeX build artifacts as primary source files.



# OUTPUT GOAL

The final PDF should look like:

. professional
. industrial-grade
. print-friendly
. engineering-focused
. clean and maintainable
