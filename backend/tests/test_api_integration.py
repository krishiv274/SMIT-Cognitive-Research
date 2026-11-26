"""Integration tests through the HTTP API (temporary database)."""


def lock_default(client, H):
    cfg = client.get("/api/admin/configs", headers=H).json()[0]
    r = client.post(f"/api/admin/configs/{cfg['id']}/lock", headers=H, json={"justification": "integration test lock"})
    assert r.status_code == 200
    return r.json()


REG = {"consent": True, "age": 21, "gender": "Female", "academic_course": "BSc Psychology", "email": "p1@example.test",
       "device": {"estimated_refresh_rate": 60}}


def trial_payload(t, resp="same", rt=650.0):
    return {"trial_number": t["trial_number"], "practice_trial": t["practice"], "practice_attempt": 1 if t["practice"] else 0,
            "participant_response": resp, "reaction_time_ms": rt,
            "interference_response": "true" if t["interference"] else None, "interference_reaction_time_ms": 1100 if t["interference"] else None,
            "actual_fixation_duration_ms": 500, "measured_stimulus_duration_ms": 500, "measured_interference_duration_ms": 3000,
            "measured_retention_duration_ms": 1000, "inter_trial_interval_ms": t["planned_iti_ms"], "refresh_rate_hz": 60}


def test_admin_endpoints_require_login(client):
    assert client.get("/api/admin/overview").status_code == 401
    assert client.post("/api/admin/login", json={"password": "wrong"}).status_code == 401
    assert client.get("/api/admin/overview", headers={"Authorization": "Bearer forged.token"}).status_code == 401


def test_main_study_closed_until_locked(client, admin_headers):
    assert client.get("/api/public/study").json()["main_study_open"] is False
    assert client.post("/api/public/sessions", json=REG).status_code == 409
    lock_default(client, admin_headers)
    info = client.get("/api/public/study").json()
    assert info["main_study_open"] and info["experiment_version"].startswith("SMIT-v1-")
    assert "hypothes" not in str(info).lower(), "welcome info must not reveal hypotheses"


def test_registration_validation_and_consent(client, admin_headers):
    lock_default(client, admin_headers)
    assert client.post("/api/public/sessions", json={**REG, "consent": False}).status_code == 400
    assert client.post("/api/public/sessions", json={**REG, "age": 17}).status_code == 422
    assert client.post("/api/public/sessions", json={**REG, "email": "bad"}).status_code == 422
    assert client.post("/api/public/sessions", json={**REG, "gender": "unknown"}).status_code == 422
    assert client.post("/api/public/sessions", json={**REG, "academic_course": "=HYPERLINK(1)"}).status_code == 422
    assert client.post("/api/public/sessions", json={**REG, "email": None}).status_code == 422
    r = client.post("/api/public/sessions", json=REG)
    assert r.status_code == 200
    d = r.json()
    assert d["participant_id"] == "P001" and d["condition_order"] == "ABC"
    assert d["plan"]["n_main"] == 60
    assert client.post("/api/public/sessions", json={**REG, "email": "P1@Example.TEST "}).status_code == 409, "duplicate email"


def test_full_session_trial_storage_and_completion(client, admin_headers):
    lock_default(client, admin_headers)
    d = client.post("/api/public/sessions", json=REG).json()
    sid, H = d["session_id"], {"X-Session-Token": d["session_token"]}
    assert client.post(f"/api/public/sessions/{sid}/trials", json={"trials": []}).status_code == 404, "token required"
    plan = d["plan"]
    prac = [trial_payload(t) for t in plan["practice"]]
    assert client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": prac}).json()["saved"] == list(range(1, 7))
    main = [t for b in plan["blocks"] for t in b["trials"]]
    payload = [trial_payload(t, resp=t["correct_answer"] if i % 4 else ("different" if t["correct_answer"] == "same" else "same"))
               for i, t in enumerate(main)]
    payload[5].update(participant_response=None, reaction_time_ms=None, response_timeout=True)
    r = client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": payload[:30]})
    assert len(r.json()["saved"]) == 30
    # duplicate submission is idempotent
    r = client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": payload[:30]})
    assert r.json()["saved"] == [] and len(r.json()["duplicates"]) == 30
    prog = client.get(f"/api/public/sessions/{sid}/progress", headers=H).json()
    assert len(prog["saved_main_trials"]) == 30 and prog["completion_status"] == "in_progress"
    assert client.post(f"/api/public/sessions/{sid}/complete", headers=H).json()["completion_status"] == "incomplete"
    client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": payload[30:]})
    done = client.post(f"/api/public/sessions/{sid}/complete", headers=H).json()
    assert done["completion_status"] == "completed" and done["main_trials_saved"] == 60
    detail = client.get(f"/api/admin/sessions/{sid}", headers=admin_headers).json()
    trials = [t for t in detail["trials"] if not t["practice_trial"]]
    by_n = {t["trial_number"]: t for t in trials}
    # server recomputes correctness from ITS plan (client cannot alter answers)
    for i, t in enumerate(main):
        row = by_n[t["trial_number"]]
        assert row["original_pattern"] == "-".join(map(str, t["original_pattern"]))
        if i == 5:
            assert row["response_timeout"] and row["is_correct"] is None and row["reaction_time_ms"] is None
        else:
            assert row["is_correct"] == (i % 4 != 0)
        if t["interference"]:
            assert row["interference_accuracy"] == (t["interference"]["correct"] == "true")
    assert all(t["timing_quality_flag"] == "ok" for t in trials)


def test_trial_not_in_plan_and_out_of_window_rt(client, admin_headers):
    lock_default(client, admin_headers)
    d = client.post("/api/public/sessions", json=REG).json()
    sid, H = d["session_id"], {"X-Session-Token": d["session_token"]}
    t = d["plan"]["blocks"][0]["trials"][0]
    bad = trial_payload(t)
    bad["trial_number"] = 999
    assert client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": [bad]}).status_code == 422
    late = trial_payload(t, rt=2500)
    client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": [late]})
    row = [x for x in client.get(f"/api/admin/sessions/{sid}", headers=admin_headers).json()["trials"] if not x["practice_trial"]][0]
    assert row["response_timeout"] is True and row["participant_response"] is None
    assert "outside response window" in row["timing_notes"]


def test_withdrawal_blocks_further_data(client, admin_headers):
    lock_default(client, admin_headers)
    d = client.post("/api/public/sessions", json=REG).json()
    sid, H = d["session_id"], {"X-Session-Token": d["session_token"]}
    assert client.post(f"/api/public/sessions/{sid}/events", headers=H, json={"event": "withdrawn"}).json()["completion_status"] == "withdrawn"
    t = d["plan"]["blocks"][0]["trials"][0]
    assert client.post(f"/api/public/sessions/{sid}/trials", headers=H, json={"trials": [trial_payload(t)]}).status_code == 409
    p = client.get("/api/admin/participants?scope=main", headers=admin_headers).json()[0]
    assert p["status"] == "withdrawn"


def test_pilot_sessions_isolated_from_main(client, admin_headers):
    assert client.post("/api/public/sessions", json={**REG, "session_type": "pilot"}).status_code == 403
    launch = client.post("/api/admin/pilot/launch", headers=admin_headers, json={}).json()
    r = client.post("/api/public/sessions", json={"consent": True, "session_type": "pilot", "pilot_token": launch["pilot_token"]})
    assert r.status_code == 200 and r.json()["participant_id"] == "PILOT-001"
    ov = client.get("/api/admin/overview", headers=admin_headers).json()
    assert ov["registered_participants"] == 0 and ov["pilot_sessions"] == 1
    run = client.post("/api/admin/analysis/run", headers=admin_headers).json()
    assert run["results"]["meta"]["n_registered"] == 0, "pilot data never enter the main analysis"


def test_counterbalancing_across_sessions(client, admin_headers):
    lock_default(client, admin_headers)
    orders = [client.post("/api/public/sessions", json={**REG, "email": f"p{i}@example.test"}).json()["condition_order"] for i in range(7)]
    assert orders == ["ABC", "ACB", "BAC", "BCA", "CAB", "CBA", "ABC"]


def test_config_versioning_and_locking(client, admin_headers):
    H = admin_headers
    base = client.get("/api/admin/configs/default", headers=H).json()
    base["timing"]["memory_stimulus_ms"] = 400
    new = client.post("/api/admin/configs", headers=H, json={"config": base, "notes": "pilot change"}).json()
    assert new["status"] == "draft" and new["deviations_from_specification"]
    bad = dict(base, timing={**base["timing"], "iti_min_ms": 2000})
    assert client.put(f"/api/admin/configs/{new['id']}", headers=H, json={"config": bad}).status_code == 422
    assert client.post(f"/api/admin/configs/{new['id']}/lock", headers=H, json={"justification": "short"}).status_code == 422
    locked = client.post(f"/api/admin/configs/{new['id']}/lock", headers=H, json={"justification": "piloted with volunteers"}).json()
    assert locked["status"] == "locked" and locked["is_active_main"]
    assert client.put(f"/api/admin/configs/{new['id']}", headers=H, json={"config": base}).status_code == 409, "locked cannot change"
    actions = [a["action"] for a in client.get("/api/admin/audit", headers=H).json()]
    assert "config_locked" in actions and "config_created" in actions
    prev = client.get("/api/admin/configs/{}/preview?seed=3&order=CBA".format(new["id"]), headers=H).json()
    assert prev["plan"]["blocks"][0]["trials"][0]["planned_memory_stimulus_ms"] == 400


def test_privacy_contacts_export_and_deletion(client, admin_headers):
    H = admin_headers
    lock_default(client, H)
    d = client.post("/api/public/sessions", json=REG).json()
    for fmt in ("json", "csv", "xlsx"):
        r = client.get(f"/api/admin/export?fmt={fmt}&scope=all", headers=H)
        assert r.status_code == 200
        assert b"p1@example.test" not in r.content
    assert client.get(f"/api/admin/participants/{d['participant_id']}/contact", headers=H).json()["email"] == "p1@example.test"
    audit = client.get("/api/admin/audit", headers=H).json()
    assert any(a["action"] == "contact_viewed" for a in audit)
    assert "p1@example.test" not in str(audit), "audit log never stores emails"
    assert client.request("DELETE", f"/api/admin/participants/{d['participant_id']}", headers=H,
                          json={"reason": "requested", "confirm_participant_id": "wrong"}).status_code == 422
    r = client.request("DELETE", f"/api/admin/participants/{d['participant_id']}", headers=H,
                       json={"reason": "participant requested deletion", "confirm_participant_id": d["participant_id"]})
    assert r.status_code == 200
    assert client.get("/api/admin/participants", headers=H).json() == []
    assert client.get(f"/api/public/sessions/{d['session_id']}", headers={"X-Session-Token": d["session_token"]}).status_code == 404


def test_status_exclusion_and_trial_exclusion(client, admin_headers):
    H = admin_headers
    lock_default(client, H)
    d = client.post("/api/public/sessions", json=REG).json()
    t = d["plan"]["blocks"][0]["trials"][0]
    client.post(f"/api/public/sessions/{d['session_id']}/trials", headers={"X-Session-Token": d["session_token"]}, json={"trials": [trial_payload(t)]})
    r = client.post(f"/api/admin/participants/{d['participant_id']}/status", headers=H, json={"status": "excluded", "reason": "did not understand task"})
    assert r.json()["status"] == "excluded"
    tid = client.get(f"/api/admin/sessions/{d['session_id']}", headers=H).json()["trials"][0]["trial_id"]
    assert client.post(f"/api/admin/trials/{tid}/exclusion", headers=H, json={"excluded": True, "reason": "fire alarm"}).json()["exclusion_status"] == "excluded"


def test_security_headers_and_settings(client, admin_headers):
    r = client.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-frame-options"] == "DENY"
    s = client.put("/api/admin/settings", headers=admin_headers, json={"university_name": "Test University", "unknown_key": "x"}).json()
    assert s["university_name"] == "Test University" and "unknown_key" not in s
    assert client.get("/api/public/study").json()["settings"]["university_name"] == "Test University"
    assert "pilot_observations" not in client.get("/api/public/study").json()["settings"]


def test_login_lockout_after_repeated_failures(client, monkeypatch):
    from app.api import admin as admin_api

    monkeypatch.setattr(admin_api.time, "sleep", lambda s: None)
    admin_api._FAILED_LOGINS.clear()
    for _ in range(admin_api.MAX_FAILED_LOGINS):
        assert client.post("/api/admin/login", json={"password": "guess"}).status_code == 401
    assert client.post("/api/admin/login", json={"password": "guess"}).status_code == 429
    assert client.post("/api/admin/login", json={"password": "test-password"}).status_code == 429, "locked even for the right password"
    admin_api._FAILED_LOGINS.clear()
    assert client.post("/api/admin/login", json={"password": "test-password"}).status_code == 200
