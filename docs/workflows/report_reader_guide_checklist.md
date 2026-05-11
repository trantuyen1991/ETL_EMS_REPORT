# Report Reader Guide Checklist

## Purpose

Create a second PDF that is shorter and more reader-facing than the current technical manual.

Target outcome:
- help report readers understand what each section means
- explain where the numbers come from
- explain the main calculation and comparison rules
- reduce misreading of charts, tables, zero values, missing values, and coverage-dependent KPI blocks

## Primary audience

This guide is for:
- report readers
- workshop managers
- supervisors
- business users
- internal stakeholders who consume the report output

This guide is not primarily for:
- developers
- deployment operators
- maintainers of systemd / runtime
- code-level handover readers

## Approved direction

The new PDF should:
- be shorter than the current technical manual
- use reader-friendly language
- stay aligned with actual implementation and report rules
- cover daily, weekly, and monthly report reading where relevant
- explain meaning first, technical source second

The new PDF should avoid going deep into:
- deployment
- service/timer operations
- repository/service ownership maps
- code structure
- host bootstrap details

## Core questions the guide must answer

1. What does each part of the report mean?
2. Where does each important number come from?
3. How is it calculated, compared, or selected?
4. What should the reader be careful not to misunderstand?

## Recommended chapter structure

1. Guide purpose and reading scope
2. Report anatomy overview
3. How to read the Header and reporting period
4. How to read Electricity
5. How to read Utility and Sensor Monitoring
6. How to read KPI
7. Source-of-truth and calculation rules that affect interpretation
8. Common interpretation notes and caveats
9. Quick glossary / symbol meaning

## Working assumptions

- cover daily, weekly, and monthly report variants
- keep tone business-facing, not code-facing
- reuse existing project rules instead of inventing new logic
- prefer concise explanation with concrete interpretation examples

## Checkpoints

- [x] Checkpoint 1. Freeze scope, audience, and chapter outline for the new reader guide
- [x] Checkpoint 2. Create the new LaTeX source set for the reader guide and build a first skeleton PDF
- [x] Checkpoint 3. Write report anatomy + header/period reading chapters
- [x] Checkpoint 4. Write Electricity interpretation chapter
- [x] Checkpoint 5. Write Utility + Sensor Monitoring interpretation chapter
- [x] Checkpoint 6. Write KPI interpretation chapter
- [ ] Checkpoint 7. Write source-of-truth, comparison, coverage, zero-vs-missing, and caveat chapter
- [ ] Checkpoint 8. Add quick glossary / reader cheat sheet and do visual cleanup
- [ ] Checkpoint 9. Final review pass, PDF rebuild, and checkpoint summary

## Notes for execution

- Each checkpoint should stay reviewable and narrowly scoped.
- Do not mix reader-guide writing with deployment/handover manual refactors unless explicitly requested.
- When explaining a metric or chart, tie it back to current report behavior, not generic theory.
- If implementation and existing docs disagree, verify against the live report logic before writing the guide.
