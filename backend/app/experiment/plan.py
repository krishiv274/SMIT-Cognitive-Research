"""Deterministic trial-plan generation for SMIT.

The full plan of a session (memory patterns, probes, secondary stimuli and
planned timings) is a pure function of (config, seed, condition_order). The
server generates it, stores it with the session and sends it to the browser,
which only executes it. This makes every session reproducible and testable.

Grid cells are indexed row-major from 0 (top-left) to size*size-1.
"""
from __future__ import annotations

import random
from itertools import combinations
from typing import Any

from .config import ExperimentConfig

CONDITIONS = ("A", "B", "C")
ORDERS = ("ABC", "ACB", "BAC", "BCA", "CAB", "CBA")
INTERFERENCE_TYPE = {"A": "none", "B": "numerical", "C": "visual"}


# ---------------------------------------------------------------------------
# Pattern utilities
# ---------------------------------------------------------------------------

def all_patterns(size: int, k: int) -> list[tuple[int, ...]]:
    return list(combinations(range(size * size), k))


def neighbours(cell: int, size: int) -> set[int]:
    """8-connected neighbours of a cell."""
    r, c = divmod(cell, size)
    out = set()
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < size and 0 <= cc < size:
                out.add(rr * size + cc)
    return out


def change_options(pattern: tuple[int, ...], size: int, change_type: str) -> list[tuple[int, int]]:
    """All (removed_cell, added_cell) moves that change exactly one filled cell."""
    filled = set(pattern)
    empty = [c for c in range(size * size) if c not in filled]
    opts = []
    for src in sorted(filled):
        for dst in empty:
            adj = dst in neighbours(src, size)
            if change_type == "adjacent" and not adj:
                continue
            if change_type == "non_adjacent" and adj:
                continue
            opts.append((src, dst))
    return opts


def apply_move(pattern: tuple[int, ...], move: tuple[int, int]) -> tuple[int, ...]:
    src, dst = move
    return tuple(sorted((set(pattern) - {src}) | {dst}))


def mirror_lr(pattern: tuple[int, ...], size: int) -> tuple[int, ...]:
    return tuple(sorted((r * size + (size - 1 - c)) for r, c in (divmod(x, size) for x in pattern)))


def is_symmetric(pattern: tuple[int, ...], size: int) -> bool:
    return mirror_lr(pattern, size) == tuple(sorted(pattern))


def symmetric_patterns(size: int, k: int) -> list[tuple[int, ...]]:
    return [p for p in all_patterns(size, k) if is_symmetric(p, size)]


def near_symmetric_patterns(size: int, k: int) -> list[tuple[int, ...]]:
    """Asymmetric patterns that are one cell-move away from a symmetric pattern.

    Using these as 'false' items prevents the symmetry judgement from being
    trivially easy (a random asymmetric pattern is usually obviously asymmetric).
    """
    out = set()
    for p in symmetric_patterns(size, k):
        for mv in change_options(p, size, "any"):
            q = apply_move(p, mv)
            if not is_symmetric(q, size):
                out.add(q)
    return sorted(out)


def pattern_to_str(pattern: tuple[int, ...] | list[int]) -> str:
    return "-".join(str(c) for c in sorted(pattern))


def pattern_from_str(s: str) -> tuple[int, ...]:
    s = str(s).strip()
    if not s:
        return tuple()
    sep = "-" if "-" in s else ("," if "," in s else " ")
    return tuple(sorted(int(x) for x in s.split(sep) if x.strip() != ""))


# ---------------------------------------------------------------------------
# Sequences with constraints
# ---------------------------------------------------------------------------

def max_run_length(seq: list[Any]) -> int:
    best = run = 0
    prev = object()
    for x in seq:
        run = run + 1 if x == prev else 1
        prev = x
        best = max(best, run)
    return best


def balanced_sequence(rng: random.Random, n_true: int, n_false: int, max_run: int,
                      labels: tuple[Any, Any] = (True, False)) -> list[Any]:
    """Random sequence with exact counts and no run longer than ``max_run``."""
    seq = [labels[0]] * n_true + [labels[1]] * n_false
    for _ in range(20000):
        rng.shuffle(seq)
        if max_run_length(seq) <= max_run:
            return list(seq)
    # Constructive fallback (extremely unbalanced counts only): alternate greedily
    out: list[Any] = []
    a, b = n_true, n_false
    while a or b:
        pick_a = a >= b
        if len(out) >= max_run and all(x == (labels[0] if pick_a else labels[1]) for x in out[-max_run:]):
            pick_a = not pick_a
        if pick_a and a:
            out.append(labels[0]); a -= 1
        elif b:
            out.append(labels[1]); b -= 1
        else:
            out.append(labels[0]); a -= 1
    return out


# ---------------------------------------------------------------------------
# Secondary stimuli
# ---------------------------------------------------------------------------

def make_equation(rng: random.Random, cfg, truth: bool, used: set[str]) -> dict:
    for _ in range(500):
        a = rng.randint(cfg.operand_min, cfg.operand_max)
        b = rng.randint(cfg.operand_min, cfg.operand_max)
        total = a + b
        shown = total if truth else total + rng.choice(cfg.false_offsets)
        if shown < 0:
            continue
        text = f"{a} + {b} = {shown}"
        if text not in used:
            used.add(text)
            return {"text": text, "a": a, "b": b, "shown": shown, "correct": "true" if truth else "false"}
    text = f"{a} + {b} = {shown}"
    return {"text": text, "a": a, "b": b, "shown": shown, "correct": "true" if truth else "false"}


def make_visual_distractor(rng: random.Random, size: int, vcfg, truth: bool,
                           avoid: set[tuple[int, ...]], pools: dict) -> dict:
    k = vcfg.highlight_count
    if vcfg.probe == "symmetry":
        pool = pools["sym"] if truth else pools["near_asym"]
        question = "symmetry"
    else:  # centre
        centre = (size * size) // 2
        key = "centre_on" if truth else "centre_off"
        if key not in pools:
            pools[key] = [p for p in all_patterns(size, k) if (centre in p) == truth]
        pool = pools[key]
        question = "centre"
    candidates = [p for p in pool if p not in avoid]
    if not candidates:  # extremely small pools only
        candidates = list(pool)
    pat = rng.choice(candidates)
    return {"pattern": list(pat), "text": pattern_to_str(pat), "question": question,
            "correct": "true" if truth else "false"}


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

def planned_timing(config: ExperimentConfig) -> dict:
    t = config.timing
    return {
        "fixation_ms": t.fixation_ms,
        "memory_stimulus_ms": t.memory_stimulus_ms,
        "post_stimulus_blank_ms": t.post_stimulus_blank_ms,
        "interference_ms": t.interference_ms,
        "retention_ms": t.retention_ms,
        "recognition_deadline_ms": t.recognition_deadline_ms,
    }


def _build_trial(rng, config, cond, pattern, trial_type, secondary, iti, number, block, practice):
    size = config.grid.size
    if trial_type == "different":
        move = rng.choice(change_options(pattern, size, config.trials.change_type))
        probe = apply_move(pattern, move)
        moved = {"from": move[0], "to": move[1]}
    else:
        probe = pattern
        moved = None
    trial = {
        "trial_number": number,
        "block_number": block,
        "condition": cond,
        "practice": practice,
        "original_pattern": list(pattern),
        "recognition_pattern": list(probe),
        "trial_type": trial_type,
        "correct_answer": trial_type,
        "moved_cell": moved,
        "interference_type": INTERFERENCE_TYPE[cond],
        "interference": secondary,
        "planned_iti_ms": iti,
        **{f"planned_{k}": v for k, v in planned_timing(config).items()},
    }
    return trial


def _secondary_for(rng, config, cond, truth, used_eq, pattern, probe_candidates, pools):
    if cond == "B":
        return make_equation(rng, config.secondary_tasks.numerical, truth, used_eq)
    if cond == "C":
        return make_visual_distractor(rng, config.grid.size, config.secondary_tasks.visual, truth,
                                      probe_candidates, pools)
    return None


def generate_plan(config: ExperimentConfig, seed: int, condition_order: str) -> dict:
    if condition_order not in ORDERS:
        raise ValueError(f"invalid condition order {condition_order!r}")
    rng = random.Random(seed)
    size, k = config.grid.size, config.grid.highlight_count
    pool = all_patterns(size, k)
    rng.shuffle(pool)
    vk = config.secondary_tasks.visual.highlight_count
    pools = {"sym": symmetric_patterns(size, vk), "near_asym": near_symmetric_patterns(size, vk)}
    if config.secondary_tasks.visual.probe == "symmetry" and (not pools["sym"] or not pools["near_asym"]):
        raise ValueError("symmetry probe impossible for this grid / highlight count")
    t = config.timing
    tr = config.trials

    def draw_iti() -> int:
        return rng.randint(t.iti_min_ms, t.iti_max_ms)

    def secondary_truths(n: int, prop: float) -> list[bool]:
        n_true = round(n * prop)
        seq = [True] * n_true + [False] * (n - n_true)
        rng.shuffle(seq)
        return seq

    # ---- Practice: fixed condition order A,A,B,B,C,C; each pair has one same + one different
    practice = []
    num = 0
    for cond in CONDITIONS:
        n = tr.practice_per_condition
        types = ["same", "different"] * (n // 2) + (["same"] if n % 2 else [])
        rng.shuffle(types)
        truths = secondary_truths(n, 0.5)
        used_eq: set[str] = set()
        for i in range(n):
            num += 1
            pattern = pool.pop()
            sec = None
            trial = _build_trial(rng, config, cond, pattern, types[i], None, draw_iti(), num, 0, True)
            avoid = {tuple(trial["original_pattern"]), tuple(trial["recognition_pattern"])}
            sec = _secondary_for(rng, config, cond, truths[i], used_eq, pattern, avoid, pools)
            trial["interference"] = sec
            practice.append(trial)

    # ---- Main blocks
    blocks = []
    num = 0
    for b_index, cond in enumerate(condition_order, start=1):
        n = tr.trials_per_condition
        n_same = round(n * tr.same_proportion)
        types = balanced_sequence(rng, n_same, n - n_same, tr.max_same_answer_run, ("same", "different"))
        if cond == "B":
            prop = config.secondary_tasks.numerical.true_proportion
        else:
            prop = config.secondary_tasks.visual.true_proportion
        truths = secondary_truths(n, prop)
        used_eq = set()
        trials = []
        for i in range(n):
            num += 1
            pattern = pool.pop()
            trial = _build_trial(rng, config, cond, pattern, types[i], None, draw_iti(), num, b_index, False)
            avoid = {tuple(trial["original_pattern"]), tuple(trial["recognition_pattern"])}
            trial["interference"] = _secondary_for(rng, config, cond, truths[i], used_eq, pattern, avoid, pools)
            trials.append(trial)
        blocks.append({"block_number": b_index, "condition": cond, "trials": trials})

    return {
        "seed": seed,
        "condition_order": condition_order,
        "grid_size": size,
        "highlight_count": k,
        "practice": practice,
        "blocks": blocks,
        "n_practice": len(practice),
        "n_main": sum(len(b["trials"]) for b in blocks),
    }


def assign_condition_order(counts: dict[str, int]) -> str:
    """Least-used order; ties broken by the fixed order ABC, ACB, BAC, BCA, CAB, CBA."""
    return min(ORDERS, key=lambda o: (counts.get(o, 0), ORDERS.index(o)))
