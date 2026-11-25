"""Unit tests: response handling, accuracy / RT / interference-cost calculations,
timing assessment and statistical procedures (cross-checked against Pingouin)."""
import numpy as np
import pandas as pd
import pingouin as pg
import pytest

from app.analysis import stats as S
from app.analysis.metrics import classify_trials, dprime_loglinear, participant_condition_metrics, pashler_k, wide_summary
from app.experiment.config import AnalysisConfig
from app.services.timing import assess_timing

ACFG = AnalysisConfig()


def trial(pid, cond, ans, resp, rt, flag="ok", practice=False, sec=None, sec_resp=None, sec_rt=None, excl="included", block=1):
    return {"participant_id": pid, "session_id": f"S-{pid}", "condition": cond, "correct_answer": ans,
            "participant_response": resp, "reaction_time_ms": rt, "timing_quality_flag": flag, "practice_trial": practice,
            "exclusion_status": excl, "interference_correct_answer": sec, "interference_response": sec_resp,
            "interference_reaction_time_ms": sec_rt, "block_number": block, "focus_loss": False}


def small_dataset():
    rows = [
        # A: 3 correct (600, 700, 150-anticipatory), 1 incorrect, 1 timeout, 1 technically invalid, 1 practice
        trial("P1", "A", "same", "same", 600), trial("P1", "A", "different", "different", 700),
        trial("P1", "A", "same", "same", 150), trial("P1", "A", "different", "same", 900),
        trial("P1", "A", "same", None, None), trial("P1", "A", "same", "same", 500, flag="invalid"),
        trial("P1", "A", "same", "different", 400, practice=True),
        # B: 2 trials, both correct; secondary 1 correct 1 missing
        trial("P1", "B", "same", "same", 800, sec="true", sec_resp="true", sec_rt=1200),
        trial("P1", "B", "different", "different", 1000, sec="false", sec_resp=None),
        # C: 2 trials, 1 correct
        trial("P1", "C", "same", "same", 900, sec="true", sec_resp="false", sec_rt=1500),
        trial("P1", "C", "different", "same", 950, sec="false", sec_resp="false", sec_rt=1100),
    ]
    return pd.DataFrame(rows)


def test_trial_classification():
    ct = classify_trials(small_dataset(), ACFG)
    assert len(ct) == 10, "practice excluded"
    a = ct[ct.condition == "A"]
    assert a.category.value_counts().to_dict() == {"correct": 3, "incorrect": 1, "timeout": 1, "technically_invalid": 1}
    assert int(a.anticipatory.sum()) == 1


def test_accuracy_rt_and_costs():
    ct = classify_trials(small_dataset(), ACFG)
    pcm = participant_condition_metrics(ct).set_index("condition")
    # A: valid = 5 (invalid excluded); correct = 3 -> 0.6; timeouts counted as errors
    assert pcm.loc["A", "n_valid"] == 5
    assert pcm.loc["A", "accuracy"] == pytest.approx(0.6)
    assert pcm.loc["A", "accuracy_answered"] == pytest.approx(3 / 4)
    assert pcm.loc["A", "timeout_rate"] == pytest.approx(0.2)
    # RT: correct, valid, >= 200 ms -> (600 + 700) / 2 (150 ms anticipatory excluded)
    assert pcm.loc["A", "mean_rt"] == pytest.approx(650)
    assert pcm.loc["B", "accuracy"] == pytest.approx(1.0)
    assert pcm.loc["B", "mean_rt"] == pytest.approx(900)
    assert pcm.loc["B", "sec_accuracy"] == pytest.approx(0.5), "missing secondary response counts as incorrect"
    assert pcm.loc["C", "sec_accuracy"] == pytest.approx(0.5)
    assert pcm.loc["C", "sec_mean_rt"] == pytest.approx(1100), "secondary RT from correct secondary responses only"
    w = wide_summary(pcm.reset_index(), ct).iloc[0]
    assert w["numerical_accuracy_cost"] == pytest.approx(0.6 - 1.0)  # A - B (negative = better under interference)
    assert w["visual_accuracy_cost"] == pytest.approx(0.6 - 0.5)
    assert w["numerical_rt_cost_ms"] == pytest.approx(900 - 650)  # B - A
    assert w["visual_rt_cost_ms"] == pytest.approx(900 - 650)
    assert w["overall_accuracy"] == pytest.approx(6 / 9)
    assert np.isnan(w["control_ies"]), "IES suppressed because accuracy < 60% in a condition"


def test_ies_computed_when_accuracy_sufficient():
    rows = [trial("P2", c, "same", "same", 500 + 100 * i) for i, c in enumerate("ABC") for _ in range(4)]
    rows += [trial("P2", c, "different", "same", 700) for c in "ABC"]
    ct = classify_trials(pd.DataFrame(rows), ACFG)
    w = wide_summary(participant_condition_metrics(ct), ct).iloc[0]
    assert w["control_accuracy"] == pytest.approx(0.8)
    assert w["control_ies"] == pytest.approx(500 / 0.8)


def test_signal_detection():
    assert dprime_loglinear(10, 10, 0, 10) == pytest.approx(2 * 1.6906216, rel=1e-4)
    assert dprime_loglinear(5, 10, 5, 10) == pytest.approx(0.0)
    assert pashler_k(0.8, 0.2, 4) == pytest.approx(3.0)


def test_timing_assessment():
    ok = {"planned_stimulus_duration_ms": 500, "measured_stimulus_duration_ms": 516.7, "planned_fixation_duration_ms": 500,
          "actual_fixation_duration_ms": 500, "planned_interference_duration_ms": 3000, "measured_interference_duration_ms": 3000}
    assert assess_timing(ok, 60, ACFG)[0] == "ok"
    assert assess_timing({**ok, "measured_stimulus_duration_ms": 540}, 60, ACFG)[0] == "invalid"
    assert assess_timing({**ok, "measured_interference_duration_ms": 3030}, 60, ACFG)[0] == "warning"
    assert assess_timing({**ok, "measured_interference_duration_ms": 3100}, 60, ACFG)[0] == "invalid"
    assert assess_timing({**ok, "focus_loss": True}, 60, ACFG)[0] == "invalid"
    assert assess_timing({**ok, "dropped_frames": 2}, 60, ACFG)[0] == "warning"
    # 144 Hz: tolerance shrinks (6.94 + 5 ms)
    assert assess_timing({**ok, "measured_stimulus_duration_ms": 515}, 144, ACFG)[0] == "invalid"
    f, note = assess_timing({"planned_stimulus_duration_ms": 500}, None, ACFG)
    assert f == "ok" and "not measured" in note


@pytest.fixture(scope="module")
def wide():
    rng = np.random.default_rng(7)
    n = 22
    base = rng.normal(0.8, 0.07, n)
    return pd.DataFrame({"A": base, "B": base - rng.normal(0.03, 0.05, n), "C": base - rng.normal(0.08, 0.06, n)})


def _long(w):
    return w.reset_index().melt(id_vars="index", var_name="cond", value_name="y")


def test_rm_anova_matches_pingouin(wide):
    r = S.rm_anova(wide)
    a = pg.rm_anova(data=_long(wide), dv="y", within="cond", subject="index", correction=True, detailed=True)
    assert r["F"] == pytest.approx(a.loc[0, "F"], rel=1e-8)
    assert r["p"] == pytest.approx(a.loc[0, "p_unc"], rel=1e-6)
    sph = pg.sphericity(data=_long(wide), dv="y", within="cond", subject="index")
    assert r["sphericity"]["W"] == pytest.approx(float(sph.W), rel=1e-6)
    assert r["sphericity"]["p"] == pytest.approx(float(sph.pval), rel=1e-6)
    assert r["sphericity"]["gg_epsilon"] == pytest.approx(pg.epsilon(data=_long(wide), dv="y", within="cond", subject="index"), rel=1e-6)
    # partial eta squared = SS_cond / (SS_cond + SS_error)
    assert r["partial_eta_sq"] == pytest.approx(r["ss_condition"] / (r["ss_condition"] + r["ss_error"]))


def test_paired_tests_and_effect_sizes(wide):
    t = S.paired_t(wide.A, wide.C)
    ref = pg.ttest(wide.A, wide.C, paired=True)
    assert t["t"] == pytest.approx(float(ref["T"].iloc[0]), rel=1e-8)
    d = wide.A - wide.C
    assert t["cohens_dz"] == pytest.approx(d.mean() / d.std(ddof=1))
    assert t["ci_low"] < t["mean_diff"] < t["ci_high"]
    w = S.wilcoxon(wide.A, wide.C)
    rw = pg.wilcoxon(wide.A, wide.C)
    assert w["p"] == pytest.approx(float(rw.iloc[0]["p_val" if "p_val" in rw else "p-val"]), rel=1e-6)
    assert w["rank_biserial"] == pytest.approx(float(rw.iloc[0]["RBC"]), rel=1e-6)


def test_friedman_and_holm(wide):
    f = S.friedman(wide)
    rf = pg.friedman(data=_long(wide), dv="y", within="cond", subject="index")
    assert f["chi2"] == pytest.approx(float(rf["Q"].iloc[0]))
    assert f["kendalls_w"] == pytest.approx(float(rf["W"].iloc[0]))
    assert S.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert S.holm([None, 0.02]) == [None, pytest.approx(0.02)]


def test_correlation_method_selection_and_ci():
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, 30)
    y = x * 0.5 + rng.normal(0, 1, 30)
    from scipy.stats import norm

    q = norm.ppf(np.linspace(0.02, 0.98, 30))  # exactly normal-shaped marginals
    assert S.correlation(q, q[::-1] * 0.3 + q * 0.7)["method"] == "pearson"
    c = S.correlation(x, y, method="pearson")
    rp = pg.corr(x, y)
    assert c["r"] == pytest.approx(float(rp["r"].iloc[0]))
    assert c["ci_low"] == pytest.approx(float(rp["CI95"].iloc[0][0]), abs=0.01)
    ages = [19, 19, 20, 20, 20, 21, 19, 22, 20, 19, 20, 21]
    c2 = S.correlation(ages, rng.normal(0, 1, 12))
    assert c2["method"] == "spearman", "few distinct ages / non-normal -> Spearman"
    assert "note" in S.correlation([1, 2, 3], [1, 2, 3])


def test_group_comparisons_and_welch_anova():
    rng = np.random.default_rng(5)
    a, b = rng.normal(0, 1, 8), rng.normal(1, 2, 9)
    r = S.two_groups(a, b, ("a", "b"))
    ref = pg.ttest(a, b, correction=True)
    assert r["welch_t"]["t"] == pytest.approx(float(ref["T"].iloc[0]))
    assert r["welch_t"]["df"] == pytest.approx(float(ref["dof"].iloc[0]))
    groups = {"x": rng.normal(0, 1, 7), "y": rng.normal(0.5, 1, 8), "z": rng.normal(1, 1.5, 9)}
    m = S.multi_groups(groups)
    df = pd.DataFrame([(k, v) for k, arr in groups.items() for v in arr], columns=["g", "v"])
    wa = pg.welch_anova(data=df, dv="v", between="g")
    assert m["welch_anova"]["F"] == pytest.approx(float(wa["F"].iloc[0]))


def test_degenerate_inputs_do_not_crash():
    w = pd.DataFrame({"A": [1.0, 1.0, 1.0], "B": [1.0, 1.0, 1.0], "C": [1.0, 1.0, 1.0]})
    assert "note" in S.rm_anova(w)
    assert "note" in S.friedman(w)
    assert "note" in S.paired_t(w.A, w.B)
    assert "note" in S.wilcoxon(w.A, w.B)
    assert S.describe([])["n"] == 0
