# Commit Convention

## 1. Format

<type>(<scope>): <short description>

---

## 2. Types

- feat: new feature
- fix: bug fix
- refactor: code change without behavior change
- docs: documentation only
- chore: config / tooling / cleanup

---

## 3. Examples

refactor(template_service): remove unused helpers  
refactor(kpi_service): simplify aggregation logic  
docs(report_spec): update KPI section description  
fix(pdf_service): correct chart rendering size  

---

## 4. Body (Optional)

Use when needed:

refactor(template_service): remove unused helpers

- removed 3 unused internal functions
- no behavior change
- verified by local run

Next:
- reorder functions
- update docstrings

---

## 5. Rules

- Keep title < 72 chars
- Use lowercase type
- No vague messages like "update", "fix stuff"
- One logical change per commit

---

## 6. Tagging

Use semantic versioning:

vMAJOR.MINOR.PATCH

Examples:
- v3.0.0 → milestone release
- v3.1.0 → feature update
- v3.0.1 → bug fix

---

## 7. Milestone Tag Rule

When closing a version:

- ensure code is stable
- docs aligned
- memory updated

Then:

git tag -a vX.X.X -m "Release VX"