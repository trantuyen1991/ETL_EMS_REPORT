# LATEX DOCUMENTATION WORKFLOW

## Purpose

This workflow defines how all AI agents, OpenClaw workflows,
and automation scripts must maintain and generate project technical documentation
inside this project.

---

# DOCUMENTATION UPDATE RULE

Whenever project documentation source files are updated, modified, generated,
or extended, the workflow MUST:

1. Update the relevant markdown or LaTeX source files
2. Validate file references and image paths
3. Validate bibliography references
4. Rebuild the LaTeX PDF
5. Verify successful PDF generation
6. Preserve previous formatting and template style

---

# PDF BUILD RULE

Documentation-related updates MUST trigger PDF regeneration.
Code-only changes do not require a LaTeX rebuild unless they also change
documentation source content, figures, references, or documentation rules.

Use:

```bash
latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex
```

Do NOT use:
- pdflatex
- plain tex

---

# TEMPLATE LOCATION

Primary template:

docs/latex/templates/project_technical_documentation_template/

Main entry file:

docs/latex/templates/project_technical_documentation_template/main.tex

---

# OUTPUT LOCATION

Generated PDFs should be stored in:

docs/output/

Recommended naming:

- project_technical_documentation_latest.pdf
- project_technical_documentation_YYYYMMDD.pdf

Generated files under `docs/output/` are output artifacts.
They should be rebuilt from source when documentation changes and should not be edited manually.

---

# DRAW.IO FIGURE SOURCE RULE

Technical diagrams used by the LaTeX technical manual MUST keep one canonical
editable source file:

```text
docs/latex/templates/project_technical_documentation_template/figure/project_diagrams.drawio
```

This `.drawio` file is the source of truth for project diagrams. It may contain
multiple pages/sheets. Do not maintain parallel hand-authored SVG/TikZ sources
for the same diagram unless the project owner explicitly approves a temporary
migration step.

Current sheet-to-artifact mapping:

| Draw.io sheet | Exported artifact used by LaTeX | LaTeX label |
| --- | --- | --- |
| `System Architecture - Vertical Icons` | `figure/hinh1_1.png` | `fig:system_architecture` |
| `Report Flow - Vertical Icons` | `figure/hinh1_2.png` | `fig:report_generation_flow` |

Current export format for these draw.io diagrams is PNG because both the VS Code
Draw.io extension and the local Draw.io desktop workflow support it reliably.
Use scale `2` and a small border when exporting so text stays readable in the
generated PDF.

Draw.io diagram design rules:

- keep operational flows top-down unless a left-to-right view is clearly more readable
- keep image/icon cells on top of their container/card cells before export
- use straight connectors or orthogonal L-shaped connectors with rounded corners
- avoid diagonal connector routing in architecture and workflow diagrams

Draw.io CLI page indexes are 1-based:

```bash
xvfb-run -a drawio -x -f png -p 1 -s 2 -b 10 \
  -o docs/latex/templates/project_technical_documentation_template/figure/hinh1_1.png \
  docs/latex/templates/project_technical_documentation_template/figure/project_diagrams.drawio

xvfb-run -a drawio -x -f png -p 2 -s 2 -b 10 \
  -o docs/latex/templates/project_technical_documentation_template/figure/hinh1_2.png \
  docs/latex/templates/project_technical_documentation_template/figure/project_diagrams.drawio
```

The Snap Draw.io package may print GPU or Mesa warnings under `xvfb-run`; the
export is still considered successful when the final `source -> output` line is
printed and the PNG file is updated.

When draw.io CLI export is not available in the local environment:

1. AI agents update only `project_diagrams.drawio`
2. The project owner exports the touched sheet manually from the VS Code Draw.io extension
3. The exported artifact replaces the matching file under `figure/`
4. The LaTeX PDF is rebuilt and the figure page is visually checked

When draw.io CLI export becomes available, agents may export directly from the
canonical `.drawio` source, but must still keep `project_diagrams.drawio` as the
only editable source.

---

# BUILD SUCCESS RULE

A successful build MUST:
- generate PDF without fatal errors
- preserve bibliography
- preserve images
- preserve table formatting
- preserve chapter formatting
- preserve page-level layout integrity for any touched template areas

Warnings about optional unicode spacing may be ignored if PDF output is correct.

When the change touches layout or template chrome, also visually verify representative pages such as:
- cover/control pages
- TOC/list pages
- a normal chapter/content page
- any page containing a note/callout banner or long metadata paths
- at least one multi-column table page
- at least one page where the last content block sits close to the footer area

For this template's current screen-first PDF workflow, verify that:
- left/right content margins stay visually symmetric across consecutive pages
- header/footer placement does not alternate like a print-spread layout
- header-to-content spacing is not overly loose
- content-to-footer spacing is not overly loose
- chapter opening rhythm from chapter title -> lead block -> first section feels intentional and consistent
- vertical rhythm between paragraph blocks, section titles, and table/figure captions feels consistent rather than accidental
- paragraph-to-list and list-to-paragraph spacing feels consistent across chapters instead of tightening or opening unpredictably
- paragraph-to-float and float-to-paragraph spacing feels consistent instead of leaving obvious holes
- bordered tables keep their explicit top border line
- long file paths or code-like table cells wrap inside the table instead of clipping past the right edge
- tables and figures are not over-forced into `h` placement when `htbp` would produce cleaner rhythm
- table borders remain readable on screen without relying on fragile custom wrappers
- draw.io icons/images render on top of their cards/containers
- flowchart connectors use straight or rounded orthogonal routing instead of diagonal arrows

---

# AGENT RESPONSIBILITIES

AI agents MUST:
- regenerate the PDF after documentation changes
- avoid modifying template core styles
- avoid unnecessary package additions
- preserve formatting consistency

AI agents SHOULD:
- use `docs/workflows/latex_rebuild_checklist.md` for grouped rebuild work to keep checkpoints small and rollback-friendly
- clean temporary build files when appropriate
- archive older PDFs if versioning is enabled

---

# RECOMMENDED WORKFLOW

Documentation source update
    ↓
Update docs
    ↓
Generate charts/images
    ↓
Render LaTeX
    ↓
Build PDF
    ↓
Store output PDF
    ↓
Update latest PDF symlink/copy

---

# OPTIONAL CLEANUP

Optional cleanup command:

```bash
latexmk -c
```

Do NOT remove:
- final PDF
- bibliography source
- template files

---

# FAILURE HANDLING

If LaTeX build fails:
1. Preserve logs
2. Preserve temporary files
3. Report the exact error
4. Do not silently skip PDF generation

---

# LONG-TERM GOAL

The project documentation system should behave like:

- Documentation-as-Code
- Continuous Documentation
- Engineering-grade reporting pipeline
