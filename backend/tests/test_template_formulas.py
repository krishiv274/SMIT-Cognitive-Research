"""The Participant_Summary formulas in the Excel template must reproduce the
application's own calculations (accuracy, RT, costs, timeout rate)."""
import ast
from pathlib import Path

import openpyxl
import pytest

from app.analysis.metrics import classify_trials, participant_condition_metrics, wide_summary
from app.experiment.config import AnalysisConfig, ExperimentConfig
from app.reports.workbook import build_collection_workbook
from tests.fixtures.synthetic import simulate

pycel = pytest.importorskip("pycel")
if not hasattr(ast, "Str"):  # pycel compatibility shim for Python ≥ 3.12 (test-only)
    ast.Str = lambda s=None, **k: ast.Constant(value=s)


def test_summary_formulas_match_python(tmp_path: Path):
    frames = simulate(n=2, seed=9)
    p = tmp_path / "t.xlsx"
    build_collection_workbook(p, ExperimentConfig(), frames, synthetic=True)
    xl = pycel.ExcelCompiler(filename=str(p))
    header = [c.value for c in openpyxl.load_workbook(p)["Participant_Summary"][1]]
    tr = frames["Raw_Trials"].copy()
    tr["timing_quality_flag"] = "ok"
    ct = classify_trials(tr, AnalysisConfig())
    w = wide_summary(participant_condition_metrics(ct), ct).set_index("participant_id")
    for row, pid in ((2, "SYN-001"), (3, "SYN-002")):
        assert xl.evaluate(f"Participant_Summary!A{row}") == pid
        for i, name in enumerate(header[4:], start=4):
            got = float(xl.evaluate(f"Participant_Summary!{chr(65 + i)}{row}"))
            assert got == pytest.approx(float(w.loc[pid, name]), abs=1e-9), name
    assert xl.evaluate("Participant_Summary!A4") == "", "blank rows stay blank"
