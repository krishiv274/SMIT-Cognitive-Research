"""Unit tests: pattern generation, same/different logic, stimulus balance, randomisation,
counterbalancing and configuration validation."""
from collections import Counter

import numpy as np
import pytest

from app.experiment.config import ExperimentConfig
from app.experiment.plan import (
    ORDERS,
    apply_move,
    assign_condition_order,
    change_options,
    generate_plan,
    is_symmetric,
    max_run_length,
    near_symmetric_patterns,
    neighbours,
    pattern_from_str,
    pattern_to_str,
    symmetric_patterns,
)

CFG = ExperimentConfig()


def all_trials(plan):
    return plan["practice"] + [t for b in plan["blocks"] for t in b["trials"]]


def test_plan_size_and_structure():
    p = generate_plan(CFG, 1, "BCA")
    assert p["n_practice"] == 6 and p["n_main"] == 60
    assert [b["condition"] for b in p["blocks"]] == ["B", "C", "A"]
    assert [t["condition"] for t in p["practice"]] == ["A", "A", "B", "B", "C", "C"]
    assert [t["trial_number"] for b in p["blocks"] for t in b["trials"]] == list(range(1, 61))
    assert all(b["block_number"] == i for i, b in enumerate(p["blocks"], 1))


@pytest.mark.parametrize("seed", range(25))
def test_patterns_and_probe_logic(seed):
    p = generate_plan(CFG, seed, ORDERS[seed % 6])
    trials = all_trials(p)
    pats = [tuple(t["original_pattern"]) for t in trials]
    assert len(set(pats)) == len(pats) == 66, "no pattern repeats within a session"
    for t in trials:
        o, r = set(t["original_pattern"]), set(t["recognition_pattern"])
        assert len(o) == len(r) == 4
        assert all(0 <= c <= 8 for c in o | r)
        if t["trial_type"] == "same":
            assert o == r
        else:
            assert len(o - r) == 1 and len(r - o) == 1, "exactly one cell moved"
        assert t["correct_answer"] == t["trial_type"]


@pytest.mark.parametrize("seed", range(25))
def test_balance_and_run_constraint(seed):
    p = generate_plan(CFG, seed, "ACB")
    for b in p["blocks"]:
        types = [t["trial_type"] for t in b["trials"]]
        assert Counter(types) == {"same": 10, "different": 10}
        assert max_run_length(types) <= 3
        if b["condition"] in "BC":
            truth = Counter(t["interference"]["correct"] for t in b["trials"])
            assert truth == {"true": 10, "false": 10}
        else:
            assert all(t["interference"] is None for t in b["trials"])
    for cond in "ABC":
        pt = [t for t in p["practice"] if t["condition"] == cond]
        assert sorted(t["trial_type"] for t in pt) == ["different", "same"]


def test_seed_reproducibility_and_variation():
    assert generate_plan(CFG, 42, "ABC") == generate_plan(CFG, 42, "ABC")
    assert generate_plan(CFG, 42, "ABC") != generate_plan(CFG, 43, "ABC")


def test_equations_are_correctly_labelled():
    for seed in range(20):
        for t in all_trials(generate_plan(CFG, seed, "ABC")):
            if t["condition"] == "B":
                e = t["interference"]
                assert (e["a"] + e["b"] == e["shown"]) == (e["correct"] == "true")
                assert 2 <= e["a"] <= 9 and 2 <= e["b"] <= 9


def test_symmetry_distractors_correct_and_independent():
    assert all(is_symmetric(p, 3) for p in symmetric_patterns(3, 4))
    assert not any(is_symmetric(p, 3) for p in near_symmetric_patterns(3, 4))
    overlaps = {"same": [], "different": []}
    for seed in range(200):
        for b in generate_plan(CFG, seed, "CAB")["blocks"]:
            if b["condition"] != "C":
                continue
            for t in b["trials"]:
                d = t["interference"]
                assert is_symmetric(tuple(d["pattern"]), 3) == (d["correct"] == "true")
                assert tuple(d["pattern"]) != tuple(t["original_pattern"])
                assert tuple(d["pattern"]) != tuple(t["recognition_pattern"])
                overlaps[t["trial_type"]].append(len(set(d["pattern"]) & set(t["original_pattern"])))
    # The distractor carries no systematic information about the answer
    diff = abs(np.mean(overlaps["same"]) - np.mean(overlaps["different"]))
    assert diff < 0.15, diff


def test_change_types():
    pat = (0, 1, 3, 4)
    adj = change_options(pat, 3, "adjacent")
    non = change_options(pat, 3, "non_adjacent")
    assert all(dst in neighbours(src, 3) for src, dst in adj)
    assert all(dst not in neighbours(src, 3) for src, dst in non)
    assert len(change_options(pat, 3, "any")) == 4 * 5
    assert apply_move((0, 1, 2, 3), (0, 8)) == (1, 2, 3, 8)
    cfg = ExperimentConfig.model_validate({**CFG.to_json_dict(), "trials": {**CFG.trials.model_dump(), "change_type": "adjacent"}})
    for t in all_trials(generate_plan(cfg, 3, "ABC")):
        if t["trial_type"] == "different":
            assert t["moved_cell"]["to"] in neighbours(t["moved_cell"]["from"], 3)


def test_pattern_string_roundtrip():
    assert pattern_to_str([7, 0, 5, 2]) == "0-2-5-7"
    assert pattern_from_str("0-2-5-7") == (0, 2, 5, 7)
    assert pattern_from_str("7,5, 2,0") == (0, 2, 5, 7)


def test_counterbalancing_least_used_and_even():
    counts = {o: 0 for o in ORDERS}
    seq = []
    for _ in range(24):
        o = assign_condition_order(counts)
        counts[o] += 1
        seq.append(o)
    assert seq[:6] == list(ORDERS)
    assert set(counts.values()) == {4}
    # a withdrawn participant's slot is refilled first
    assert assign_condition_order({**{o: 4 for o in ORDERS}, "BAC": 3}) == "BAC"


def test_iti_jitter_within_range():
    itis = [t["planned_iti_ms"] for s in range(10) for t in all_trials(generate_plan(CFG, s, "ABC"))]
    assert min(itis) >= 800 and max(itis) <= 1200
    assert len(set(itis)) > 50


def test_config_validation_and_hash():
    base = CFG.to_json_dict()
    with pytest.raises(Exception):
        ExperimentConfig.model_validate({**base, "timing": {**base["timing"], "iti_min_ms": 1500, "iti_max_ms": 800}})
    with pytest.raises(Exception):
        ExperimentConfig.model_validate({**base, "trials": {**base["trials"], "trials_per_condition": 21}})  # 10.5 same trials
    with pytest.raises(Exception):
        ExperimentConfig.model_validate({**base, "keys": {**base["keys"], "different": "f"}})
    with pytest.raises(Exception):  # too few distinct patterns for 66 trials (C(9,8) = 9)
        ExperimentConfig.model_validate({**base, "grid": {**base["grid"], "highlight_count": 8}})
    renamed = ExperimentConfig.model_validate({**base, "name": "other name"})
    assert renamed.canonical_hash() == CFG.canonical_hash()
    changed = ExperimentConfig.model_validate({**base, "timing": {**base["timing"], "memory_stimulus_ms": 400}})
    assert changed.canonical_hash() != CFG.canonical_hash()
    assert changed.deviates_from_specification() == ["timing.memory_stimulus_ms = 400 (specification: 500)"]
    assert CFG.deviates_from_specification() == []
