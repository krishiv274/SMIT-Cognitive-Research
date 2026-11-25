# RESEARCHER GUIDE

Start the application (`./scripts/start.sh`, see SETUP.md) and open **http://127.0.0.1:8000/researcher**. Log in with `SMIT_ADMIN_PASSWORD`.

## 1. Configure the experiment

*Configuration* lists all versions. Version 1 is the default from the specification (500 ms fixation, 500 ms memory stimulus, 3,000 ms interference, 1,000 ms retention, 2,000 ms deadline, 800–1,200 ms ITI, 4 cells, 20 trials per condition).
- **Edit** a draft (or **Copy to draft** for a locked one), change parameters, add a note explaining why, and **Save as new draft version**. Each version gets an identifier such as `SMIT-v3-1a2b3c4d`.
- Differences from the original specification are listed for every version — you must justify them in the report.
- *Advanced JSON* exposes every parameter (colours, keys, secondary-task settings, analysis thresholds).

## 2. Run a technical dry run

Already done for the software (see `pilot/Technical_Dry_Run_Report.md`). Re-run on the **testing computer** before piloting:
```bash
./scripts/run_all_tests.sh
```
Then do one pilot session yourself (step 3) and inspect *Pilot mode → Inspect*: the refresh rate should be detected correctly and nearly all trials flagged `ok`.

## 3. Conduct human pilot testing

Follow `experiment/documentation/Pilot_Testing_Protocol.md` with 3–5 volunteers who will not be in the main study. *Pilot mode → Start pilot session* opens a pilot participant tab (data stored as pilot, never analysed). Complete `pilot/Human_Pilot_Testing_Checklist.xlsx` and write your observations in *Settings → Human pilot testing* (they go into the report). Adjust one parameter at a time and re-pilot.

## 4. Finalise and lock the configuration

*Configuration → Lock* on the chosen draft; write the justification (e.g. pilot results). The main study opens immediately and every session records the version. Locked versions cannot be edited; a later change creates a new version and is an audited protocol deviation.

## 5. Recruit participants

Adults (18+), not involved in the pilot, normal or corrected vision, able to distinguish blue/orange. Target ≥ 20 completers; recruiting ~24 balances all six orders (4 each) and allows for exclusions. Fill in *Settings* (university, contacts, ethics status, withdrawal deadline, retention, apparatus, recruitment) — these appear on the consent screen and in the report. Never state ethics approval that was not granted.

## 6. Conduct the main experiment

Same computer, monitor, wired keyboard and quiet room for everybody; close other apps; disable notifications. Open `/participate`, let the participant read and consent, stay nearby during practice, then leave them to work. After completion, check the *Participants* page shows the session as `completed` with 60/60 trials. Briefly debrief (do not reveal hypotheses beforehand).

## 7. Collect participant information

Collected automatically on screen 3 (age, gender, course, email). Emails are visible only via *Participants → reveal* (logged) or *Contacts (confidential)* export. Condition order is assigned automatically.

## 8. Export data

*Import / Export* or *Participants*: de-identified **.xlsx / .csv (zip) / .json** for main, pilot or all data. Exports never include emails.

## 9. Complete the Excel template (only if data were collected outside the app)

Download `SMIT_Data_Collection_Template.xlsx` (*Import / Export → Templates*). Fill **Participants, Contacts, Sessions, Raw_Trials** following the *Instructions* and *Data_Dictionary* sheets (dropdowns enforce allowed values; leave missing values blank; never invent data). *Participant_Summary* calculates itself. If you only have per-participant summaries, use `Participant_Summary_Template.xlsx` (reduced analyses — listed in its instructions). CSV equivalents are in `templates/`.

## 10. Upload genuine participant data

*Import / Export* → drag the workbook (or the CSV files together, or a SMIT `.json` export) onto the upload area.

## 11. Validate the dataset

The preview shows counts, **row-level errors** (sheet, row, column, problem), warnings, missing values, recalculated accuracy per participant and the first rows of each sheet. Errors block the import — fix the file and upload again (nothing is corrected silently). If it passes, **Confirm import** commits everything in one transaction, logs it, and runs the analysis automatically. The same file cannot be imported twice and existing participants are never overwritten.

## 12. Generate statistical analyses

*Analysis → Run Analysis*. The pipeline applies the pre-specified exclusion rules, chooses parametric or nonparametric tests by the pre-registered criteria (and says why), and shows hypothesis outcomes, omnibus and Holm-corrected pairwise tests with effect sizes, descriptives, manipulation check, sensitivity analyses, exploratory correlations and group comparisons, data quality and exclusions. With fewer than 3 eligible participants results are marked pending.

## 13. Download graphs

*Analysis → Publication figures*: each of the 18 figures as PNG, SVG or PDF, or *Download all (zip)*. Figures are not generated when their data are insufficient (the reason is shown).

## 14. Generate the final research report

*Reports → Generate Research Report* produces PDF, DOCX, HTML and `SMIT_Statistical_Results.xlsx` from the latest analysis run. Without eligible data a **preliminary** report (results pending) is produced. Automatically drafted Discussion/Conclusion text is clearly flagged: **read, edit (in the DOCX) and approve every interpretation**. To change theory sections, edit the Markdown in `research/` and regenerate.

## 15. Regenerate the final presentation

*Reports → Regenerate presentation* rebuilds `SMIT_Presentation.pptx` with the results slides filled from the latest analysis. Edit the slides afterwards for your own wording.

## 16. Prepare the submission

- Functional task: this repository (source + `README.md`/`SETUP.md`).
- Data: de-identified export (.xlsx) of the main study — **never** the contacts file.
- Report: generated final report (edited and approved), statistical results workbook, figures.
- Presentation and `presentation/VIVA_Preparation.md` (add your actual results).
- Pilot documentation: completed `Human_Pilot_Testing_Checklist.xlsx`, `Technical_Dry_Run_Report.md`.
- Check that no synthetic file or test artefact is included (`tests/artifacts/` is git-ignored; any report built from synthetic data carries a SYNTHETIC watermark).
- Back up `data/smit.db` securely, then apply the retention plan.
