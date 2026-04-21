# Development Workflows

## 1. Purpose

This file defines repeatable development workflows for the project so that OpenClaw can follow a stable process without needing the user to restate the same steps every time.

The goal is to:
- keep changes safe and reviewable
- preserve a clean Git history
- update project memory after meaningful changes
- reduce inconsistency in code, docs, and UI work

---

## 2. General Principles

### 2.1 Small, Checkpoint-Based Changes
- Prefer small, explicit checkpoints over one large refactor.
- Each checkpoint should be:
  - buildable
  - reviewable
  - reversible

### 2.2 Build Before and After Important Changes
- Before changing logic, run the project once to understand the current state.
- After each meaningful refactor step, run the project again to verify behavior.

### 2.3 Commit at Safe Milestones
- Commit only when the codebase is in a stable state.
- Do not mix unrelated concerns into the same commit.

### 2.4 Memory Must Match the Real Project
- After docs or code change meaningfully, re-mine MemPalace.
- Project memory should reflect the latest approved implementation.

### 2.5 Human-in-the-Loop
- OpenClaw should propose findings first when deletion or behavior changes may be risky.
- The user decides before destructive cleanup.

---

## 3. Standard Working Cycle

Use this base cycle for most development tasks:

1. Understand current state
2. Build / run to establish baseline
3. Make one focused change
4. Build / run again
5. Review result
6. Commit stable checkpoint
7. Re-mine project memory if code/docs changed significantly

Short form:

```text
BUILD → CHANGE → BUILD → REVIEW → COMMIT → MINE
```

---

## 4. Workflow: Refactor a Single File

This workflow is intended for cleanup and refactor work on one file at a time.

### Step 1 — Baseline Build
Purpose:
- confirm the project is runnable before refactor
- capture current errors before touching the file

Actions:
1. Build or run the relevant entry point
2. Record whether the project is currently passing or already failing
3. If no new issue exists, create a baseline commit before refactor starts

Recommended checkpoint intent:
- preserve a clean rollback point before file refactor

### Step 2 — Detect Duplicate / Unused Functions
Purpose:
- identify cleanup candidates before deleting anything

Actions:
1. Inspect the file for:
   - duplicated logic
   - dead helper functions
   - functions no longer referenced
   - nearly identical functions that may be merged later
2. Summarize findings for user review
3. Do not delete immediately when risk is unclear

Output to user should include:
- function name
- suspected issue type
- evidence or reason
- recommended action

### Step 3 — Remove Confirmed Unused / Redundant Functions
Purpose:
- perform safe cleanup first, before structural refactor

Actions:
1. Delete only the functions approved by the user
2. Build / run the project again
3. If the build passes, create a cleanup commit
4. If the build fails:
   - stop
   - report the likely broken dependency
   - explain which deletion may have been incorrect

Recommended checkpoint intent:
- cleanup only

### Step 4 — Reorder and Organize Functions
Purpose:
- improve readability without changing behavior

Actions:
1. Group functions by responsibility
2. Move public / high-level functions above helpers when appropriate
3. Keep related helpers near the functions that use them
4. Avoid logic changes unless necessary
5. Build / run again
6. Commit if stable

Recommended order preference:
1. module constants / config
2. public entry functions
3. main orchestration helpers
4. transformation helpers
5. formatting helpers
6. private utility helpers

Recommended checkpoint intent:
- structure only

### Step 5 — Update Docstrings and File-Level Documentation
Purpose:
- align documentation with the real implementation after cleanup

Actions:
1. Update file header comments if needed
2. Update each function docstring to match current behavior
3. Remove stale comments
4. Keep docstrings concise and structured
5. Build / run once more if documentation edits touched code formatting or decorators
6. Commit final documentation pass

Recommended checkpoint intent:
- docs only

### Step 6 — Re-Mine Project Memory
Purpose:
- keep MemPalace aligned with the new code and docs

Actions:
1. Ensure the terminal is in the correct project folder
2. Run `pwd`
3. Run `mempalace mine .`
4. Optionally run `mempalace status`

---

## 5. Recommended Refactor Decision Rules

### 5.1 When to Delete a Function
Delete only when at least one is true:
- no references remain
- replaced by another function already in use
- legacy path is clearly obsolete
- duplicate behavior is already covered elsewhere

### 5.2 When Not to Delete Yet
Do not delete yet when:
- dynamic calls may exist
- the function is part of a planned next step
- the function is unused now but intentionally reserved
- evidence is uncertain

In those cases:
- report first
- let the user decide

### 5.3 Reordering vs Refactoring
Treat these as separate steps:
- cleanup deletion
- function ordering
- logic refactor
- documentation update

This keeps commits smaller and debugging easier.

---

## 6. Workflow: Commit and Tag a Milestone

Use this workflow when closing a version stage such as V3 and preparing V4.

### Step 1 — Verify Project State
- review `git status`
- review meaningful diffs
- ensure docs reflect the intended milestone state

### Step 2 — Create Milestone Commit
- stage only the intended files
- commit with a clear milestone message

### Step 3 — Create Annotated Tag
- use annotated tags for milestones
- tag should represent a stable rollback point

### Step 4 — Re-Mine Memory
- after commit and tag, re-mine project memory if docs/code changed

### Step 5 — Run Verification Task
Example:
- render a weekly PDF
- verify output path
- report the result

---

## 7. Commit Message Convention

Use a clear and consistent format.

### 7.1 Preferred Style

```text
<type>(<scope>): <short title>
```

Examples:
- `refactor(period_service): remove unused helpers and reorder functions`
- `docs(report): align V3 status with current implementation`
- `fix(pdf): stabilize chart resize before print`
- `feat(csv_export): add report csv output service`
- `chore(memory): re-mine project after docs update`

### 7.2 Recommended Types
- `feat` → new feature
- `fix` → bug fix
- `refactor` → code cleanup or restructuring without intended behavior change
- `docs` → documentation only
- `test` → tests only
- `chore` → maintenance, tooling, memory update, config update
- `style` → formatting only, no logic change

### 7.3 Commit Body (Recommended for Important Changes)

Use a short structured body when the change is significant.

Example:

```text
refactor(template_service): reorder helpers and remove dead code

- remove confirmed unused helper functions
- group render helpers by responsibility
- no intended business logic change
- verified by local run before commit

Next:
- update file docstrings
- re-mine project memory
```

### 7.4 Recommendation About "finish / next"
Your idea is good, but it should be used in the commit body, not forced into every title.

Recommended usage:
- title = concise and searchable
- body = what was finished, what comes next

This is better than making every subject line too long.

---

## 8. Tag Convention

### 8.1 Recommended Version Tag Format
Use semantic-like milestone tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

### 8.2 Meaning
- first number = major milestone or large stage change
- second number = meaningful feature milestone
- third number = small stable patch point

### 8.3 Recommendation for Current Project Stage
If V3 is a milestone closeout before moving to V4, good options are:
- `v3.0.0` → if V3 is treated as a real milestone release
- `v3.0.0-dev` → if still internal / not release-like
- `report-v3-final` → if you prefer descriptive milestone tags

Recommendation:
- use `v3.0.0` for a clean stage boundary

---

## 9. Workflow: Update Memory After Approved Changes

Use after meaningful code/doc changes.

### Required Steps
1. `cd ~/.openclaw/workspace/02_MySQL`
2. `pwd`
3. verify path is correct
4. `mempalace mine .`
5. optionally `mempalace status`

### Important Rule
- Never run `mempalace mine .` from `~`
- Always confirm project path first

---

## 10. Workflow: UI Change with Shared Style Rules

Use when changing HTML / CSS / report templates.

### Required Rules
- follow `docs/ui_style.md` strictly
- do not introduce a second visual style for the same object type
- reuse shared patterns for:
  - section titles
  - cards
  - tables
  - KPI blocks
  - semantic colors
  - spacing

### Recommended Prompt Pattern

```text
Refactor this UI block based on docs/ui_style.md.
Keep the same object types visually consistent.
Do not introduce a second style for the same card/table/button pattern.
```

---

## 11. Suggested Reusable Workflow Names

These names can be used when instructing OpenClaw.

- `Refactor Single File`
- `Close Milestone and Tag`
- `Update Project Memory`
- `Render Weekly Verification PDF`
- `UI Refactor with Shared Style`

Example usage:

```text
Use workflow: Refactor Single File for src/services/template_service.py
```

---

## 12. Practical Recommendations for This Project

### 12.1 What OpenClaw Should Usually Do
- explain before modifying
- separate cleanup from behavior change
- commit at stable checkpoints
- re-mine after meaningful changes
- keep docs aligned with implementation

### 12.2 What OpenClaw Should Avoid
- auto-commit without user approval
- mixing deletion, reordering, refactor, and docs in one giant step
- running memory updates from the wrong directory
- introducing inconsistent UI styles

---

## 13. Minimal Prompt Shortcuts

### A. Refactor One File

```text
Use workflow: Refactor Single File.
Target file: <path>.
Follow the workflow exactly and stop at each decision point that may require deletion approval.
```

### B. Close a Milestone

```text
Use workflow: Close Milestone and Tag.
Target milestone: V3.
After commit/tag, re-mine memory and render a weekly verification PDF.
```

### C. UI Refactor

```text
Use workflow: UI Refactor with Shared Style.
Follow docs/ui_style.md strictly.
```

