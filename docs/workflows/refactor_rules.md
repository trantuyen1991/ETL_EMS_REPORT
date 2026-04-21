# Refactor Rules

## 1. Principles

- Do not change business logic unless explicitly requested
- Prefer small, incremental changes
- Always validate after each step
- Maintain backward compatibility unless approved

---

## 2. Refactor Flow (Single File)

### Step 1 — Baseline
- Build/run current code
- Ensure no errors
- Create checkpoint commit

---

### Step 2 — Analysis (NO CHANGE)
- Detect:
  - unused functions
  - duplicated logic
  - dead code
- Output summary → WAIT for approval

---

### Step 3 — Cleanup
- Remove only approved items
- Build & run again

If OK:
→ commit: `refactor(<file>): remove unused code`

If error:
→ STOP and report root cause

---

### Step 4 — Reordering
- Group functions logically:
  - public → private
  - high-level → low-level
- NO logic change

→ build → commit

---

### Step 5 — Documentation
- Update:
  - docstrings
  - comments
  - misleading names

→ commit: `docs(<file>): align documentation`

---

## 3. Safety Rules

- Never combine multiple refactor steps in one commit
- Never auto-delete without confirmation
- Always provide summary before destructive changes
- Prefer readability over clever optimization

---

## 4. Done Criteria

- Code runs without error
- No unused functions remain
- Structure is clean and readable
- Documentation matches implementation