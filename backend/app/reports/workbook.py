"""Excel data-collection workbook and CSV templates.

The same writer produces (a) the blank templates shipped with the project and
(b) filled workbooks for software tests (synthetic, clearly labelled) — it never
invents participant data by itself.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from ..data_dictionary import (
    CONTACT_VARS,
    PARTICIPANT_VARS,
    SESSION_VARS,
    SUMMARY_CALCULATED,
    SUMMARY_VARS,
    TRIAL_VARS,
    Var,
)
from ..experiment.config import ExperimentConfig

HEADER_FILL = PatternFill("solid", fgColor="1F3A93")
CALC_FILL = PatternFill("solid", fgColor="E7E6E6")
CONF_FILL = PatternFill("solid", fgColor="FDE9D9")
REQ_FONT = Font(bold=True, color="FFFFFF")
OPT_FONT = Font(bold=False, color="FFFFFF", italic=True)
THIN = Side(style="thin", color="BFBFBF")
N_ROWS = {"Participants": 60, "Contacts": 60, "Sessions": 60, "Raw_Trials": 5000}


def _fmt_for(v: Var) -> str | None:
    if v.type == "int":
        return "0"
    if v.type == "float":
        return "0.000" if "proportion" in v.unit else "0.0"
    if v.type in ("str", "pattern", "enum", "datetime"):
        return "@"
    return None


def _write_sheet(wb: Workbook, name: str, vars_: list[Var], df: pd.DataFrame | None, *, confidential=False) -> None:
    ws = wb.create_sheet(name)
    for j, v in enumerate(vars_, start=1):
        c = ws.cell(row=1, column=j, value=v.name)
        c.fill = HEADER_FILL
        c.font = REQ_FONT if v.required else OPT_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        text = f"{v.description}\nType: {v.type}{' (' + v.unit + ')' if v.unit else ''}\n" \
               f"{'REQUIRED' if v.required else 'Optional'}" + (f"\nAllowed: {', '.join(v.allowed)}" if v.allowed else "")
        c.comment = Comment(text, "SMIT")
        ws.column_dimensions[get_column_letter(j)].width = max(14, min(34, len(v.name) + 4))
    n_rows = N_ROWS.get(name, 60)
    if df is not None and len(df):
        n_rows = max(n_rows, len(df) + 20)
        for i, row in enumerate(df.itertuples(index=False), start=2):
            for j, v in enumerate(vars_, start=1):
                val = getattr(row, v.name, None) if v.name in df.columns else None
                if isinstance(val, float) and pd.isna(val):
                    val = None
                if v.type == "bool" and val is not None and not isinstance(val, bool):
                    val = str(val).upper() in ("TRUE", "1")
                ws.cell(row=i, column=j, value=val)
    for j, v in enumerate(vars_, start=1):
        fmt = _fmt_for(v)
        col = get_column_letter(j)
        if fmt and fmt != "@":
            for r in range(2, n_rows + 2):
                ws[f"{col}{r}"].number_format = fmt
        if v.derived:
            for r in range(2, min(n_rows + 2, 400)):
                ws[f"{col}{r}"].fill = CALC_FILL
        if confidential:
            for r in range(2, n_rows + 2):
                ws[f"{col}{r}"].fill = CONF_FILL
        allowed = v.allowed if v.type in ("enum", "bool") else ()
        if allowed:
            dv = DataValidation(type="list", formula1='"' + ",".join(allowed) + '"', allow_blank=not v.required,
                                showErrorMessage=True, errorTitle="Invalid value",
                                error=f"Allowed: {', '.join(allowed)}")
            dv.add(f"{col}2:{col}{n_rows + 1}")
            ws.add_data_validation(dv)
        elif v.type in ("int", "float") and (v.min is not None or v.max is not None):
            dv = DataValidation(type="decimal" if v.type == "float" else "whole", operator="between",
                                formula1=str(v.min if v.min is not None else -1e9), formula2=str(v.max if v.max is not None else 1e9),
                                allow_blank=True, showErrorMessage=True, error=f"Must be between {v.min} and {v.max}")
            dv.add(f"{col}2:{col}{n_rows + 1}")
            ws.add_data_validation(dv)
    ws.freeze_panes = "B2" if name == "Raw_Trials" else "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(vars_))}{n_rows + 1}"
    ws.row_dimensions[1].height = 32


def _summary_sheet(wb: Workbook) -> None:
    """Participant_Summary: CALCULATED from Raw_Trials with Excel formulas (no manual calculation)."""
    ws = wb.create_sheet("Participant_Summary")
    tcol = {v.name: get_column_letter(i) for i, v in enumerate(TRIAL_VARS, start=1)}
    last = N_ROWS["Raw_Trials"] + 1

    def rng(name: str) -> str:
        return f"Raw_Trials!${tcol[name]}$2:${tcol[name]}${last}"

    cols = ["participant_id", "age", "gender", "academic_course"] + [v.name for v in SUMMARY_CALCULATED]
    for j, name in enumerate(cols, start=1):
        c = ws.cell(row=1, column=j, value=name)
        c.fill = HEADER_FILL
        c.font = REQ_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = max(14, min(30, len(name) + 2))
    desc = {v.name: v.description for v in SUMMARY_CALCULATED}
    for j, name in enumerate(cols, start=1):
        if name in desc:
            ws.cell(row=1, column=j).comment = Comment(desc[name] + "\nCALCULATED — do not type here.", "SMIT")
    base = lambda pid, cond: (f"({rng('participant_id')}={pid})*({rng('condition')}=\"{cond}\")*"  # noqa: E731
                              f"(({rng('practice_trial')}=FALSE)+({rng('practice_trial')}=\"FALSE\"))*(({rng('exclusion_status')}<>\"excluded\"))")
    correct = f"({rng('participant_response')}={rng('correct_answer')})*({rng('participant_response')}<>\"\")"
    rt_ok = f"({rng('reaction_time_ms')}>=200)*ISNUMBER({rng('reaction_time_ms')})"
    for r in range(2, N_ROWS["Participants"] + 2):
        pid = f"$A{r}"
        ws[f"A{r}"] = f'=IF(Participants!A{r}="","",Participants!A{r})'
        ws[f"B{r}"] = f'=IF(A{r}="","",Participants!B{r})'
        ws[f"C{r}"] = f'=IF(A{r}="","",Participants!C{r})'
        ws[f"D{r}"] = f'=IF(A{r}="","",Participants!D{r})'
        f = {}
        for cond, nm in (("A", "control"), ("B", "numerical"), ("C", "visual")):
            n = f"SUMPRODUCT({base(pid, cond)})"
            f[f"{nm}_accuracy"] = f"IFERROR(SUMPRODUCT({base(pid, cond)}*{correct})/{n},\"\")"
            f[f"{nm}_mean_correct_rt_ms"] = (f"IFERROR(SUMPRODUCT({base(pid, cond)}*{correct}*{rt_ok}*{rng('reaction_time_ms')})/"
                                            f"SUMPRODUCT({base(pid, cond)}*{correct}*{rt_ok}),\"\")")
        col = {name: get_column_letter(j) for j, name in enumerate(cols, start=1)}
        for k, v in f.items():
            ws[f"{col[k]}{r}"] = f'=IF($A{r}="","",{v})'
        ws[f"{col['numerical_accuracy_cost']}{r}"] = f'=IFERROR({col["control_accuracy"]}{r}-{col["numerical_accuracy"]}{r},"")'
        ws[f"{col['visual_accuracy_cost']}{r}"] = f'=IFERROR({col["control_accuracy"]}{r}-{col["visual_accuracy"]}{r},"")'
        ws[f"{col['numerical_rt_cost_ms']}{r}"] = f'=IFERROR({col["numerical_mean_correct_rt_ms"]}{r}-{col["control_mean_correct_rt_ms"]}{r},"")'
        ws[f"{col['visual_rt_cost_ms']}{r}"] = f'=IFERROR({col["visual_mean_correct_rt_ms"]}{r}-{col["control_mean_correct_rt_ms"]}{r},"")'
        allp = (f"({rng('participant_id')}={pid})*(({rng('practice_trial')}=FALSE)+({rng('practice_trial')}=\"FALSE\"))*({rng('exclusion_status')}<>\"excluded\")")
        ws[f"{col['timeout_rate']}{r}"] = f'=IF($A{r}="","",IFERROR(SUMPRODUCT({allp}*({rng("participant_response")}=""))/SUMPRODUCT({allp}),""))'
        ws[f"{col['overall_accuracy']}{r}"] = f'=IF($A{r}="","",IFERROR(SUMPRODUCT({allp}*{correct})/SUMPRODUCT({allp}),""))'
        ws[f"{col['overall_mean_correct_rt_ms']}{r}"] = (
            f'=IF($A{r}="","",IFERROR(SUMPRODUCT({allp}*{correct}*{rt_ok}*{rng("reaction_time_ms")})/SUMPRODUCT({allp}*{correct}*{rt_ok}),""))')
        for j, name in enumerate(cols, start=1):
            cell = ws.cell(row=r, column=j)
            cell.fill = CALC_FILL
            if "accuracy" in name or "rate" in name:
                cell.number_format = "0.000"
            elif "rt" in name:
                cell.number_format = "0.0"
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{N_ROWS['Participants'] + 1}"
    note_row = N_ROWS["Participants"] + 3
    ws[f"A{note_row}"] = ("CALCULATED SHEET — values are formulas computed from Raw_Trials (timeouts count as errors; RT = correct "
                          "trials ≥ 200 ms). Timing-quality exclusions and the pre-specified participant exclusion rules are applied "
                          "only by the SMIT application's analysis.")
    ws[f"A{note_row}"].font = Font(italic=True)


def _flatten(d: dict, prefix="") -> list[tuple[str, str]]:
    out = []
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.extend(_flatten(v, key + "."))
        else:
            out.append((key, json.dumps(v) if isinstance(v, list) else v))
    return out


INSTRUCTIONS = [
    ("SMIT Data Collection Template", None),
    ("Purpose", "Use this workbook ONLY if data are collected outside the SMIT application (e.g. on paper or another tool). "
                "Data collected with the application are stored automatically and do not need this workbook."),
    ("Never invent data", "Enter only genuine observations. Leave cells blank where a value was not recorded."),
    ("Sheets to fill in", "Participants, Contacts (CONFIDENTIAL), Sessions and Raw_Trials. Participant_Summary is CALCULATED "
                          "automatically (grey cells). Data_Dictionary and Experiment_Configuration are reference sheets."),
    ("Column headers", "Do not rename, delete or reorder header cells. Bold headers are REQUIRED; italic headers are optional. "
                       "Hover over a header to see its definition."),
    ("Identifiers", "participant_id: letters, digits, '-' and '_' only (e.g. P001). session_id: e.g. S-P001-1. Never use names or "
                    "emails as identifiers."),
    ("Allowed values", "Dropdown lists enforce allowed values (gender, condition A/B/C, TRUE/FALSE, same/different, true/false, "
                       "condition_order, session_type, completion_status)."),
    ("Patterns", "Cell numbers 0–8 in reading order (top-left = 0, top-right = 2, bottom-right = 8) separated by '-', e.g. 0-2-5-7. "
                 "A 'different' recognition pattern has exactly one cell moved."),
    ("Missing values", "Leave the cell EMPTY. Do not type NA, -, 0 or 999. A missing participant_response means no response "
                       "(timeout); in that case also leave reaction_time_ms empty."),
    ("Calculated fields", "is_correct, response_timeout, interference_accuracy and timing_quality_flag are recalculated by the "
                          "application. If you fill them in and they conflict with the raw data, the import is rejected with a "
                          "row-level error (the application never silently corrects them)."),
    ("Units", "Times in milliseconds (ms). Proportions between 0 and 1. Dates/times in ISO format, e.g. 2026-12-01T10:15:00."),
    ("Practice trials", "Enter practice trials with practice_trial = TRUE and block_number = 0; they are excluded from analysis."),
    ("Confidentiality", "The Contacts sheet contains identifying information. Store this file securely, never share it, and "
                        "delete it once data have been imported. Emails never appear in analyses or reports."),
    ("Upload", "Researcher dashboard → Import / Export → drag this .xlsx file onto the upload area → review the validation "
               "preview → Confirm import. Analysis runs automatically after a successful import."),
    ("Summary-only option", "If trial-level data are unavailable, use Participant_Summary_Template.xlsx instead. Trial-level "
                            "quality checks, timing checks, RT distributions, signal-detection measures, fatigue/order analyses and "
                            "most exclusion rules are then unavailable."),
    ("Formula safety", "Do not enter formulas in data sheets. Text starting with = + - @ is rejected on import."),
]


def build_collection_workbook(path: Path, config: ExperimentConfig, frames: dict[str, pd.DataFrame] | None = None,
                              *, version_label: str = "Default pre-pilot configuration (replace with the locked version)",
                              synthetic: bool = False) -> Path:
    frames = frames or {}
    wb = Workbook()
    ws = wb.active
    ws.title = "Instructions"
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 120
    r = 1
    if synthetic:
        ws.cell(row=r, column=1, value="SYNTHETIC TEST DATA — FOR SOFTWARE VERIFICATION ONLY — NOT REAL PARTICIPANTS").font = Font(bold=True, color="C00000", size=14)
        r += 2
    for title, text in INSTRUCTIONS:
        a = ws.cell(row=r, column=1, value=title)
        a.font = Font(bold=True, size=14 if text is None else 11)
        if text:
            b = ws.cell(row=r, column=2, value=text)
            b.alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r].height = max(18, 15 * (len(text) // 110 + 1))
        r += 1
    r += 1
    ws.cell(row=r, column=1, value="Columns by sheet").font = Font(bold=True, size=12)
    r += 1
    for sheet, vars_ in (("Participants", PARTICIPANT_VARS), ("Contacts", CONTACT_VARS), ("Sessions", SESSION_VARS),
                         ("Raw_Trials", TRIAL_VARS)):
        ws.cell(row=r, column=1, value=sheet).font = Font(bold=True)
        ws.cell(row=r, column=2, value=", ".join(f"{v.name}{'*' if v.required else ''}" for v in vars_)).alignment = Alignment(wrap_text=True)
        r += 1
    ws.cell(row=r, column=2, value="* = required").font = Font(italic=True)

    _write_sheet(wb, "Participants", PARTICIPANT_VARS, frames.get("Participants"))
    _write_sheet(wb, "Contacts", CONTACT_VARS, frames.get("Contacts"), confidential=True)
    _write_sheet(wb, "Sessions", SESSION_VARS, frames.get("Sessions"))
    _write_sheet(wb, "Raw_Trials", TRIAL_VARS, frames.get("Raw_Trials"))
    _summary_sheet(wb)

    dd = wb.create_sheet("Data_Dictionary")
    head = ["sheet", "variable", "type", "unit", "required", "allowed values", "missing-value convention",
            "description", "scientific interpretation", "calculated"]
    for j, h in enumerate(head, start=1):
        c = dd.cell(row=1, column=j, value=h)
        c.fill = HEADER_FILL
        c.font = REQ_FONT
    rr = 2
    for sheet, vars_ in (("Participants", PARTICIPANT_VARS), ("Contacts", CONTACT_VARS), ("Sessions", SESSION_VARS),
                         ("Raw_Trials", TRIAL_VARS), ("Participant_Summary (calculated)", SUMMARY_CALCULATED),
                         ("Participant_Summary_Template (import)", SUMMARY_VARS)):
        for v in vars_:
            vals = [sheet, v.name, v.type, v.unit, "yes" if v.required else "no", ", ".join(map(str, v.allowed)),
                    v.missing, v.description, v.interpretation, "yes" if v.derived else "no"]
            for j, val in enumerate(vals, start=1):
                dd.cell(row=rr, column=j, value=val).alignment = Alignment(wrap_text=True, vertical="top")
            rr += 1
    for j, w in enumerate([22, 30, 9, 16, 9, 30, 26, 60, 50, 10], start=1):
        dd.column_dimensions[get_column_letter(j)].width = w
    dd.freeze_panes = "C2"
    dd.auto_filter.ref = f"A1:J{rr - 1}"

    ec = wb.create_sheet("Experiment_Configuration")
    ec["A1"], ec["B1"] = "parameter", "value"
    for c in (ec["A1"], ec["B1"]):
        c.fill = HEADER_FILL
        c.font = REQ_FONT
    ec["A2"], ec["B2"] = "experiment_version", version_label
    ec["A3"], ec["B3"] = "config_hash", config.canonical_hash()
    for i, (k, v) in enumerate(_flatten(config.to_json_dict()), start=4):
        ec.cell(row=i, column=1, value=k)
        ec.cell(row=i, column=2, value=v)
    ec.column_dimensions["A"].width = 48
    ec.column_dimensions["B"].width = 60
    ec.freeze_panes = "A2"

    if synthetic:
        s = wb.create_sheet("SYNTHETIC_DATA_NOTICE", 0)
        s["A1"] = "SYNTHETIC TEST DATA — generated by automated tests. NOT real participants. Must never be submitted or imported into the research database."
        s["A1"].font = Font(bold=True, color="C00000", size=14)
    for wsx in wb.worksheets:
        for row in wsx.iter_rows(min_row=1, max_row=1):
            for c in row:
                c.border = Border(bottom=THIN)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def build_summary_template(path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Participant_Summary"
    _fill_header(ws, SUMMARY_VARS)
    n = 60
    for j, v in enumerate(SUMMARY_VARS, start=1):
        col = get_column_letter(j)
        fmt = _fmt_for(v)
        if fmt and fmt != "@":
            for r in range(2, n + 2):
                ws[f"{col}{r}"].number_format = fmt
        if v.allowed and v.type in ("enum", "bool"):
            dv = DataValidation(type="list", formula1='"' + ",".join(v.allowed) + '"', allow_blank=not v.required, showErrorMessage=True)
            dv.add(f"{col}2:{col}{n + 1}")
            ws.add_data_validation(dv)
        elif v.type == "float" and v.max == 1:
            dv = DataValidation(type="decimal", operator="between", formula1="0", formula2="1", allow_blank=True, showErrorMessage=True,
                                error="Proportion between 0 and 1")
            dv.add(f"{col}2:{col}{n + 1}")
            ws.add_data_validation(dv)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(SUMMARY_VARS))}{n + 1}"
    info = wb.create_sheet("Instructions")
    lines = [
        "OPTIONAL simplified import format: one row per participant with condition-level summaries.",
        "Use only if trial-level data (SMIT_Data_Collection_Template.xlsx → Raw_Trials) are not available.",
        "Accuracy = proportion correct (0–1) with timeouts counted as errors. RT = mean of correct trials in ms.",
        "UNAVAILABLE with summary-only data: trial-level validation, timing-quality checks, exclusion rules 2–5 "
        "(valid-trial counts, timeouts, response bias, secondary-task engagement unless provided), RT distributions, "
        "hit/false-alarm rates, d′ and K, learning/fatigue and block-order analyses, and verification of same/different balance.",
        "Never invent values. Leave a cell blank if it was not measured.",
    ]
    for i, l in enumerate(lines, start=1):
        info.cell(row=i, column=1, value=l).alignment = Alignment(wrap_text=True)
    info.column_dimensions["A"].width = 140
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def _fill_header(ws, vars_: list[Var]) -> None:
    for j, v in enumerate(vars_, start=1):
        c = ws.cell(row=1, column=j, value=v.name)
        c.fill = HEADER_FILL
        c.font = REQ_FONT if v.required else OPT_FONT
        c.comment = Comment(v.description, "SMIT")
        ws.column_dimensions[get_column_letter(j)].width = max(14, min(32, len(v.name) + 4))


def write_csv_templates(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    out = []
    for fname, vars_ in (("Participant_Template.csv", PARTICIPANT_VARS), ("Contacts_Template_CONFIDENTIAL.csv", CONTACT_VARS),
                         ("Session_Template.csv", SESSION_VARS), ("Trial_Data_Template.csv", TRIAL_VARS),
                         ("Participant_Summary_Template.csv", SUMMARY_VARS)):
        p = directory / fname
        with p.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([v.name for v in vars_])
        out.append(p)
    return out
