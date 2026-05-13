# Technical Diagram Sources

`project_diagrams.drawio` is the canonical editable source for technical manual diagrams.

Current export mapping:

| Draw.io sheet | Export artifact | Used in |
| --- | --- | --- |
| `System Architecture` | `hinh1_1.png` | `chapter_project_overview.tex` / `fig:system_architecture` |
| `Report Generation Flow` | `hinh1_2.png` | `chapter_project_overview.tex` / `fig:report_generation_flow` |

Edit diagrams in `project_diagrams.drawio` first. Export the changed sheet from the VS Code Draw.io extension or Draw.io desktop CLI to the matching PNG file, then rebuild the LaTeX manual.

Draw.io CLI page indexes are 1-based:

```bash
xvfb-run -a drawio -x -f png -p 1 -s 2 -b 10 -o hinh1_1.png project_diagrams.drawio
xvfb-run -a drawio -x -f png -p 2 -s 2 -b 10 -o hinh1_2.png project_diagrams.drawio
```

Do not create a second editable source such as a separate hand-authored SVG or TikZ file for the same diagram unless it is an explicit, temporary migration step.
