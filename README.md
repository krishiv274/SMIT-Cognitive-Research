# SMIT — Spatial Memory Interference Task

**Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory and Cognitive Performance Among University Students**

A complete, locally-run research application for a university Cognitive Psychology project: a frame-synchronised cognitive task, a researcher dashboard, Excel/CSV data import, a pre-specified statistical analysis pipeline, and automatic generation of the research report, results workbook and presentation.

> **New here? Read [SIMPLE_GUIDE.md](SIMPLE_GUIDE.md) first.**

> **Status:** software complete and tested. **No participant data exist.** Human pilot testing, genuine data collection (≥ 20 participants) and review of the findings remain for the research team. Results sections of the report are marked *pending* until real data are analysed.

## Scientific purpose

- **RQ1:** How do numerical and visual interference during the retention interval affect spatial working-memory recognition accuracy and RT?
- **RQ2 (exploratory):** How does performance vary with age, gender and course; how are accuracy, RT and interference costs related?
- **Design:** within-subjects; A = control, B = arithmetic verification, C = spatial symmetry judgement; 6 practice + 60 trials (20/condition, 10 same/10 different); all six block orders counterbalanced.
- **Trial:** fixation 500 ms → 3×3 grid with 4 blue cells 500 ms → interference 3,000 ms → retention 1,000 ms → probe (same / one cell moved, F/J, ≤ 2,000 ms) → ITI 800–1,200 ms.
- **Framework:** custom adaptation of visual change detection + complex span + selective-interference paradigms (no claim of a new paradigm). See `research/`.

## Features

- Participant app: welcome, consent, registration, illustrated instructions, practice with feedback (repeatable), full-screen blocks, standardised breaks, pause/withdraw, completion with save confirmation, crash resume without duplicate sessions.
- Trial engine: canvas stimuli; requestAnimationFrame phase scheduling in whole frames; refresh-rate estimation; planned vs measured duration of every phase; dropped-frame and focus-loss detection; first-key-only, auto-repeat-safe responses; premature-key counting; deadline handling; per-trial upload with offline retry queue.
- Server-generated reproducible trial plans (seeded), persistent counterbalancing, versioned and lockable configurations with audit history, pilot/main separation.
- Researcher dashboard (light/dark): overview & progress, participants (status, withdrawal, deletion, audited contact access), session timing inspector with stimulus previews, configuration editor, pilot mode, import/export (xlsx/csv/json), interactive analysis (Plotly), reports, settings, audit log.
- Import: drag-and-drop; detection of format; validation of sheets, columns, types, IDs, duplicates, missing values, conditions, RTs, relationships, same/different balance, versions; recalculated derived metrics; row-level messages; preview → confirm/cancel; transactional commit; duplicate-file and overwrite protection; automatic analysis.
- Analysis: trial classification (invalid/timeout/incorrect/correct), pre-specified exclusions, descriptives with CIs, RM-ANOVA (Mauchly, Greenhouse–Geisser) or Friedman, paired t/Wilcoxon with Holm, d_z/η²p/r_rb/W, d′, K, IES, interference costs, manipulation check, sensitivity analyses, correlations with CIs, demographic tests with small-group suppression, block-position effects, 18 publication figures (PNG/SVG/PDF).
- Deliverables: report (PDF/DOCX/HTML), `SMIT_Statistical_Results.xlsx`, `SMIT_Presentation.pptx`, Excel/CSV templates, viva preparation.

## Technology

React 19 + TypeScript + Vite + Tailwind CSS · Python 3.14 + FastAPI + Pydantic + SQLAlchemy 2 + Alembic · SQLite (PostgreSQL optional) · pandas, NumPy, SciPy, statsmodels, Pingouin · Matplotlib, Plotly · openpyxl, python-docx, ReportLab, python-pptx · pytest, Vitest, Playwright. A custom TypeScript trial engine replaces jsPsych for testable frame-level control (rationale in `docs/Architecture.md`). All versions are pinned.

## Repository structure

```
backend/            FastAPI app (app/api, app/models, app/services, app/experiment, app/analysis, app/reports), tests/
frontend/           React app (src/participant, src/researcher, src/engine), tests/ (Playwright), unit tests in src/
experiment/         configuration/default_config.json, stimuli/ (diagrams), documentation/ (pilot protocol)
database/           migrations/ (Alembic), schema/ (SQL schema + ER description)
research/           protocol, literature review, framework, hypotheses, SAP, design, lecture mapping, consent, instructions
templates/          SMIT_Data_Collection_Template.xlsx, Participant_Summary_Template.xlsx, CSV templates
pilot/              Technical_Dry_Run_Report.md, Human_Pilot_Testing_Checklist.xlsx
reports/            Preliminary_Research_Report.(pdf|docx|html), report_templates/
presentation/       SMIT_Presentation.pptx, VIVA_Preparation.md
docs/               Architecture.md, Security_and_Deployment.md, screenshots/
scripts/            setup/start (sh, ps1), tests, backups, template/report generators
```

## Installation and running

```bash
./scripts/setup.sh
```

```bash
./scripts/start.sh
```

Then open http://127.0.0.1:8000 (participants: `/participate`, researchers: `/researcher`). Windows, Linux, Docker and development mode: see **SETUP.md**. Set real secrets in `.env` before collecting data.

## Experiment workflow

1. Start the app → 2. human pilot testing (Pilot mode) → 3. lock the configuration → 4. test ≥ 20 participants at `/participate` (or collect externally with the Excel template) → 5. upload external data if any → 6. validate → 7. **Run Analysis** → 8. review results and figures → 9. **Generate Research Report** → 10. download report, results workbook, figures and presentation → 11. review and approve all interpretations. Details: **RESEARCHER_GUIDE.md**. Participant view: **USER_GUIDE.md**.

## Data upload

*Researcher → Import / Export*: drop the completed `SMIT_Data_Collection_Template.xlsx` (or CSVs/JSON). Review row-level validation, then **Confirm import**; analysis runs automatically. No code changes or scripts are needed after data collection.

## Analysis and report generation

*Analysis → Run Analysis*, then *Reports → Generate Research Report* and *Regenerate presentation*. Without eligible data the outputs are explicitly preliminary.

## Testing

`./scripts/run_all_tests.sh` runs 104 backend tests, 20 frontend unit tests and 13 Playwright end-to-end tests on temporary databases with clearly labelled synthetic fixtures. Results: `pilot/Technical_Dry_Run_Report.md`.

## Troubleshooting

See the table in **SETUP.md** (study not open, blank page, port in use, login, timing warnings, reset).

## Integrity commitments

No fabricated participant data, findings, citations (all 44 DOIs verified against Crossref — `research/Reference_Verification_Log.md`), pilot observations or test claims; synthetic data are confined to automated tests and watermarked; hypotheses and analysis plan were fixed before data collection.
