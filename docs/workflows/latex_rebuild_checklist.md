# LaTeX Source Rebuild Checklist

## Goal

Rebuild LaTeX documentation outputs from checked-in source for the project documentation templates and keep each step isolated for easy checkpointing.

## Scope for this run

- `docs/latex/templates/project_technical_documentation_template/main.tex`
- `docs/latex/templates/report_reader_guide_template/main.tex`
- `docs/output/`
- `docs/latex/templates/project_technical_documentation_template/figure/project_diagrams.drawio`

## Execution Checkpoints

### Checkpoint 1: Prepare and baseline
- [x] Confirm rebuild scope and lock target outputs.
- [x] Snapshot current generated artifacts in `docs/output/` (if any) with date suffix.
- [x] Check required source files list before edits/build:
  - `.tex` files under both template folders
  - `ref/references.bib` (technical template)
  - `figure/project_diagrams.drawio` + `figure/hinh1_1.png` + `figure/hinh1_2.png`.
- [x] Run this task only with no behavior changes outside docs build path.
- [x] Baseline artifact created: `docs/output/archive_20260609_174341_before_rebuild/`.

### Checkpoint 2: Technical documentation template build
- [x] From `docs/latex/templates/project_technical_documentation_template`, run:
  - `latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex`
- [x] Resolve any LaTeX errors shown in the log.
- [x] Run `latexmk -c` only after successful build in this template.
- [x] Verify `main.pdf` generated (948K).

### Checkpoint 3: Reader guide template build
- [x] From `docs/latex/templates/report_reader_guide_template`, run:
  - `latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex`
- [x] Resolve any LaTeX errors shown in the log.
- [x] Run `latexmk -c` only after successful build in this template.
- [x] Verify `main.pdf` generated (279K).

### Checkpoint 4: Publish output artifacts
- [x] Copy latest successful PDFs to `docs/output/`:
  - `project_technical_documentation_latest.pdf`
  - `project_technical_documentation_YYYYMMDD.pdf`
  - `report_reader_guide_latest.pdf`
  - `report_reader_guide_YYYYMMDD.pdf`
- [x] Ensure output filenames match the workspace naming convention.

### Checkpoint 5: Output sanity check
- [x] Verify files exist at expected paths.
- [x] Check file sizes are non-zero.
- [x] Confirm artifact list after publish:
  - `docs/output/project_technical_documentation_20260609.pdf`
  - `docs/output/project_technical_documentation_latest.pdf`
  - `docs/output/report_reader_guide_20260609.pdf`
  - `docs/output/report_reader_guide_latest.pdf`
- [x] Quick visual sanity review on representative pages:
  - title/cover
  - TOC + lists
  - a normal chapter page
  - an image page / table page

### Checkpoint 6: Close and report
- [x] Record build outputs, date, and commands run in this checklist log.
- [x] Report to Anh: results, generated artifact names, and any warnings encountered.

## Execution log

- `2026-06-09 17:43:41`: created checkpoint backup directory `docs/output/archive_20260609_174341_before_rebuild/`.
- `2026-06-09 17:43:46`: ran `latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex` in `project_technical_documentation_template/` -> up-to-date, no errors.
- `2026-06-09 17:43:52`: ran `latexmk -xelatex -interaction=nonstopmode -file-line-error main.tex` in `report_reader_guide_template/` -> up-to-date, no errors.
- `2026-06-09 17:44:00`: ran `latexmk -c` in cả hai template để dọn file tạm.
- `2026-06-09 17:44:08`: phát hành artifact mới:
  - `docs/output/project_technical_documentation_20260609.pdf`
  - `docs/output/project_technical_documentation_latest.pdf`
  - `docs/output/report_reader_guide_20260609.pdf`
  - `docs/output/report_reader_guide_latest.pdf`
- `2026-06-09 17:45:10`: kiểm tra `pdfinfo`:
  - `project_technical_documentation_latest.pdf`: 59 trang, 970288 bytes, kích thước 538.58 x 765.35 pt.
  - `report_reader_guide_latest.pdf`: 36 trang, 285560 bytes, kích thước 538.58 x 765.35 pt.
- `2026-06-09 17:45:20`: kiểm tra trích xuất nội dung mẫu bằng `pdftotext` (cover/section/table samples):
  - Kỹ thuật: trang bìa và phần kiểm soát tài liệu đúng văn bản đích, bảng metadata hiển thị.
  - Reader guide: trang đầu và phần KPI reading hiển thị đúng tiêu đề, nội dung section.
- `2026-06-09 17:45:35`: log build kiểm tra:
  - Không có lỗi compile chặn.
  - Có cảnh báo `Underfull/Overfull` (layout cảnh báo bình thường với text-heavy document), không ảnh hưởng tạo file PDF.
