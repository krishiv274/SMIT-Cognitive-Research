# SMIT Software Architecture

## 1. Overview

```
┌──────────────────────── Browser (testing computer) ───────────────────────┐
│  React + TypeScript + Tailwind (Vite build)                                │
│  ├─ Participant app  (/participate)  welcome → consent → registration →    │
│  │     instructions → practice → 3 blocks → completion                     │
│  │     Trial engine: plain TypeScript, <canvas> stimuli, requestAnimation- │
│  │     Frame scheduling, performance.now()/event.timeStamp timing          │
│  └─ Researcher dashboard (/researcher) overview, participants, config,     │
│        pilot mode, import/export, analysis (Plotly), reports, settings    │
└───────────────▲────────────────────────────────────────────────────────────┘
                │ JSON over HTTP (same origin; served by FastAPI in production)
┌───────────────┴──────────── FastAPI (Python) ─────────────────────────────┐
│  api/participant.py  public: study info, registration, trial upload       │
│  api/admin.py        researcher (token auth): participants, configs, ...   │
│  api/imports.py      upload → validate → preview → commit                  │
│  api/analysis.py     run analysis, results JSON, figure downloads          │
│  api/reports.py      report / Excel results / presentation generation      │
│  experiment/         config schema, deterministic trial-plan generator     │
│  services/           sessions, configs, timing QA, dataset, importer       │
│  analysis/           cleaning, descriptives, inferential, figures          │
│  reports/            document model → HTML / DOCX / PDF, PPTX, XLSX        │
└───────────────▲────────────────────────────────────────────────────────────┘
                │ SQLAlchemy 2.x
        SQLite (data/smit.db)  — or PostgreSQL via SMIT_DATABASE_URL
```

### Key decisions

| Decision | Rationale |
|---|---|
| **Custom TypeScript trial engine instead of jsPsych** | SMIT needs frame-counted phase durations, a secondary task embedded inside a fixed-length phase, and per-phase measured durations, all with a testable, dependency-free scheduler. A small purpose-built engine (≈ 400 lines) is easier to verify with unit tests (fake 60 Hz clock) than a jsPsych plugin. jsPsych's own timing approach (requestAnimationFrame, `performance.now`) is followed (de Leeuw, 2015). |
| **Server-generated trial plan** | The plan is a pure function of (locked config, seed, condition order); generated in Python, stored with the session and executed by the browser. Reproducible, unit-testable, and the server re-derives correctness from its own plan (the client cannot alter stimuli or answers). |
| **Canvas rendering** | Drawing the grid on a canvas inside the animation-frame callback avoids React re-render latency and guarantees identical geometry on every trial. |
| **Per-trial upload + local retry queue** | Each trial is POSTed immediately (idempotent on `session_id + practice + attempt + trial_number`); failures are queued in `localStorage` and retried, and the session can be resumed after a crash without creating a duplicate session. |
| **SQLite by default** | Zero setup, single file, local-only storage (privacy). PostgreSQL is supported by setting `SMIT_DATABASE_URL`. |
| **Report document model** | Report content is built once as a list of blocks (heading, paragraph, table, figure) and rendered to HTML, DOCX (python-docx) and PDF (ReportLab, pure Python — no system libraries). |
| **One analysis pipeline** | App-collected and imported data are stored in the same tables and analysed by the same code. |

## 2. Participant state machine

```
WELCOME ──► CONSENT ──(declined)──► END (nothing stored)
              │ consent
              ▼
         REGISTRATION ──► POST /sessions (participant + contact + session + plan)
              ▼
         INSTRUCTIONS ──► REFRESH-RATE CHECK ──► FULLSCREEN
              ▼
         PRACTICE (6 trials, feedback) ──► PRACTICE END ──(repeat ≤ 2)──┐
              │                                ▲─────────────────────────┘
              ▼ start main
   ┌─► BLOCK INSTRUCTIONS (condition-specific)
   │        ▼
   │   TRIALS ×20 (no feedback) ── each trial saved ──► server
   │        ▼
   └── BREAK (≥ 20 s) ◄── until 3 blocks done
              ▼
         UPLOAD CHECK (flush queue) ──► POST /complete ──► COMPLETION (participant ID, save status)
Esc at any time ──► PAUSE ──► resume | withdraw (session marked withdrawn)
Crash / reload  ──► resume prompt ──► continue from first unsaved trial (interruption logged)
```

## 3. Trial state machine (one trial)

```
FIXATION ─(N_fix frames)─► MEMORY ─(N_mem frames)─► [BLANK] ─► INTERFERENCE (fixed N_int frames;
secondary stimulus until response, then dot) ─► RETENTION ─(N_ret frames)─► PROBE (until key or
deadline) ─► [PRACTICE FEEDBACK] ─► ITI (jittered) ─► next trial
```

Keyboard handling: `keydown` only; `event.repeat` ignored; only the first valid key inside the current response window is accepted; keys pressed during fixation/memory/retention/ITI are counted as `premature_keypresses` and otherwise ignored.

## 4. Database

See `database/schema/schema_sqlite.sql` (generated) and `database/schema/README.md` (entity–relationship description). Email addresses exist only in `participant_contacts`.

## 5. Import/export formats

| Format | Content |
|---|---|
| `.xlsx` full workbook | `SMIT_Data_Collection_Template.xlsx` sheets Participants, Contacts, Sessions, Raw_Trials (others are informational) |
| `.csv` (multiple files) | `Participant_Template.csv`, `Session_Template.csv`, `Trial_Data_Template.csv` (+ optional contacts CSV) uploaded together |
| `.json` | The application's own de-identified export format (round-trip) |
| Summary-only `.xlsx` / `.csv` | `Participant_Summary_Template.xlsx` — one row per participant (reduced analyses) |

## 6. Security and privacy

- Researcher endpoints require a bearer token obtained with `SMIT_ADMIN_PASSWORD`; tokens are HMAC-signed with `SMIT_SECRET_KEY` and expire (default 12 h).
- Participant sessions use an unguessable session token (only its SHA-256 hash is stored).
- Email addresses are stored separately, de-duplicated with a peppered HMAC hash, excluded from every research export/report, and viewing/exporting them is audit-logged.
- SQL is generated by SQLAlchemy with bound parameters (no string-built SQL).
- Uploads: size limit, extension + magic-byte check, `defusedxml`-protected XLSX parsing, formulas never evaluated (cell values only), text cells starting with `= + - @` rejected in identifier fields and neutralised in exports.
- Security headers (`nosniff`, `DENY` framing, no referrer); CORS limited to the local dev origin.
- No third-party services or telemetry. See `docs/Security_and_Deployment.md`.
