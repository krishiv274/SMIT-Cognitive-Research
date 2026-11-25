# Implementation Checklist

Status of every requirement in `PROJECT_PROMPT.md`. ✅ = implemented and verified by automated tests or inspection · 🧑‍🔬 = requires the research team.

## Phase 1 — Academic research
- ✅ Lecture PDF analysed (28 slides) → `research/Lecture_Concept_Mapping.md`
- ✅ Literature review with 44 Crossref-verified APA 7 references → `research/Literature_Review.md`, `Reference_Verification_Log.md`
- ✅ Methodology, variables, hypotheses (H0–H4), SAP with pre-specified exclusions, parameter justification
- ✅ Informed consent, participant instructions, research protocol, theoretical framework

## Phase 2 — Architecture
- ✅ Architecture, state machines, import/export formats, privacy/security → `docs/`
- ✅ Relational schema with constraints, Alembic migration, generated SQL → `database/`

## Phase 3 — Cognitive task
- ✅ Welcome, consent, registration (validation, 18+, duplicate email), instructions with examples
- ✅ Practice (6, feedback, repeatable), 3 conditions × 20 trials, breaks, completion, save confirmation
- ✅ Seeded server-side plans, balanced same/different, run limits, no pattern repeats, 6-order counterbalancing
- ✅ Frame-synchronised timing, measured durations, refresh-rate estimate, focus loss, dropped frames, duplicate/premature key handling, deadline
- ✅ Per-trial storage, retry queue, resume without duplicate sessions, withdrawal

## Phase 4 — Researcher dashboard
- ✅ Overview, participants (status/exclude/withdraw/delete, audited contact access), session inspector
- ✅ Versioned configuration with locking and audit; pilot mode with debugging and stimulus previews
- ✅ Import (xlsx/csv/json, 18-point validation, preview, transactional commit, audit, auto-analysis) and export
- ✅ Templates: 8-sheet workbook (dropdowns, freeze panes, filters, formulas verified), summary template, CSVs

## Phase 5 — Statistics
- ✅ Cleaning, classification, exclusions, descriptives, RM-ANOVA/Friedman, paired t/Wilcoxon + Holm, effect sizes, correlations, demographics, costs, IES, d′, sensitivity analyses — cross-validated with Pingouin
- ✅ 18 figures (PNG/SVG/PDF), skipped when data are insufficient

## Phase 6 — Deliverables
- ✅ Preliminary report (PDF/DOCX/HTML), final-report engine, results workbook, presentation (20 slides + regeneration), viva guide (38 Q&A), pilot checklist

## Phase 7 — Quality assurance
- ✅ Backend pytest, frontend Vitest, Playwright E2E, full-length default-configuration dry run → `pilot/Technical_Dry_Run_Report.md`
- ⚠️ Docker image not built here (Docker daemon not running); files provided

## Phase 8 — Handover
- ✅ README, SETUP, USER_GUIDE, RESEARCHER_GUIDE, submission checklist (below)

## Remaining human research activities
- 🧑‍🔬 Fill in Settings (university, names, contacts, ethics status, retention, apparatus, recruitment)
- 🧑‍🔬 Set secrets in `.env`
- 🧑‍🔬 Human pilot testing (3–5 volunteers), complete checklist, record observations, calibrate, lock configuration
- 🧑‍🔬 Recruit and test ≥ 20 eligible adult participants (or upload externally collected data)
- 🧑‍🔬 Run analysis, generate final report and presentation
- 🧑‍🔬 Review, edit and approve all interpretations; write the comparison-with-literature paragraph
- 🧑‍🔬 Prepare viva answers about the actual results

## Submission checklist
- [ ] Locked configuration version recorded in the report
- [ ] ≥ 20 eligible completers; exclusions documented
- [ ] De-identified data export (.xlsx) — no contacts file
- [ ] Final report (PDF/DOCX) reviewed; all "[…]" placeholders replaced; no auto-draft flags left unaddressed
- [ ] `SMIT_Statistical_Results.xlsx` and figures
- [ ] Presentation updated with your own wording
- [ ] Human pilot checklist completed; technical dry-run report included
- [ ] No synthetic data or test artefacts in the submission
