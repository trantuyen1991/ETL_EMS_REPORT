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

Warnings about optional unicode spacing may be ignored if PDF output is correct.

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
