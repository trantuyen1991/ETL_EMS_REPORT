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
- long history/revision tables break across pages cleanly instead of colliding with the footer area
- bordered tables keep their explicit top border line
- long file paths or code-like table cells wrap inside the table instead of clipping past the right edge
- tables and figures are not over-forced into `h` placement when `htbp` would produce cleaner rhythm
- table borders remain readable on screen without relying on fragile custom wrappers
- flowchart connectors use straight or orthogonal routing instead of diagonal arrows
- diagrams are large enough for screen review and their text stays wrapped inside the intended container boxes

---

# AGENT RESPONSIBILITIES

AI agents MUST:
- regenerate the PDF after documentation changes
- avoid modifying template core styles
- avoid unnecessary package additions
- preserve formatting consistency

AI agents SHOULD:
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
