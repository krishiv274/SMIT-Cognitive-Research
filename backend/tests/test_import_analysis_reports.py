"""Integration tests: Excel/CSV/JSON import, validation errors, export round trip,
analysis pipeline and report generation — all with SYNTHETIC fixtures in temporary databases."""
import io
import json
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from app.reports.workbook import build_collection_workbook
from app.experiment.config import ExperimentConfig
from tests.fixtures.synthetic import simulate, write_synthetic_csvs, write_synthetic_workbook

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def upload(client, H, files):
    return client.post("/api/admin/import/validate", headers=H,
                       files=[("files", (name, data, XLSX if name.endswith("xlsx") else "text/csv")) for name, data in files])


@pytest.fixture(scope="module")
def syn_xlsx(tmp_path_factory):
    p = tmp_path_factory.mktemp("syn") / "SYNTHETIC_full.xlsx"
    write_synthetic_workbook(p, n=24, effect={"A": 0.85, "B": 0.8, "C": 0.72})
    return p.read_bytes()


def edited_workbook(tmp_path, mutate) -> bytes:
    frames = simulate(n=4, seed=11)
    mutate(frames)
    p = tmp_path / "edited.xlsx"
    build_collection_workbook(p, ExperimentConfig(), frames, synthetic=True)
    return p.read_bytes()


def test_blank_template_structure():
    root = Path(__file__).resolve().parents[2] / "templates"
    wb = openpyxl.load_workbook(root / "SMIT_Data_Collection_Template.xlsx")
    assert wb.sheetnames == ["Instructions", "Participants", "Contacts", "Sessions", "Raw_Trials", "Participant_Summary",
                             "Data_Dictionary", "Experiment_Configuration"]
    for s in ("Participants", "Sessions", "Raw_Trials"):
        ws = wb[s]
        assert ws.freeze_panes and ws.auto_filter.ref and ws.data_validations.dataValidation
        assert ws.max_row >= 2 and all(c.value is None for c in ws[2]), "no invented data"
    assert str(wb["Participant_Summary"]["E2"].value).startswith("=IF(")
    for f in ("Participant_Template.csv", "Session_Template.csv", "Trial_Data_Template.csv", "Participant_Summary_Template.xlsx"):
        assert (root / f).exists()


def test_full_xlsx_import_preview_commit_and_analysis(client, admin_headers, syn_xlsx):
    r = upload(client, admin_headers, [("SYNTHETIC_full.xlsx", syn_xlsx)]).json()
    rep = r["report"]
    assert r["status"] == "validated" and rep["ok"], rep["errors"][:3]
    assert rep["counts"]["participants"] == 24 and rep["counts"]["experimental_trials"] == 1440
    assert rep["preview"]["Raw_Trials"] and rep["derived_summary"]
    assert client.get("/api/admin/overview", headers=admin_headers).json()["registered_participants"] == 0, "nothing before confirm"
    c = client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).json()
    assert c["committed"] == {"participants": 24, "sessions": 24, "trials": 1584}
    assert c["analysis"]["n_participants_included"] == 24, "analysis triggered automatically"
    # duplicate file import is rejected
    again = upload(client, admin_headers, [("copy.xlsx", syn_xlsx)]).json()
    assert again["status"] == "invalid"
    assert any("already" in e["message"] for e in again["report"]["errors"])
    assert client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).status_code == 409
    res = client.get("/api/admin/analysis/latest", headers=admin_headers).json()["results"]
    assert res["meta"]["status"] == "ok"
    assert {h["id"] for h in res["hypotheses"]} == {"H0", "H1", "H2", "H3", "H4"}
    assert sum(f["available"] for f in res["figures"]) >= 16
    hist = client.get("/api/admin/import", headers=admin_headers).json()
    assert hist[0]["status"] == "invalid" and hist[1]["status"] == "committed"


def test_csv_import(client, admin_headers, tmp_path):
    paths = write_synthetic_csvs(tmp_path / "csv", n=6, seed=5)
    r = upload(client, admin_headers, [(p.name, p.read_bytes()) for p in paths]).json()
    assert r["status"] == "validated", r["report"]["errors"][:3]
    assert r["report"]["format"] == "csv"
    assert client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).json()["committed"]["trials"] == 6 * 66


def test_json_export_roundtrip(client, admin_headers, tmp_path, syn_xlsx):
    r = upload(client, admin_headers, [("s.xlsx", syn_xlsx)]).json()
    client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers)
    exported = client.get("/api/admin/export?fmt=json&scope=main", headers=admin_headers).content
    data = json.loads(exported)
    assert len(data["Raw_Trials"]) == 1584 and "example.invalid" not in exported.decode()
    xl = client.get("/api/admin/export?fmt=xlsx&scope=main", headers=admin_headers)
    assert set(pd.ExcelFile(io.BytesIO(xl.content)).sheet_names) >= {"Participants", "Sessions", "Raw_Trials"}
    # Re-importing into the same database is refused (no overwriting)
    again = upload(client, admin_headers, [("export.json", exported)]).json()
    assert again["status"] == "invalid"
    assert any("already exists" in e["message"] for e in again["report"]["errors"])


def test_summary_only_import(client, admin_headers, tmp_path):
    rows = pd.DataFrame([{"participant_id": f"SYN-S{i}", "age": 20 + i, "gender": "Female", "academic_course": "SYNTHETIC course",
                          "consent_status": True, "control_accuracy": 0.8, "numerical_accuracy": 0.75 - i / 100,
                          "visual_accuracy": 0.7 - i / 50, "control_mean_correct_rt_ms": 700 + i, "numerical_mean_correct_rt_ms": 760,
                          "visual_mean_correct_rt_ms": 780 + 2 * i} for i in range(6)])
    p = tmp_path / "summary.csv"
    rows.to_csv(p, index=False)
    r = upload(client, admin_headers, [("summary.csv", p.read_bytes())]).json()
    assert r["status"] == "validated" and r["import_kind"] == "summary"
    assert any("unavailable" in w["message"] for w in r["report"]["warnings"])
    c = client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).json()
    assert c["analysis"]["n_participants_included"] == 6


@pytest.mark.parametrize("mutate,expected", [
    (lambda f: f["Raw_Trials"].loc.__setitem__((0, "condition"), "D"), "must be one of"),
    (lambda f: f["Raw_Trials"].loc.__setitem__((7, "is_correct"), not f["Raw_Trials"].loc[7, "is_correct"]
                                               if f["Raw_Trials"].loc[7, "participant_response"] else True), "conflicts"),
    (lambda f: f["Raw_Trials"].__setitem__("trial_number", f["Raw_Trials"]["trial_number"].where(f["Raw_Trials"].index != 10, 1)), "Duplicate trial"),
    (lambda f: f["Participants"].loc.__setitem__((0, "consent_status"), False), "Consent is FALSE"),
    (lambda f: f["Participants"].loc.__setitem__((1, "age"), 16), "must be ≥ 18"),
    (lambda f: f["Raw_Trials"].loc.__setitem__((20, "recognition_pattern"), "0-1-2"), "same number of filled cells"),
    (lambda f: f["Raw_Trials"].loc.__setitem__((30, "participant_id"), "SYN-004" if f["Raw_Trials"].loc[30, "participant_id"] != "SYN-004" else "SYN-001"), "does not match"),
    (lambda f: f["Raw_Trials"].loc.__setitem__((40, "session_id"), "S-UNKNOWN"), "session not in the Sessions"),
    (lambda f: f["Participants"].loc.__setitem__((2, "academic_course"), "=cmd|' /C calc'!A0"), "formulas are not accepted"),
    (lambda f: f["Raw_Trials"].loc.__setitem__((50, "reaction_time_ms"), -5), "must be ≥ 0"),
])
def test_validation_errors_are_reported_not_corrected(client, admin_headers, tmp_path, mutate, expected):
    data = edited_workbook(tmp_path, mutate)
    r = upload(client, admin_headers, [("bad.xlsx", data)]).json()
    assert r["status"] == "invalid"
    msgs = " | ".join(e["message"] for e in r["report"]["errors"])
    assert expected in msgs, msgs[:500]
    assert all(("row" in e) for e in r["report"]["errors"])
    assert client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).status_code == 409


def test_missing_sheet_column_and_bad_files(client, admin_headers, tmp_path):
    frames = simulate(n=2, seed=3)
    frames["Raw_Trials"] = frames["Raw_Trials"].drop(columns=["condition"])
    p = tmp_path / "t.csv"
    frames["Raw_Trials"].assign(original_pattern=frames["Raw_Trials"]["original_pattern"]).to_csv(p, index=False)
    r = upload(client, admin_headers, [("t.csv", p.read_bytes())]).json()
    assert any("Participants" in e["message"] and "required" in e["message"] for e in r["report"]["errors"])
    assert any(e["column"] == "condition" for e in r["report"]["errors"])
    r = upload(client, admin_headers, [("fake.xlsx", b"not a zip")]).json()
    assert r["status"] == "invalid" and "not a valid .xlsx" in r["report"]["errors"][0]["message"]
    r = upload(client, admin_headers, [("macro.xlsm", b"PK\x03\x04")]).json()
    assert "macro-enabled" in r["report"]["errors"][0]["message"]
    r = upload(client, admin_headers, [("x.exe", b"MZ")]).json()
    assert "unsupported" in r["report"]["errors"][0]["message"]


def test_synthetic_guard_when_not_allowed(client, admin_headers, syn_xlsx, monkeypatch):
    from app.settings import get_settings

    monkeypatch.setattr(get_settings(), "allow_synthetic_imports", False)
    r = upload(client, admin_headers, [("s.xlsx", syn_xlsx)]).json()
    assert r["status"] == "invalid"
    assert any("SYNTHETIC" in e["message"] for e in r["report"]["errors"])


def test_cancel_import(client, admin_headers, syn_xlsx):
    r = upload(client, admin_headers, [("s.xlsx", syn_xlsx)]).json()
    assert client.post(f"/api/admin/import/{r['id']}/cancel", headers=admin_headers).json()["status"] == "cancelled"
    assert client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers).status_code == 409


def test_exclusion_rules_applied(client, admin_headers, tmp_path):
    frames = simulate(n=6, seed=21)
    t = frames["Raw_Trials"]
    # SYN-001: non-engagement — no responses on 40 % of experimental trials (rule R3)
    m = (t.participant_id == "SYN-001") & (~t.practice_trial)
    idx = t[m].index[:24]
    t.loc[idx, ["participant_response", "reaction_time_ms", "is_correct", "response_timeout"]] = [None, None, None, True]
    # SYN-002: secondary task ignored (rule R5)
    m2 = (t.participant_id == "SYN-002") & t.condition.isin(["B", "C"])
    t.loc[m2, ["interference_response", "interference_reaction_time_ms", "interference_accuracy"]] = [None, None, None]
    p = tmp_path / "excl.xlsx"
    build_collection_workbook(p, ExperimentConfig(), frames, synthetic=True)
    r = upload(client, admin_headers, [("excl.xlsx", p.read_bytes())]).json()
    assert r["status"] == "validated", r["report"]["errors"][:3]
    client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers)
    res = client.get("/api/admin/analysis/latest", headers=admin_headers).json()["results"]
    excl = {e["participant_id"]: e["rules"] for e in res["exclusions"]}
    assert "R3" in excl["SYN-001"] and "R5" in excl["SYN-002"]
    assert res["meta"]["n_included"] == 4
    assert "including_engagement_exclusions" in res["sensitivity"]


def test_insufficient_data_marks_results_pending(client, admin_headers):
    res = client.post("/api/admin/analysis/run", headers=admin_headers).json()["results"]
    assert res["meta"]["status"] == "no_data" and "confirmatory" not in res and res["figures"] == []


def test_report_and_presentation_generation(client, admin_headers, syn_xlsx, artifacts):
    # preliminary (no data)
    rep = client.post("/api/admin/reports/generate", headers=admin_headers).json()
    assert rep["kind"] == "preliminary" and {f["label"] for f in rep["files"]} >= {"PDF", "DOCX", "HTML"}
    html = client.get(f"/api/admin/reports/{rep['id']}/files/Preliminary_Research_Report.html", headers=admin_headers).text
    assert "PENDING" in html and "Hypothesis outcomes" not in html
    # final, from synthetic data — must carry the SYNTHETIC watermark
    r = upload(client, admin_headers, [("s.xlsx", syn_xlsx)]).json()
    client.post(f"/api/admin/import/{r['id']}/commit", headers=admin_headers)
    rep = client.post("/api/admin/reports/generate", headers=admin_headers).json()
    assert rep["kind"] == "final"
    names = {f["name"] for f in rep["files"]}
    assert names == {"SMIT_Research_Report.pdf", "SMIT_Research_Report.docx", "SMIT_Research_Report.html", "SMIT_Statistical_Results.xlsx"}
    html = client.get(f"/api/admin/reports/{rep['id']}/files/SMIT_Research_Report.html", headers=admin_headers).text
    assert "SYNTHETIC TEST DATA" in html and "Hypothesis outcomes" in html and "@example" not in html
    pdf = client.get(f"/api/admin/reports/{rep['id']}/files/SMIT_Research_Report.pdf", headers=admin_headers).content
    assert pdf.startswith(b"%PDF")
    (artifacts / "SYNTHETIC_test_report.pdf").write_bytes(pdf)
    xl = client.get(f"/api/admin/reports/{rep['id']}/files/SMIT_Statistical_Results.xlsx", headers=admin_headers).content
    assert {"Summary", "Hypotheses", "Descriptives", "Correlations"} <= set(pd.ExcelFile(io.BytesIO(xl)).sheet_names)
    pres = client.post("/api/admin/reports/presentation", headers=admin_headers).json()
    pp = client.get(f"/api/admin/reports/{pres['id']}/files/SMIT_Presentation.pptx", headers=admin_headers)
    from pptx import Presentation

    deck = Presentation(io.BytesIO(pp.content))
    text = " ".join(sh.text_frame.text for s in deck.slides for sh in s.shapes if sh.has_text_frame)
    assert len(deck.slides) >= 20 and "16. Results" in text and "PENDING" not in text
    assert client.get("/api/admin/reports/999/files/x.pdf", headers=admin_headers).status_code == 404
    assert client.get("/api/admin/templates/../backend/app/main.py", headers=admin_headers).status_code == 404
    assert client.get("/api/admin/templates/SMIT_Data_Collection_Template.xlsx", headers=admin_headers).status_code == 200


def test_reports_use_their_own_design_figures(client, admin_headers):
    """Generating a report or slides must not overwrite the shared figures in experiment/stimuli, and the
    trial counts in the text must come from the configuration (not the 20-per-condition specification)."""
    import hashlib

    from app.settings import REPO_ROOT

    stim = REPO_ROOT / "experiment" / "stimuli"
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stim.glob("*.png"))}
    rep = client.post("/api/admin/reports/generate", headers=admin_headers).json()
    client.post("/api/admin/reports/presentation", headers=admin_headers)
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stim.glob("*.png"))}
    assert before == after
    cfg = client.get("/api/admin/configs", headers=admin_headers).json()
    used = next((c for c in cfg if c["is_active_main"]), cfg[0])["config"]["trials"]["trials_per_condition"]
    name = next(f["name"] for f in rep["files"] if f["label"] == "HTML")
    html = client.get(f"/api/admin/reports/{rep['id']}/files/{name}", headers=admin_headers).text
    assert f"{3 * used} experimental trials ({used} per condition)" in html
