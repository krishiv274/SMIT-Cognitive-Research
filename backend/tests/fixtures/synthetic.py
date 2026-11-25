"""SYNTHETIC test fixtures — FOR SOFTWARE VERIFICATION ONLY.

Every participant ID starts with "SYN-" and every file is labelled SYNTHETIC.
These data are simulated by a simple random model; they are NOT observations of
real people, are never written to the research database (tests use temporary
databases) and must never be presented as research findings.
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from app.experiment.config import ExperimentConfig
from app.experiment.plan import ORDERS, generate_plan, pattern_to_str

SYN_PREFIX = "SYN-"
COURSES = ["SYNTHETIC Course Alpha", "SYNTHETIC Course Beta", "SYNTHETIC Course Gamma"]
GENDERS = ["Female", "Male", "Non-binary", "Prefer not to answer"]


def simulate(n: int = 24, seed: int = 2026, config: ExperimentConfig | None = None,
             effect: dict[str, float] | None = None, version: str = "SMIT-SYNTHETIC-TEST") -> dict[str, pd.DataFrame]:
    """Simulate trial-level data for `n` synthetic participants.

    `effect` gives the probability of a correct response per condition (default: no built-in
    hypothesis; all conditions equal unless a test asks otherwise).
    """
    cfg = config or ExperimentConfig()
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    effect = effect or {"A": 0.8, "B": 0.8, "C": 0.8}
    parts, contacts, sessions, trials = [], [], [], []
    for i in range(n):
        pid = f"{SYN_PREFIX}{i + 1:03d}"
        sid = f"S-{pid}"
        order = ORDERS[i % 6]
        ability = nrng.normal(0, 0.06)
        speed = nrng.normal(0, 80)
        parts.append({"participant_id": pid, "age": int(18 + nrng.integers(0, 12)), "gender": GENDERS[i % 4],
                      "academic_course": COURSES[i % 3], "consent_status": True})
        contacts.append({"participant_id": pid, "email": f"synthetic{i + 1}@example.invalid"})
        sessions.append({"session_id": sid, "participant_id": pid, "experiment_version": version, "session_type": "main",
                         "condition_order": order, "random_seed": 1000 + i, "estimated_refresh_rate": 60.0,
                         "start_time": "2026-12-01T10:00:00", "completion_time": "2026-12-01T10:20:00",
                         "completion_status": "completed", "device_information": "SYNTHETIC", "browser_information": "SYNTHETIC"})
        plan = generate_plan(cfg, 1000 + i, order)
        all_trials = [(t, True) for t in plan["practice"]] + [(t, False) for b in plan["blocks"] for t in b["trials"]]
        for t, practice in all_trials:
            p = float(np.clip(effect[t["condition"]] + ability, 0.05, 0.99))
            timeout = rng.random() < 0.03
            if timeout:
                resp, rt = None, None
            else:
                ok = rng.random() < p
                resp = t["correct_answer"] if ok else ("different" if t["correct_answer"] == "same" else "same")
                rt = float(np.clip(nrng.normal(800 + speed + (60 if t["condition"] != "A" else 0), 180), 150, 1990))
            sec = t["interference"]
            sec_resp = sec_rt = None
            if sec:
                sec_resp = sec["correct"] if rng.random() < 0.9 else ("false" if sec["correct"] == "true" else "true")
                sec_rt = float(np.clip(nrng.normal(1300, 250), 300, 2900))
            trials.append({
                "session_id": sid, "participant_id": pid, "trial_number": t["trial_number"],
                "block_number": t["block_number"], "condition": t["condition"], "practice_trial": practice,
                "original_pattern": pattern_to_str(t["original_pattern"]),
                "recognition_pattern": pattern_to_str(t["recognition_pattern"]), "correct_answer": t["correct_answer"],
                "participant_response": resp, "is_correct": None if resp is None else resp == t["correct_answer"],
                "reaction_time_ms": None if rt is None else round(rt, 1), "response_timeout": resp is None,
                "interference_stimulus": sec["text"] if sec else None,
                "interference_correct_answer": sec["correct"] if sec else None, "interference_response": sec_resp,
                "interference_accuracy": None if not sec else sec_resp == sec["correct"],
                "interference_reaction_time_ms": None if sec_rt is None else round(sec_rt, 1),
                "planned_fixation_duration_ms": 500, "actual_fixation_duration_ms": 500.0 + rng.choice([0, 0, 16.7]),
                "planned_stimulus_duration_ms": 500, "measured_stimulus_duration_ms": 500.0 + rng.choice([0, 0, 0, 16.7]),
                "planned_interference_duration_ms": 3000, "measured_interference_duration_ms": 3000.0,
                "planned_retention_duration_ms": 1000, "measured_retention_duration_ms": 1000.0,
                "inter_trial_interval_ms": float(t["planned_iti_ms"]), "focus_loss": False,
                "timing_quality_flag": None, "exclusion_status": "included", "exclusion_reason": None,
                "timestamp": "2026-12-01T10:05:00",
            })
    return {"Participants": pd.DataFrame(parts), "Contacts": pd.DataFrame(contacts),
            "Sessions": pd.DataFrame(sessions), "Raw_Trials": pd.DataFrame(trials)}


def write_synthetic_workbook(path: Path, **kw) -> Path:
    from app.reports.workbook import build_collection_workbook

    frames = simulate(**kw)
    return build_collection_workbook(path, kw.get("config") or ExperimentConfig(), frames,
                                     version_label="SYNTHETIC TEST", synthetic=True)


def write_synthetic_csvs(directory: Path, **kw) -> list[Path]:
    frames = simulate(**kw)
    directory.mkdir(parents=True, exist_ok=True)
    names = {"Participants": "SYNTHETIC_participants.csv", "Sessions": "SYNTHETIC_sessions.csv",
             "Raw_Trials": "SYNTHETIC_trials.csv", "Contacts": "SYNTHETIC_contacts.csv"}
    out = []
    for k, df in frames.items():
        p = directory / names[k]
        df.to_csv(p, index=False)
        out.append(p)
    return out
