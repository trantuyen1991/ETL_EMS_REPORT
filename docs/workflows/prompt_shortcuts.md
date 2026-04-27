# Prompt Shortcuts

## 1. Refactor Single File

Use workflow: Refactor Single File

Target: <file_path>

Rules:
- follow docs/refactor_rules.md
- do not delete without approval
- commit after each step

---

## 2. Close Milestone

Use workflow: Close Milestone

Target version: <Vx>

Steps:
- review changes
- update docs
- commit
- create tag
- run `/home/nbt/services/mempalace/.venv/bin/mempalace mine .`

---

## 3. Render Weekly Report

Use workflow: Render Weekly Report

Steps:
- set REPORT_ANCHOR_DATE to weekend
- run report generation
- return PDF path

---

## 4. UI Refactor

Refactor UI based on docs/ui_style.md

Rules:
- reuse existing components
- do not introduce new style patterns
- keep consistency across sections

---

## 5. Memory Update

After any code/doc change:

cd project  
/home/nbt/services/mempalace/.venv/bin/mempalace mine .

---

## 6. Debug Mode

When error occurs:

- do not auto-fix
- explain root cause
- propose minimal solution
- wait for approval