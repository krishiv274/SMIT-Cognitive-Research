# Research Protocol — SMIT

**Title:** Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory and Cognitive Performance Among University Students
**Short name:** SMIT — Spatial Memory Interference Task
**Type:** Student research project (Cognitive Psychology course). No claim of institutional ethics approval is made unless one is obtained and recorded in *Settings → Ethics statement*.

Related documents: `Research_Question_and_Hypotheses.md`, `Experimental_Design.md`, `Statistical_Analysis_Plan.md`, `Theoretical_Framework.md`, `Literature_Review.md`, `Lecture_Concept_Mapping.md`, `Informed_Consent.md`, `Participant_Instructions.md`, `../experiment/documentation/Pilot_Testing_Protocol.md`.

## 1. Background and rationale

Spatial working memory supports everyday activities such as navigation, reading maps and following diagrams, and is a core component of academic skills in mathematics and science. Theories disagree about whether interference with working memory depends on the *content* of competing activity (domain-specific accounts) or mainly on how much *attention* it captures (domain-general accounts). SMIT compares a numerical and a visuospatial secondary task against a no-load control in a within-subjects design, using a change-detection recognition test of a spatial pattern.

## 2. Objectives

1. Test whether numerical and visual interference during retention reduce spatial recognition accuracy (H1, H2) and whether visual interference is more disruptive (H3).
2. Test whether interference affects recognition RT (H4).
3. Explore relationships between performance, interference costs, age, gender and academic course (RQ2).

## 3. Participants

- **Target:** at least 20 eligible participants who complete the experiment (assignment requirement). Recruiting 24 allows each counterbalancing order to be used 4 times and leaves margin for exclusions.
- **Recruitment:** convenience sample of university students via class announcements/messages. Participation is voluntary; no course credit is linked to performance.
- **Inclusion criteria:** age ≥ 18; normal or corrected-to-normal vision; able to use a keyboard; informed consent given.
- **Exclusion criteria (before testing):** participation in the pilot; self-reported photosensitive epilepsy; colour-vision difficulty that prevents distinguishing blue from orange (ask at recruitment); having seen the hypotheses.
- **Analysis exclusions:** pre-specified in `Statistical_Analysis_Plan.md §4`.

## 4. Apparatus and software

- One desktop or laptop computer used for all participants (record model, OS, browser, monitor size/refresh rate in *Settings → Apparatus*), a wired USB keyboard, quiet room.
- SMIT web application (React/TypeScript front end; FastAPI/Python back end; SQLite database) running locally; stimuli rendered on an HTML canvas synchronised to the display refresh.
- Chrome or Edge (latest stable) in full-screen mode; notifications disabled.

## 5. Procedure

1. Researcher starts the application and opens the participant screen on the testing computer.
2. Welcome screen → information sheet and consent (screen 2). If consent is not given, the session ends and nothing is stored.
3. Registration (age, gender, course, email). Participant ID generated automatically.
4. Instructions with visual examples; refresh-rate check.
5. Practice: 6 trials with feedback; may be repeated (max 2 repeats).
6. Main task: 3 blocks × 20 trials in the assigned counterbalanced order, with ≥ 20 s breaks.
7. Completion screen showing the participant ID and confirmation that the data were saved.
8. Brief verbal debrief (purpose of the study explained; hypotheses can be shared after participation). Ask the participant not to discuss the task with other potential participants.

## 6. Ethics and data protection

- Informed consent obtained electronically before any data are recorded.
- Minimal risk; right to withdraw at any time and to request deletion later using the participant ID.
- Identifying data (email) stored in a separate table, never exported with research data, never shown in reports; access requires researcher login and is logged.
- All data stored locally; no third-party transmission.
- **Data retention:** contact details deleted after the course assessment period; de-identified data retained only as long as required for assessment (set exact dates in the consent form).
- **Backups:** the SQLite database file `data/smit.db` should be backed up after each testing day to an encrypted drive (e.g. `scripts/backup_database.sh`), and the backup deleted at the end of the retention period.

## 7. Data management

- Trial data are saved to the server after each trial, with a local retry queue in the browser; sessions can be resumed after interruption without duplicating trials.
- Pilot and main data are separated by `session_type`; synthetic test fixtures are confined to temporary test databases and are labelled `SYNTHETIC`.
- The experiment configuration is locked and versioned before the main study.
- Data exported in de-identified form (XLSX/CSV/JSON) for the submission.

## 8. Statistical analysis

See `Statistical_Analysis_Plan.md`.

## 9. Limitations anticipated at design stage

- **Sample size:** N ≈ 20 provides adequate power only for medium-to-large within-subject effects (d_z ≥ 0.66).
- **Convenience sampling** of students limits generalisability; age range will be narrow, which limits age analyses.
- **Demographic imbalance:** gender/course groups may be too small for inference.
- **Browser and hardware timing** is not laboratory-grade; mitigated by a single standardised device and logged timing.
- **Secondary-task difficulty** may differ between numerical and visual tasks; measured and reported.
- **Construct validity:** the control condition has no secondary response; recognition with a whole-display probe may be supported by holistic familiarity.
- **Practice and fatigue effects:** mitigated by counterbalancing and breaks, but not eliminated.
- **Shared response keys** between secondary and recognition tasks may create response carry-over.

## 10. Timeline (to be completed by the team)

| Step | Planned date | Done |
|---|---|---|
| Technical dry run | | |
| Human pilot testing (3–5 people) | | |
| Configuration locked | | |
| Main data collection (≥ 20 participants) | | |
| Analysis and report | | |
| Submission | | |
