"""Import of externally collected data (Excel / CSV / JSON).

Workflow: upload -> parse -> validate (row-level messages) -> preview -> researcher
confirms -> transactional commit -> audit log -> analysis.

Principles
  * Never evaluate spreadsheet formulas; only stored cell values are read.
  * Never silently correct scientifically important values: conflicts between
    supplied and recalculated values are reported as ERRORS.
  * Never overwrite existing participants; duplicate files are rejected.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..data_dictionary import (
    CONTACT_VARS,
    PARTICIPANT_VARS,
    SESSION_VARS,
    SUMMARY_VARS,
    TRIAL_VARS,
    Var,
)
from ..experiment.config import AnalysisConfig, ExperimentConfig
from ..experiment.plan import pattern_from_str, pattern_to_str
from ..models import (
    ExperimentConfigVersion,
    ExperimentSession,
    ImportBatch,
    ImportedParticipantSummary,
    Participant,
    ParticipantContact,
    Trial,
    utcnow,
)
from ..security import email_hash
from ..settings import get_settings
from .audit import audit
from .timing import assess_timing

ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
EMAIL_RE = re.compile(r"^[^@\s<>\"']{1,64}@[A-Za-z0-9.-]{1,180}\.[A-Za-z]{2,24}$")
MAX_ERRORS = 500


class ImportRejected(Exception):
    pass


@dataclass
class Report:
    format: str = ""
    kind: str = ""
    files: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)
    missing: dict = field(default_factory=dict)
    counts: dict = field(default_factory=dict)
    preview: dict = field(default_factory=dict)
    derived: list = field(default_factory=list)

    def err(self, sheet: str, row: int | None, column: str | None, message: str, value=None) -> None:
        if len(self.errors) < MAX_ERRORS:
            self.errors.append({"sheet": sheet, "row": row, "column": column, "message": message,
                                "value": None if value is None else str(value)[:80]})

    def warn(self, sheet: str, row: int | None, column: str | None, message: str) -> None:
        if len(self.warnings) < MAX_ERRORS:
            self.warnings.append({"sheet": sheet, "row": row, "column": column, "message": message})

    def as_dict(self) -> dict:
        return {"ok": not self.errors, "format": self.format, "kind": self.kind, "files": self.files,
                "n_errors": len(self.errors), "n_warnings": len(self.warnings), "errors": self.errors,
                "warnings": self.warnings, "missing_values": self.missing, "counts": self.counts,
                "preview": self.preview, "derived_summary": self.derived,
                "truncated": len(self.errors) >= MAX_ERRORS}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _is_blank(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v)) or (isinstance(v, str) and v.strip() == "")


def _clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() if c is not None else "" for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]]
    mask = df.apply(lambda r: all(_is_blank(v) for v in r), axis=1) if len(df) else pd.Series(dtype=bool)
    df = df[~mask] if len(df) else df
    return df


def _read_xlsx(data: bytes) -> dict[str, pd.DataFrame]:
    if not data.startswith(b"PK\x03\x04"):
        raise ImportRejected("The file is not a valid .xlsx workbook.")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
            if any(n.lower().endswith("vbaproject.bin") for n in names):
                raise ImportRejected("Macro-enabled workbooks are not accepted.")
            if sum(i.file_size for i in z.infolist()) > 200 * 1024 * 1024:
                raise ImportRejected("Workbook expands to an unreasonably large size.")
    except zipfile.BadZipFile as exc:
        raise ImportRejected("The workbook is corrupted (not a valid zip container).") from exc
    import openpyxl  # defusedxml is installed, so openpyxl parses XML safely

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    # Second, formula-preserving read: formulas are NEVER evaluated; a formula in a data cell is
    # surfaced as text beginning with "=" so validation reports it explicitly.
    wbf = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=False)
    out = {}
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        frows = list(wbf[ws.title].iter_rows(values_only=True))
        for i, fr in enumerate(frows[1:len(rows)], start=1):
            for j, fv in enumerate(fr[: len(rows[i])]):
                if isinstance(fv, str) and fv.startswith("="):
                    rows[i][j] = fv
        if not rows:
            continue
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        body = rows[1:]
        df = pd.DataFrame(body, columns=header) if body else pd.DataFrame(columns=header)
        out[ws.title] = _clean_frame(df)
    wb.close()
    wbf.close()
    return out


def _read_csv(data: bytes, name: str) -> pd.DataFrame:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportRejected(f"{name}: CSV files must be UTF-8 encoded.") from exc
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        sep = dialect.delimiter
    except csv.Error:
        sep = ","
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)
    return _clean_frame(df.replace({"": None}))


def _classify_csv(df: pd.DataFrame) -> str | None:
    cols = set(df.columns)
    if {"trial_number", "original_pattern"} <= cols:
        return "Raw_Trials"
    if {"control_accuracy", "numerical_accuracy"} <= cols:
        return "Participant_Summary"
    if {"session_id", "condition_order"} <= cols:
        return "Sessions"
    if "email" in cols and "age" not in cols:
        return "Contacts"
    if {"participant_id", "age", "gender"} <= cols:
        return "Participants"
    return None


def parse_files(files: list[tuple[str, bytes]], report: Report) -> dict[str, pd.DataFrame]:
    s = get_settings()
    sheets: dict[str, pd.DataFrame] = {}
    exts = set()
    for name, data in files:
        report.files.append(name)
        if len(data) > s.max_upload_mb * 1024 * 1024:
            raise ImportRejected(f"{name} is larger than {s.max_upload_mb} MB.")
        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        exts.add(ext)
        if ext == "xlsx":
            for k, v in _read_xlsx(data).items():
                sheets[k] = v
        elif ext == "csv":
            df = _read_csv(data, name)
            kind = _classify_csv(df)
            if kind is None:
                raise ImportRejected(f"{name}: could not recognise this CSV (check the header row matches a template).")
            if kind in sheets:
                raise ImportRejected(f"Two uploaded CSV files both look like '{kind}'.")
            sheets[kind] = df
        elif ext == "json":
            try:
                payload = json.loads(data.decode("utf-8"))
            except Exception as exc:
                raise ImportRejected(f"{name}: invalid JSON.") from exc
            if not isinstance(payload, dict):
                raise ImportRejected(f"{name}: expected a JSON object with Participants/Sessions/Raw_Trials.")
            for k in ("Participants", "Contacts", "Sessions", "Raw_Trials", "Participant_Summary"):
                if k in payload and isinstance(payload[k], list):
                    sheets[k] = _clean_frame(pd.DataFrame(payload[k]))
        elif ext in ("xls", "xlsm", "xlsb"):
            raise ImportRejected(f"{name}: legacy or macro-enabled Excel files are not accepted; save as .xlsx.")
        else:
            raise ImportRejected(f"{name}: unsupported file type (use .xlsx, .csv or .json).")
    report.format = "+".join(sorted(exts))
    return sheets


# ---------------------------------------------------------------------------
# Value conversion
# ---------------------------------------------------------------------------

def _to_bool(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)) and v in (0, 1):
        return bool(v)
    s = str(v).strip().lower()
    if s in ("true", "yes", "1"):
        return True
    if s in ("false", "no", "0"):
        return False
    raise ValueError("expected TRUE or FALSE")


def _convert(var: Var, v):
    if _is_blank(v):
        return None
    if isinstance(v, str) and v.strip()[:1] == "=":
        raise ValueError("formulas are not accepted in data cells")
    t = var.type
    if t == "str":
        return str(v).strip()
    if t == "int":
        f = float(v)
        if not f.is_integer():
            raise ValueError("expected a whole number")
        x = int(f)
    elif t == "float":
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            raise ValueError("expected a number")
    elif t == "bool":
        return _to_bool(v)
    elif t == "enum":
        s = str(v).strip()
        allowed = {a.lower(): a for a in var.allowed}
        if s.lower() not in allowed:
            raise ValueError(f"must be one of: {', '.join(var.allowed)}")
        return allowed[s.lower()]
    elif t == "pattern":
        p = pattern_from_str(str(v))
        if not p or any(c < 0 or c > 63 for c in p) or len(set(p)) != len(p):
            raise ValueError("pattern must be distinct cell numbers separated by '-' (e.g. 0-2-5-7)")
        return pattern_to_str(p)
    elif t == "datetime":
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            return pd.Timestamp(str(v)).isoformat()
        except Exception as exc:
            raise ValueError("expected a date-time such as 2026-12-01T10:15:00") from exc
    else:
        return v
    if var.min is not None and x < var.min:
        raise ValueError(f"must be ≥ {var.min:g}")
    if var.max is not None and x > var.max:
        raise ValueError(f"must be ≤ {var.max:g}")
    return x


def _validate_sheet(name: str, df: pd.DataFrame, vars_: list[Var], report: Report, *,
                    required_override: set[str] | None = None) -> list[dict]:
    present = set(df.columns)
    known = {v.name for v in vars_}
    required = {v.name for v in vars_ if v.required} if required_override is None else required_override
    missing_cols = sorted(required - present)
    for c in missing_cols:
        report.err(name, None, c, f"Required column '{c}' is missing from sheet {name}.")
    extra = sorted(present - known)
    if extra:
        report.warn(name, None, None, f"Columns ignored (not in the template): {', '.join(extra[:10])}")
    if missing_cols:
        return []
    out = []
    miss = {v.name: 0 for v in vars_ if v.name in present}
    for i, (_, row) in enumerate(df.iterrows()):
        excel_row = i + 2
        rec = {}
        for v in vars_:
            if v.name not in present:
                rec[v.name] = None
                continue
            raw = row[v.name]
            try:
                val = _convert(v, raw)
            except (ValueError, TypeError) as exc:
                report.err(name, excel_row, v.name, str(exc), raw)
                val = None
            if val is None:
                miss[v.name] += 1
                if v.name in required and _is_blank(raw):
                    report.err(name, excel_row, v.name, "Required value is missing.")
            rec[v.name] = val
        rec["_row"] = excel_row
        out.append(rec)
    report.missing[name] = {k: n for k, n in miss.items() if n}
    return out


# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def _expected_from_versions(db: Session, versions: set[str]) -> dict[str, ExperimentConfig]:
    out = {}
    for v in versions:
        row = db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.experiment_version == v))
        if row:
            out[v] = ExperimentConfig.model_validate(row.config_json)
    return out


def _check_synthetic(ids: list[str], sheets: dict, report: Report) -> None:
    flagged = any(str(i).upper().startswith("SYN") for i in ids) or any(k.upper().startswith("SYNTHETIC") for k in sheets)
    if flagged and not get_settings().allow_synthetic_imports:
        report.err("file", None, None, "This file is marked as SYNTHETIC test data (IDs starting with 'SYN' or a "
                   "SYNTHETIC sheet). Synthetic data must never enter the research database.")


def validate(db: Session, files: list[tuple[str, bytes]]) -> tuple[Report, dict | None]:
    report = Report()
    try:
        sheets = parse_files(files, report)
    except ImportRejected as exc:
        report.err("file", None, None, str(exc))
        return report, None

    if "Raw_Trials" in sheets and len(sheets["Raw_Trials"]):
        report.kind = "full"
        return _validate_full(db, sheets, report)
    summary_sheet = next((k for k in ("Participant_Summary", "Summary") if k in sheets and len(sheets[k])), None)
    if summary_sheet:
        report.kind = "summary"
        return _validate_summary(db, sheets[summary_sheet], sheets, report)
    if "Raw_Trials" in sheets:
        report.err("Raw_Trials", None, None, "The Raw_Trials sheet contains no data rows.")
    else:
        report.err("file", None, None, "No Raw_Trials or Participant_Summary data found. Use the SMIT templates.")
    return report, None


def _existing_ids(db: Session, ids: list[str]) -> set[str]:
    if not ids:
        return set()
    return set(db.scalars(select(Participant.participant_id).where(Participant.participant_id.in_(ids))).all())


def _validate_participants(db: Session, sheets: dict, report: Report) -> list[dict]:
    if "Participants" not in sheets:
        report.err("Participants", None, None, "Sheet/file 'Participants' is required for a full import.")
        return []
    parts = _validate_sheet("Participants", sheets["Participants"], PARTICIPANT_VARS, report)
    seen = set()
    for p in parts:
        pid = p["participant_id"]
        if pid is None:
            continue
        if not ID_RE.match(pid):
            report.err("Participants", p["_row"], "participant_id", "IDs may contain only letters, digits, '-' and '_'.", pid)
        if pid in seen:
            report.err("Participants", p["_row"], "participant_id", "Duplicate participant_id in file.", pid)
        seen.add(pid)
        if p.get("consent_status") is False:
            report.err("Participants", p["_row"], "consent_status", "Consent is FALSE: data from this person cannot be imported.")
        course = p.get("academic_course")
        if course and re.match(r"^[=+\-@]", course):
            report.err("Participants", p["_row"], "academic_course", "Text starting with = + - @ is not allowed.", course)
    existing = _existing_ids(db, list(seen))
    for p in parts:
        if p["participant_id"] in existing:
            report.err("Participants", p["_row"], "participant_id",
                       "This participant already exists in the database (existing data are never overwritten).",
                       p["participant_id"])
    return parts


def _validate_full(db: Session, sheets: dict, report: Report) -> tuple[Report, dict | None]:
    parts = _validate_participants(db, sheets, report)
    pids = {p["participant_id"] for p in parts if p["participant_id"]}

    contacts = []
    if "Contacts" in sheets and len(sheets["Contacts"]):
        contacts = _validate_sheet("Contacts", sheets["Contacts"], CONTACT_VARS, report,
                                   required_override={"participant_id"})
        cseen = set()
        for c in contacts:
            if c["participant_id"] not in pids:
                report.err("Contacts", c["_row"], "participant_id", "Contact refers to an unknown participant.", c["participant_id"])
            if c["participant_id"] in cseen:
                report.err("Contacts", c["_row"], "participant_id", "Duplicate contact row.")
            cseen.add(c["participant_id"])
            if c.get("email") and not EMAIL_RE.match(c["email"]):
                report.err("Contacts", c["_row"], "email", "Invalid email address format.")
        hashes = [email_hash(c["email"]) for c in contacts if c.get("email")]
        if len(hashes) != len(set(hashes)):
            report.err("Contacts", None, "email", "The same email address appears for more than one participant.")
        if hashes:
            dup = db.scalars(select(ParticipantContact.participant_id).where(ParticipantContact.email_hash.in_(hashes))).all()
            for d in dup:
                report.err("Contacts", None, "email", f"An email in this file is already registered (participant {d}).")

    if "Sessions" not in sheets:
        report.err("Sessions", None, None, "Sheet/file 'Sessions' is required for a full import.")
        sessions = []
    else:
        sessions = _validate_sheet("Sessions", sheets["Sessions"], SESSION_VARS, report)
    sids = {}
    for s in sessions:
        sid = s["session_id"]
        if sid is None:
            continue
        if not ID_RE.match(sid):
            report.err("Sessions", s["_row"], "session_id", "IDs may contain only letters, digits, '-' and '_'.", sid)
        if sid in sids:
            report.err("Sessions", s["_row"], "session_id", "Duplicate session_id in file.", sid)
        sids[sid] = s
        if s["participant_id"] not in pids:
            report.err("Sessions", s["_row"], "participant_id", "Session refers to a participant not in the Participants sheet.", s["participant_id"])
    if sids and db.scalars(select(ExperimentSession.session_id).where(ExperimentSession.session_id.in_(list(sids)))).first():
        report.err("Sessions", None, "session_id", "One or more session_id values already exist in the database.")
    versions = {s["experiment_version"] for s in sessions if s["experiment_version"] and s["session_type"] == "main"}
    if len(versions) > 1:
        report.warn("Sessions", None, "experiment_version",
                    f"Inconsistent experiment versions in main-study sessions: {', '.join(sorted(versions))}. "
                    "Results will be reported by version; check that this is intended.")
    known_cfgs = _expected_from_versions(db, versions)
    for v in versions - set(known_cfgs):
        report.warn("Sessions", None, "experiment_version",
                    f"Version '{v}' is not a configuration in this database; trial-count checks use the default 20 per condition.")
    sess_participant = {sid: s["participant_id"] for sid, s in sids.items()}
    for p in parts:
        if p["participant_id"] and p["participant_id"] not in sess_participant.values():
            report.warn("Participants", p["_row"], "participant_id", "Participant has no session in the Sessions sheet.")

    trials = _validate_sheet("Raw_Trials", sheets["Raw_Trials"], TRIAL_VARS, report)
    keys = set()
    acfg_default = AnalysisConfig()
    for t in trials:
        r = t["_row"]
        sid = t["session_id"]
        if sid not in sids:
            report.err("Raw_Trials", r, "session_id", "Trial refers to a session not in the Sessions sheet.", sid)
        elif t["participant_id"] != sess_participant[sid]:
            report.err("Raw_Trials", r, "participant_id",
                       f"participant_id does not match the session's participant ({sess_participant[sid]}).", t["participant_id"])
        key = (sid, t["practice_trial"], t["trial_number"])
        if key in keys:
            report.err("Raw_Trials", r, "trial_number", "Duplicate trial (same session, practice flag and trial_number).")
        keys.add(key)
        # pattern logic
        op, rp = t["original_pattern"], t["recognition_pattern"]
        if op and rp:
            a, b = set(pattern_from_str(op)), set(pattern_from_str(rp))
            if len(a) != len(b):
                report.err("Raw_Trials", r, "recognition_pattern", "Recognition pattern must have the same number of filled cells as the original.")
            else:
                n_diff = len(a - b)
                derived_answer = "same" if n_diff == 0 else ("different" if n_diff == 1 else None)
                if derived_answer is None:
                    report.err("Raw_Trials", r, "recognition_pattern", "Patterns differ by more than one moved cell.")
                elif t["correct_answer"] and t["correct_answer"] != derived_answer:
                    report.err("Raw_Trials", r, "correct_answer",
                               f"correct_answer '{t['correct_answer']}' conflicts with the patterns (they are {derived_answer}).")
        # responses and RT
        resp, rt = t["participant_response"], t["reaction_time_ms"]
        derived_timeout = resp is None
        if t["response_timeout"] is not None and t["response_timeout"] != derived_timeout:
            report.err("Raw_Trials", r, "response_timeout", "response_timeout conflicts with participant_response.")
        if resp is None and rt is not None:
            report.err("Raw_Trials", r, "reaction_time_ms", "A reaction time is given but there is no response.")
        if resp is not None and rt is None:
            report.warn("Raw_Trials", r, "reaction_time_ms", "Response without reaction time; excluded from RT analyses.")
        if rt is not None and rt < acfg_default.min_valid_rt_ms:
            report.warn("Raw_Trials", r, "reaction_time_ms", f"RT {rt:.0f} ms < {acfg_default.min_valid_rt_ms:.0f} ms (anticipatory; excluded from RT analyses).")
        if resp is not None and t["correct_answer"]:
            derived_correct = resp == t["correct_answer"]
            if t["is_correct"] is not None and t["is_correct"] != derived_correct:
                report.err("Raw_Trials", r, "is_correct", f"is_correct={t['is_correct']} conflicts with response/correct_answer (should be {derived_correct}).")
        # secondary task
        cond = t["condition"]
        if cond == "A" and (t["interference_response"] or t["interference_correct_answer"]):
            report.err("Raw_Trials", r, "interference_response", "Condition A (control) has no secondary task.")
        if cond in ("B", "C") and not t["practice_trial"] and t["interference_correct_answer"] is None:
            report.err("Raw_Trials", r, "interference_correct_answer", "Interference conditions need interference_correct_answer.")
        if t["interference_accuracy"] is not None and t["interference_correct_answer"]:
            derived_sec = t["interference_response"] == t["interference_correct_answer"]
            if t["interference_accuracy"] != derived_sec:
                report.err("Raw_Trials", r, "interference_accuracy", "interference_accuracy conflicts with the secondary response.")
        if t["exclusion_status"] == "excluded" and not t["exclusion_reason"]:
            report.err("Raw_Trials", r, "exclusion_reason", "An exclusion reason is required for excluded trials.")
        if t["block_number"] is not None and t["practice_trial"] is not None:
            if t["practice_trial"] and t["block_number"] != 0:
                report.warn("Raw_Trials", r, "block_number", "Practice trials normally have block_number 0.")
            if not t["practice_trial"] and t["block_number"] == 0:
                report.err("Raw_Trials", r, "block_number", "Experimental trials must have block_number 1–3.")

    # trial counts and same/different balance per session
    df = pd.DataFrame([t for t in trials if t["session_id"] in sids])
    if not df.empty:
        main = df[df["practice_trial"] == False]  # noqa: E712
        for sid, s in sids.items():
            cfg = known_cfgs.get(s["experiment_version"]) or ExperimentConfig()
            per = cfg.trials.trials_per_condition
            n_same_exp = round(per * cfg.trials.same_proportion)
            g = main[main["session_id"] == sid]
            if s["completion_status"] == "completed" and len(g) != 3 * per:
                report.err("Sessions", s["_row"], "completion_status",
                           f"Session {sid} is marked completed but has {len(g)} experimental trials (expected {3 * per}).")
            for cond in ("A", "B", "C"):
                gc = g[g["condition"] == cond]
                if len(gc) and len(gc) > per:
                    report.err("Raw_Trials", None, "condition", f"Session {sid}: {len(gc)} trials in condition {cond} (max {per}).")
                if len(gc) == per:
                    ns = int((gc["correct_answer"] == "same").sum())
                    if ns != n_same_exp:
                        report.warn("Raw_Trials", None, "correct_answer",
                                    f"Session {sid}, condition {cond}: {ns} same / {per - ns} different trials (expected {n_same_exp}/{per - n_same_exp}).")
            blocks = g.groupby("block_number")["condition"].agg(lambda x: set(x))
            order = s["condition_order"]
            for bn, conds in blocks.items():
                if len(conds) > 1:
                    report.err("Raw_Trials", None, "condition", f"Session {sid}: block {bn} mixes conditions {sorted(conds)}.")
                elif order and 1 <= int(bn) <= 3 and order[int(bn) - 1] not in conds:
                    report.err("Raw_Trials", None, "block_number",
                               f"Session {sid}: block {bn} contains condition {next(iter(conds))} but condition_order is {order}.")

    _check_synthetic([p["participant_id"] for p in parts if p["participant_id"]], sheets, report)
    report.counts = {"participants": len(parts), "contacts": len(contacts), "sessions": len(sessions),
                     "trials": len(trials), "experimental_trials": int(sum(1 for t in trials if t["practice_trial"] is False)),
                     "practice_trials": int(sum(1 for t in trials if t["practice_trial"] is True))}
    report.preview = {
        "Participants": [{k: v for k, v in p.items() if k != "_row"} for p in parts[:10]],
        "Sessions": [{k: v for k, v in s.items() if k != "_row"} for s in sessions[:10]],
        "Raw_Trials": [{k: v for k, v in t.items() if k != "_row"} for t in trials[:10]],
    }
    if not report.errors and not df.empty:
        from ..analysis.metrics import classify_trials, participant_condition_metrics

        tmp = df.copy()
        tmp["timing_quality_flag"] = "ok"
        ct = classify_trials(tmp, AnalysisConfig())
        pcm = participant_condition_metrics(ct)
        if not pcm.empty:
            pv = pcm.pivot(index="participant_id", columns="condition", values="accuracy").round(3)
            report.derived = [{"participant_id": pid, **{f"accuracy_{c}": (None if pd.isna(v) else float(v))
                                                         for c, v in row.items()}} for pid, row in pv.iterrows()]
    if report.errors:
        return report, None
    payload = {"kind": "full", "participants": _strip(parts), "contacts": _strip(contacts),
               "sessions": _strip(sessions), "trials": _strip(trials)}
    return report, payload


def _strip(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if k != "_row"} for r in rows]


def _validate_summary(db: Session, df: pd.DataFrame, sheets: dict, report: Report) -> tuple[Report, dict | None]:
    rows = _validate_sheet("Participant_Summary", df, SUMMARY_VARS, report)
    seen = set()
    for r in rows:
        pid = r["participant_id"]
        if pid and not ID_RE.match(pid):
            report.err("Participant_Summary", r["_row"], "participant_id", "IDs may contain only letters, digits, '-' and '_'.")
        if pid in seen:
            report.err("Participant_Summary", r["_row"], "participant_id", "Duplicate participant_id.")
        seen.add(pid)
        if r.get("consent_status") is False:
            report.err("Participant_Summary", r["_row"], "consent_status", "Consent is FALSE: cannot import.")
    for pid in _existing_ids(db, [p for p in seen if p]):
        report.err("Participant_Summary", None, "participant_id", f"Participant {pid} already exists (no overwrite).")
    versions = {r["experiment_version"] for r in rows if r.get("experiment_version")}
    if len(versions) > 1:
        report.warn("Participant_Summary", None, "experiment_version", f"Inconsistent experiment versions: {sorted(versions)}")
    report.warn("Participant_Summary", None, None,
                "Summary-only data: trial-level quality checks, timing checks, exclusion rules 2–5, RT distributions, "
                "signal-detection measures, block-order/fatigue analyses and secondary-task RT are unavailable for these participants.")
    _check_synthetic([r["participant_id"] for r in rows if r["participant_id"]], sheets, report)
    report.counts = {"participants": len(rows)}
    report.preview = {"Participant_Summary": _strip(rows[:10])}
    if report.errors:
        return report, None
    return report, {"kind": "summary", "rows": _strip(rows)}


# ---------------------------------------------------------------------------
# Batch lifecycle
# ---------------------------------------------------------------------------

def create_batch(db: Session, files: list[tuple[str, bytes]]) -> ImportBatch:
    sha = hashlib.sha256()
    for name, data in sorted(files, key=lambda x: x[0]):
        sha.update(hashlib.sha256(data).digest())
    digest = sha.hexdigest()
    report, payload = validate(db, files)
    dup = db.scalar(select(ImportBatch).where(ImportBatch.file_sha256 == digest, ImportBatch.status == "committed"))
    if dup:
        report.err("file", None, None, f"This exact file was already imported on {dup.committed_at:%Y-%m-%d %H:%M} (import #{dup.id}).")
        payload = None
    batch = ImportBatch(file_names=", ".join(n for n, _ in files)[:2000], file_sha256=digest, file_format=report.format or "?",
                        import_kind=report.kind or "unknown", status="validated" if payload else "invalid",
                        validation_report=json.loads(json.dumps(report.as_dict(), default=str)),
                        staged_payload=json.loads(json.dumps(payload, default=str)) if payload else None,
                        n_participants=report.counts.get("participants", 0), n_sessions=report.counts.get("sessions", 0),
                        n_trials=report.counts.get("trials", 0))
    db.add(batch)
    db.flush()
    audit(db, "import_validated", entity_type="import", entity_id=str(batch.id),
          details={"files": batch.file_names, "status": batch.status, "errors": len(report.errors),
                   "warnings": len(report.warnings), "kind": report.kind})
    db.commit()
    return batch


def commit_batch(db: Session, batch: ImportBatch) -> dict:
    if batch.status != "validated" or not batch.staged_payload:
        raise ImportRejected("Only a successfully validated import that has not been committed or cancelled can be committed.")
    if db.scalar(select(ImportBatch).where(ImportBatch.file_sha256 == batch.file_sha256, ImportBatch.status == "committed")):
        raise ImportRejected("This file has already been imported.")
    p = batch.staged_payload
    try:
        if p["kind"] == "full":
            n = _commit_full(db, batch, p)
        else:
            n = _commit_summary(db, batch, p)
        batch.status = "committed"
        batch.committed_at = utcnow()
        batch.staged_payload = None  # do not keep a second copy of the data
        audit(db, "import_committed", entity_type="import", entity_id=str(batch.id), details=n)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return n


def _dt(v):
    return pd.Timestamp(v).to_pydatetime() if v else None


def _commit_full(db: Session, batch: ImportBatch, p: dict) -> dict:
    existing = _existing_ids(db, [x["participant_id"] for x in p["participants"]])
    if existing:
        raise ImportRejected(f"Participants already exist: {sorted(existing)[:5]} — re-validate the file.")
    session_type = {s["participant_id"]: s["session_type"] for s in p["sessions"]}
    for x in p["participants"]:
        db.add(Participant(participant_id=x["participant_id"], age=x["age"], gender=x["gender"],
                           academic_course=x["academic_course"], consent_status=bool(x["consent_status"]),
                           participant_type=session_type.get(x["participant_id"], "main"), data_source="import",
                           import_batch_id=batch.id))
    db.flush()
    for c in p["contacts"]:
        if c.get("email"):
            db.add(ParticipantContact(participant_id=c["participant_id"], email=c["email"], email_hash=email_hash(c["email"])))
    cfg_ids = {}
    for s in p["sessions"]:
        v = s["experiment_version"]
        if v not in cfg_ids:
            row = db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.experiment_version == v))
            cfg_ids[v] = (row.id, ExperimentConfig.model_validate(row.config_json)) if row else (None, ExperimentConfig())
        db.add(ExperimentSession(
            session_id=s["session_id"], participant_id=s["participant_id"], config_id=cfg_ids[v][0],
            experiment_version=v, session_type=s["session_type"], condition_order=s["condition_order"],
            random_seed=s["random_seed"], estimated_refresh_rate=s["estimated_refresh_rate"],
            start_time=_dt(s["start_time"]), completion_time=_dt(s["completion_time"]),
            completion_status=s["completion_status"], device_information=s["device_information"],
            browser_information=s["browser_information"], data_source="import", import_batch_id=batch.id))
    db.flush()
    sess_cfg = {s["session_id"]: (cfg_ids[s["experiment_version"]][1], s["estimated_refresh_rate"]) for s in p["sessions"]}
    for t in p["trials"]:
        cfg, hz = sess_cfg[t["session_id"]]
        resp = t["participant_response"]
        sec_resp = t["interference_response"]
        row = {k: t.get(k) for k in (
            "session_id", "participant_id", "trial_number", "block_number", "condition", "practice_trial",
            "original_pattern", "recognition_pattern", "reaction_time_ms", "interference_stimulus",
            "interference_correct_answer", "interference_reaction_time_ms", "planned_fixation_duration_ms",
            "actual_fixation_duration_ms", "planned_stimulus_duration_ms", "measured_stimulus_duration_ms",
            "planned_interference_duration_ms", "measured_interference_duration_ms", "planned_retention_duration_ms",
            "measured_retention_duration_ms", "inter_trial_interval_ms", "exclusion_reason")}
        op, rp = set(pattern_from_str(t["original_pattern"])), set(pattern_from_str(t["recognition_pattern"]))
        correct_answer = "same" if op == rp else "different"
        row.update(
            correct_answer=correct_answer, participant_response=resp,
            is_correct=None if resp is None else resp == correct_answer,
            response_timeout=resp is None, interference_response=sec_resp,
            interference_type={"A": "none", "B": "numerical", "C": "visual"}[t["condition"]],
            interference_accuracy=(None if not t["interference_correct_answer"] else sec_resp == t["interference_correct_answer"]),
            focus_loss=bool(t.get("focus_loss") or False),
            exclusion_status=t.get("exclusion_status") or "included", practice_attempt=1 if t["practice_trial"] else 0,
            refresh_rate_hz=hz,
        )
        flag, notes = assess_timing(row, hz, cfg.analysis)
        row["timing_quality_flag"] = flag
        row["timing_notes"] = notes
        if t.get("timestamp"):
            row["timestamp"] = _dt(t["timestamp"])
        db.add(Trial(**row))
    db.flush()
    return {"participants": len(p["participants"]), "sessions": len(p["sessions"]), "trials": len(p["trials"])}


def _commit_summary(db: Session, batch: ImportBatch, p: dict) -> dict:
    for r in p["rows"]:
        part = Participant(participant_id=r["participant_id"], age=r["age"], gender=r["gender"],
                           academic_course=r["academic_course"], consent_status=bool(r["consent_status"]),
                           participant_type="main", data_source="import", import_batch_id=batch.id)
        part.imported_summary = ImportedParticipantSummary(
            experiment_version=r.get("experiment_version"), condition_order=r.get("condition_order"),
            accuracy_a=r["control_accuracy"], accuracy_b=r["numerical_accuracy"], accuracy_c=r["visual_accuracy"],
            rt_a=r.get("control_mean_correct_rt_ms"), rt_b=r.get("numerical_mean_correct_rt_ms"),
            rt_c=r.get("visual_mean_correct_rt_ms"), timeout_rate=r.get("timeout_rate"),
            secondary_accuracy_b=r.get("numerical_secondary_accuracy"),
            secondary_accuracy_c=r.get("visual_secondary_accuracy"), import_batch_id=batch.id)
        db.add(part)
    db.flush()
    return {"participants": len(p["rows"]), "sessions": 0, "trials": 0}
