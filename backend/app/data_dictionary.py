"""Single source of truth for every exported/imported variable.

Used by: Excel/CSV templates, the import validator, data exports and the
Data Dictionary appendix of the report.

Types: str, int, float, bool, datetime, pattern, enum
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Var:
    name: str
    type: str
    required: bool
    description: str
    unit: str = ""
    allowed: tuple = ()
    missing: str = "leave blank"
    interpretation: str = ""
    min: float | None = None
    max: float | None = None
    derived: bool = False  # recalculated by the application; may be left blank on import


GENDERS = ("Female", "Male", "Non-binary", "Other", "Prefer not to answer")
BOOL = ("TRUE", "FALSE")

PARTICIPANT_VARS: list[Var] = [
    Var("participant_id", "str", True, "Pseudonymous participant identifier (e.g. P001). Must be unique.",
        allowed=("letters, digits, '-' and '_' only; max 40 characters",), missing="not allowed",
        interpretation="Links participants, sessions and trials. Never use names or emails."),
    Var("age", "int", True, "Age in whole years at the time of testing.", unit="years", min=18, max=120,
        missing="not allowed for main-study participants",
        interpretation="Exploratory predictor; adults only (≥ 18)."),
    Var("gender", "enum", True, "Self-described gender.", allowed=GENDERS, missing="use 'Prefer not to answer'",
        interpretation="Nominal category; never numerically coded."),
    Var("academic_course", "str", True, "Academic course / programme of study (free text, e.g. 'BSc Psychology').",
        missing="not allowed", interpretation="Nominal category used in exploratory group comparisons."),
    Var("consent_status", "bool", True, "TRUE if informed consent was obtained before testing.", allowed=BOOL,
        missing="not allowed", interpretation="Rows with FALSE are rejected on import."),
]

CONTACT_VARS: list[Var] = [
    Var("participant_id", "str", True, "Participant identifier (must exist in Participants).", missing="not allowed"),
    Var("email", "str", True, "CONFIDENTIAL. Participant email address.", missing="leave blank if not collected",
        interpretation="Stored separately; never exported with research data or shown in reports."),
]

SESSION_VARS: list[Var] = [
    Var("session_id", "str", True, "Unique session identifier (e.g. S-P001-1).", missing="not allowed"),
    Var("participant_id", "str", True, "Participant identifier (must exist in Participants).", missing="not allowed"),
    Var("experiment_version", "str", True, "Locked experiment configuration version (e.g. SMIT-v3-1a2b3c4d).",
        missing="not allowed", interpretation="All main-study sessions should share one version."),
    Var("session_type", "enum", True, "main or pilot. Pilot sessions are excluded from analysis.", allowed=("main", "pilot")),
    Var("condition_order", "enum", True, "Block order of conditions.", allowed=("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")),
    Var("random_seed", "int", False, "Seed used to generate the trial plan.", missing="leave blank if unknown"),
    Var("estimated_refresh_rate", "float", False, "Estimated monitor refresh rate.", unit="Hz", min=20, max=500),
    Var("start_time", "datetime", False, "Session start (ISO 8601, e.g. 2026-12-01T10:15:00).", unit="date-time"),
    Var("completion_time", "datetime", False, "Session end (ISO 8601).", unit="date-time"),
    Var("completion_status", "enum", True, "Session outcome.",
        allowed=("completed", "incomplete", "withdrawn", "abandoned")),
    Var("device_information", "str", False, "Computer / OS description.", missing="leave blank"),
    Var("browser_information", "str", False, "Browser name and version.", missing="leave blank"),
]

TRIAL_VARS: list[Var] = [
    Var("session_id", "str", True, "Session identifier (must exist in Sessions)."),
    Var("participant_id", "str", True, "Participant identifier (must match the session's participant)."),
    Var("trial_number", "int", True, "Trial number within the experimental part (1–60) or within practice (1–6).", min=1),
    Var("block_number", "int", True, "Block position: 0 = practice, 1–3 = experimental blocks.", min=0, max=3),
    Var("condition", "enum", True, "A = Control, B = Numerical interference, C = Visual interference.", allowed=("A", "B", "C")),
    Var("practice_trial", "bool", True, "TRUE for practice trials (excluded from analysis).", allowed=BOOL),
    Var("original_pattern", "pattern", True,
        "Cells highlighted in the memory grid, cell indices 0–8 (row-major, top-left = 0) separated by '-', e.g. 0-2-5-7."),
    Var("recognition_pattern", "pattern", True, "Cells highlighted in the recognition grid (same format)."),
    Var("correct_answer", "enum", True, "'same' if the patterns are identical, else 'different'.",
        allowed=("same", "different"), interpretation="Recalculated from the patterns; mismatches are reported as errors."),
    Var("participant_response", "enum", False, "Participant's recognition response.", allowed=("same", "different"),
        missing="leave blank for no response (timeout)"),
    Var("is_correct", "bool", False, "TRUE if the response matches the correct answer.", allowed=BOOL, derived=True,
        missing="leave blank (recalculated)", interpretation="Recalculated; conflicting values are reported as errors."),
    Var("reaction_time_ms", "float", False, "Recognition RT from probe onset to key press.", unit="ms", min=0, max=10000,
        missing="leave blank for timeouts"),
    Var("response_timeout", "bool", False, "TRUE if no response was made before the deadline.", allowed=BOOL, derived=True,
        missing="leave blank (derived from participant_response)"),
    Var("interference_stimulus", "str", False, "Equation text (B) or distractor pattern (C).", missing="blank for condition A"),
    Var("interference_correct_answer", "enum", False, "Correct secondary answer.", allowed=("true", "false"),
        missing="blank for condition A"),
    Var("interference_response", "enum", False, "Participant's secondary response.", allowed=("true", "false"),
        missing="blank for no response or condition A"),
    Var("interference_accuracy", "bool", False, "TRUE if the secondary response was correct.", allowed=BOOL, derived=True,
        missing="leave blank (recalculated)"),
    Var("interference_reaction_time_ms", "float", False, "Secondary-task RT from secondary stimulus onset.", unit="ms",
        min=0, max=20000),
    Var("planned_fixation_duration_ms", "float", False, "Planned fixation duration.", unit="ms"),
    Var("actual_fixation_duration_ms", "float", False, "Measured fixation duration.", unit="ms"),
    Var("planned_stimulus_duration_ms", "float", False, "Planned memory-stimulus duration.", unit="ms"),
    Var("measured_stimulus_duration_ms", "float", False, "Measured memory-stimulus duration.", unit="ms"),
    Var("planned_interference_duration_ms", "float", False, "Planned interference-phase duration.", unit="ms"),
    Var("measured_interference_duration_ms", "float", False, "Measured interference-phase duration.", unit="ms"),
    Var("planned_retention_duration_ms", "float", False, "Planned retention-interval duration.", unit="ms"),
    Var("measured_retention_duration_ms", "float", False, "Measured retention-interval duration.", unit="ms"),
    Var("inter_trial_interval_ms", "float", False, "Measured inter-trial interval.", unit="ms"),
    Var("focus_loss", "bool", False, "TRUE if the window lost focus during the trial.", allowed=BOOL, missing="FALSE"),
    Var("timing_quality_flag", "enum", False, "ok / warning / invalid (recalculated from timing columns).",
        allowed=("ok", "warning", "invalid"), derived=True, missing="leave blank (recalculated)"),
    Var("exclusion_status", "enum", False, "Researcher trial exclusion.", allowed=("included", "excluded"),
        missing="'included'"),
    Var("exclusion_reason", "str", False, "Required when exclusion_status = excluded."),
    Var("timestamp", "datetime", False, "Time the trial was recorded (ISO 8601).", unit="date-time"),
]

SUMMARY_VARS: list[Var] = [
    Var("participant_id", "str", True, "Pseudonymous participant identifier."),
    Var("age", "int", True, "Age in years.", unit="years", min=18, max=120),
    Var("gender", "enum", True, "Gender.", allowed=GENDERS),
    Var("academic_course", "str", True, "Academic course."),
    Var("consent_status", "bool", True, "Consent obtained.", allowed=BOOL),
    Var("experiment_version", "str", False, "Experiment configuration version."),
    Var("condition_order", "enum", False, "Block order.", allowed=("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")),
    Var("control_accuracy", "float", True, "Proportion correct in condition A (timeouts = incorrect).", unit="proportion 0–1", min=0, max=1),
    Var("numerical_accuracy", "float", True, "Proportion correct in condition B.", unit="proportion 0–1", min=0, max=1),
    Var("visual_accuracy", "float", True, "Proportion correct in condition C.", unit="proportion 0–1", min=0, max=1),
    Var("control_mean_correct_rt_ms", "float", False, "Mean correct RT in condition A.", unit="ms", min=0, max=10000),
    Var("numerical_mean_correct_rt_ms", "float", False, "Mean correct RT in condition B.", unit="ms", min=0, max=10000),
    Var("visual_mean_correct_rt_ms", "float", False, "Mean correct RT in condition C.", unit="ms", min=0, max=10000),
    Var("timeout_rate", "float", False, "Proportion of experimental trials without a response.", unit="proportion 0–1", min=0, max=1),
    Var("numerical_secondary_accuracy", "float", False, "Arithmetic-task accuracy.", unit="proportion 0–1", min=0, max=1),
    Var("visual_secondary_accuracy", "float", False, "Symmetry-task accuracy.", unit="proportion 0–1", min=0, max=1),
]

# Calculated columns of the Participant_Summary sheet (computed by the application / workbook formulas)
SUMMARY_CALCULATED: list[Var] = [
    Var("control_accuracy", "float", False, "Proportion correct, condition A.", unit="proportion", derived=True),
    Var("numerical_accuracy", "float", False, "Proportion correct, condition B.", unit="proportion", derived=True),
    Var("visual_accuracy", "float", False, "Proportion correct, condition C.", unit="proportion", derived=True),
    Var("control_mean_correct_rt_ms", "float", False, "Mean correct RT, A.", unit="ms", derived=True),
    Var("numerical_mean_correct_rt_ms", "float", False, "Mean correct RT, B.", unit="ms", derived=True),
    Var("visual_mean_correct_rt_ms", "float", False, "Mean correct RT, C.", unit="ms", derived=True),
    Var("numerical_accuracy_cost", "float", False, "Accuracy A − Accuracy B (positive = worse under interference).", derived=True),
    Var("visual_accuracy_cost", "float", False, "Accuracy A − Accuracy C.", derived=True),
    Var("numerical_rt_cost_ms", "float", False, "RT B − RT A (positive = slower under interference).", unit="ms", derived=True),
    Var("visual_rt_cost_ms", "float", False, "RT C − RT A.", unit="ms", derived=True),
    Var("timeout_rate", "float", False, "Proportion of experimental trials without response.", derived=True),
    Var("overall_accuracy", "float", False, "Proportion correct across all experimental trials.", derived=True),
    Var("overall_mean_correct_rt_ms", "float", False, "Mean correct RT across all experimental trials.", unit="ms", derived=True),
]

SHEETS = {
    "Participants": PARTICIPANT_VARS,
    "Contacts": CONTACT_VARS,
    "Sessions": SESSION_VARS,
    "Raw_Trials": TRIAL_VARS,
}


def names(vars_: list[Var]) -> list[str]:
    return [v.name for v in vars_]
