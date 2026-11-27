import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ApiError, request } from "../api";
import { Alert, Button } from "../components/ui";
import { estimateRefreshRate } from "../engine/clock";
import { UploadQueue, safeLocalStorage } from "../engine/uploadQueue";
import type { ExperimentConfig, SessionStart, TrialPlan, TrialResult } from "../types";
import ExperimentScreen, { type StartPoint, useOtherExperimentOpen } from "./ExperimentScreen";
import { runDeviceCheck, summariseCheck, type DeviceCheckResult } from "./deviceCheck";
import { Consent, DeviceCheckScreen, Instructions, Message, Registration, Welcome, type RegistrationValues, type StudyInfo } from "./screens";

const ACTIVE_KEY = "smit_active_session";

interface ActiveSession {
  session_id: string;
  session_token: string;
  participant_id: string;
  session_type: "main" | "pilot";
}

type Step = "loading" | "error" | "closed" | "device_check" | "resume_prompt" | "welcome" | "consent" | "declined" | "register" | "instructions" | "experiment" | "finishing" | "complete" | "withdrawn";

function deviceInfo(hz: number | null, check: DeviceCheckResult | null) {
  return {
    charging: check?.facts.charging ?? null,
    battery_level: check?.facts.batteryLevel ?? null,
    device_check: check ? summariseCheck(check) : "not run",
    user_agent: navigator.userAgent.slice(0, 500),
    platform: (navigator as Navigator & { userAgentData?: { platform?: string } }).userAgentData?.platform ?? navigator.platform,
    language: navigator.language,
    screen_width: window.screen.width,
    screen_height: window.screen.height,
    device_pixel_ratio: window.devicePixelRatio,
    viewport_width: window.innerWidth,
    viewport_height: window.innerHeight,
    hardware_concurrency: navigator.hardwareConcurrency,
    estimated_refresh_rate: hz,
    touch_capable: "ontouchstart" in window,
  };
}

export default function ParticipantApp() {
  const [params] = useSearchParams();
  const pilotToken = params.get("pilot");
  const store = useMemo(() => safeLocalStorage(), []);
  const [step, setStep] = useState<Step>("loading");
  const [info, setInfo] = useState<StudyInfo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [session, setSession] = useState<SessionStart | null>(null);
  const [start, setStart] = useState<StartPoint>({ phase: "practice" });
  const [refresh, setRefresh] = useState<{ hz: number; frameMs: number } | null>(null);
  const [saveState, setSaveState] = useState<{ ok: boolean; saved: number; planned: number; pending: number; error: string | null } | null>(null);
  const queueRef = useRef<UploadQueue | null>(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [stored, setStored] = useState<ActiveSession | null>(null);
  const otherOpen = useOtherExperimentOpen(step === "instructions");
  const [measuring, setMeasuring] = useState(false);
  const [check, setCheck] = useState<DeviceCheckResult | null>(null);
  const [checking, setChecking] = useState(false);
  const checkingRef = useRef(false);
  const afterCheck = useRef<Step>("welcome");
  const checkRequired = info?.device_check_required !== false;

  /** Run the computer check; go on to `afterCheck` only if every item passes, otherwise stay on the check screen. */
  const runCheck = useCallback(async (): Promise<DeviceCheckResult | null> => {
    if (checkingRef.current) return null;
    checkingRef.current = true;
    setChecking(true);
    try {
      const r = await runDeviceCheck();
      setCheck(r);
      if (r.facts.windowFocused && r.facts.refreshHz) setRefresh({ hz: r.facts.refreshHz, frameMs: 1000 / r.facts.refreshHz });
      setStep(r.ok ? afterCheck.current : "device_check");
      return r;
    } finally {
      checkingRef.current = false;
      setChecking(false);
    }
  }, []);

  const gate = useCallback((next: Step) => {
    afterCheck.current = next;
    setCheck(null);
    setStep("device_check");
    void runCheck();
  }, [runCheck]);

  // While the check screen is up, check again automatically when the window comes back to the front.
  useEffect(() => {
    if (step !== "device_check") return;
    const again = () => { void runCheck(); };
    window.addEventListener("focus", again);
    return () => window.removeEventListener("focus", again);
  }, [step, runCheck]);

  // The first refresh estimate runs while the page loads, possibly in a background tab where browsers throttle
  // frames (e.g. 30 Hz instead of 120 Hz). Measure again when the participant starts, with the window in front —
  // as part of a second computer check, since power saving may have switched on since the page opened.
  const startExperiment = async () => {
    if (checkRequired) {
      afterCheck.current = "experiment";
      setMeasuring(true);
      try { await runCheck(); } finally { setMeasuring(false); }
      return;
    }
    setMeasuring(true);
    try {
      const r = await estimateRefreshRate();
      if (document.hasFocus() && !document.hidden) setRefresh({ hz: r.hz, frameMs: r.frameMs });
    } finally {
      setMeasuring(false);
    }
    setStep("experiment");
  };

  const makeQueue = useCallback((sid: string, token: string) => {
    queueRef.current?.dispose();
    const q = new UploadQueue(sid, (trials: TrialResult[]) =>
      request<{ saved: number[]; duplicates: number[] }>("POST", `/api/public/sessions/${sid}/trials`, { trials }, { "X-Session-Token": token }), store);
    q.onChange = () => setPendingCount(q.pending().length);
    queueRef.current = q;
    void q.flush();
    return q;
  }, [store]);

  // Initial load: study info, refresh estimate, interrupted-session detection
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const st = await request<StudyInfo>("GET", `/api/public/study${pilotToken ? `?pilot_token=${encodeURIComponent(pilotToken)}` : ""}`);
        if (!alive) return;
        setInfo(st);
        estimateRefreshRate().then((r) => alive && setRefresh({ hz: r.hz, frameMs: r.frameMs }));
        let active: ActiveSession | null = null;
        try { active = JSON.parse(store.getItem(ACTIVE_KEY) || "null"); } catch { active = null; }
        // Only offer to resume a session of the same kind as this link (a pilot session must not
        // appear on the main-study link and vice versa). The other session stays stored.
        const next: Step = active && active.session_type === st.mode ? "resume_prompt"
          : st.mode === "main" && !st.main_study_open ? "closed" : "welcome";
        if (next === "resume_prompt") setStored(active);
        // The computer check comes before anything else (consent, registration, resuming).
        if (next !== "closed" && st.device_check_required !== false) gate(next);
        else setStep(next);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setStep("error");
      }
    })();
    return () => { alive = false; };
  }, [pilotToken, store, gate]);

  const event = useCallback((ev: string, detail?: string) => {
    const s = session;
    if (!s) return;
    request("POST", `/api/public/sessions/${s.session_id}/events`, { event: ev, detail }, { "X-Session-Token": s.session_token }).catch(() => undefined);
  }, [session]);

  const register = async (v: RegistrationValues) => {
    if (!info) return;
    setBusy(true);
    setError(null);
    try {
      const hz = refresh?.hz ?? (await estimateRefreshRate()).hz;
      const res = await request<SessionStart>("POST", "/api/public/sessions", {
        consent: true,
        age: v.age ? Number(v.age) : null,
        gender: v.gender || null,
        academic_course: v.academic_course.trim() || null,
        email: v.email.trim() || null,
        session_type: info.mode,
        pilot_token: pilotToken,
        device: deviceInfo(hz, check),
      });
      store.setItem(ACTIVE_KEY, JSON.stringify({ session_id: res.session_id, session_token: res.session_token, participant_id: res.participant_id, session_type: res.session_type }));
      makeQueue(res.session_id, res.session_token);
      setSession(res);
      setStart({ phase: "practice" });
      setStep("instructions");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const resume = async () => {
    if (!stored) return;
    setStep("loading");
    try {
      const r = await request<{ participant_id: string; session_id: string; session_type: "main" | "pilot"; condition_order: string; experiment_version: string; config: ExperimentConfig; plan: TrialPlan; progress: { completion_status: string; saved_main_trials: number[] } }>(
        "GET", `/api/public/sessions/${stored.session_id}`, undefined, { "X-Session-Token": stored.session_token });
      const s: SessionStart = { ...r, session_token: stored.session_token };
      setSession(s);
      const q = makeQueue(r.session_id, stored.session_token);
      await q.flush();
      if (["completed", "withdrawn", "abandoned"].includes(r.progress.completion_status)) {
        await finish(s);
        return;
      }
      const savedSet = new Set([...r.progress.saved_main_trials, ...q.pending().filter((t) => !t.practice_trial).map((t) => t.trial_number)]);
      if (savedSet.size === 0) {
        setStart({ phase: "practice" });
        setStep("instructions");
      } else {
        let found: StartPoint | null = null;
        r.plan.blocks.forEach((b, bi) => b.trials.forEach((t, ti) => {
          if (!found && !savedSet.has(t.trial_number)) found = { phase: "main", blockIndex: bi, trialIndex: ti };
        }));
        if (!found) { await finish(s); return; }
        request("POST", `/api/public/sessions/${r.session_id}/events`, { event: "interrupted", detail: "browser closed or reloaded; session resumed" }, { "X-Session-Token": stored.session_token }).catch(() => undefined);
        setStart(found);
        // Check the computer again before continuing (power saving may have switched on meanwhile).
        if (checkRequired) gate("experiment");
        else setStep("experiment");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStep("resume_prompt");
    }
  };

  const discardStored = () => {
    store.removeItem(ACTIVE_KEY);
    setStored(null);
    if (info && info.mode === "main" && !info.main_study_open) setStep("closed");
    else setStep("welcome");
  };

  const finish = useCallback(async (s: SessionStart | null = session) => {
    if (!s) return;
    setStep("finishing");
    const q = queueRef.current;
    let ok = false;
    for (let i = 0; i < 5 && q; i++) {
      ok = await q.flush();
      if (ok) break;
      await new Promise((r) => setTimeout(r, 1500));
    }
    try {
      const res = await request<{ completion_status: string; main_trials_saved: number; n_main_planned: number }>(
        "POST", `/api/public/sessions/${s.session_id}/complete`, undefined, { "X-Session-Token": s.session_token });
      const pending = q?.pending().length ?? 0;
      setSaveState({ ok: pending === 0 && res.main_trials_saved >= res.n_main_planned, saved: res.main_trials_saved, planned: res.n_main_planned, pending, error: q?.lastError ?? null });
      if (pending === 0) store.removeItem(ACTIVE_KEY);
    } catch (e) {
      setSaveState({ ok: false, saved: 0, planned: s.plan.n_main, pending: q?.pending().length ?? 0, error: e instanceof Error ? e.message : String(e) });
    }
    if (document.fullscreenElement) document.exitFullscreen().catch(() => undefined);
    setStep("complete");
  }, [session, store]);

  const withdraw = async () => {
    if (session) {
      await queueRef.current?.flush();
      await request("POST", `/api/public/sessions/${session.session_id}/events`, { event: "withdrawn" }, { "X-Session-Token": session.session_token }).catch(() => undefined);
    }
    store.removeItem(ACTIVE_KEY);
    if (document.fullscreenElement) document.exitFullscreen().catch(() => undefined);
    setStep("withdrawn");
  };

  const downloadBackup = () => {
    const q = queueRef.current;
    if (!q || !session) return;
    const blob = new Blob([JSON.stringify({ session_id: session.session_id, participant_id: session.participant_id, pending_trials: q.pending() }, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `SMIT_backup_${session.participant_id}.json`;
    a.click();
  };

  const pilot = info?.mode === "pilot";

  switch (step) {
    case "loading":
      return <Message title="Loading…">Preparing the study…</Message>;
    case "error":
      return <Message title="Cannot start the study"><Alert kind="error">{error}</Alert><p>Please ask the researcher for help.</p></Message>;
    case "device_check":
      return <DeviceCheckScreen result={check} checking={checking} onRetry={() => void runCheck()} pilot={pilot} />;
    case "closed":
      return <Message title="The study is not open yet">The researcher has not yet finalised (locked) the experiment configuration. Please ask the researcher.</Message>;
    case "resume_prompt":
      return (
        <Message title="Unfinished session found" pilot={stored?.session_type === "pilot"}>
          <p>A session for participant <strong className="font-mono">{stored?.participant_id}</strong> was interrupted on this computer.</p>
          {error && <Alert kind="error">{error}</Alert>}
          <div className="flex flex-wrap justify-between gap-3 pt-2">
            <Button variant="secondary" onClick={discardStored}>This is a new participant</Button>
            <Button onClick={resume}>Resume this session</Button>
          </div>
          <p className="text-xs text-slate-500">Resuming continues from the first unsaved trial without creating a new session. The interruption is recorded.</p>
        </Message>
      );
    case "welcome":
      return info && <Welcome info={info} onNext={() => setStep("consent")} />;
    case "consent":
      return info && <Consent info={info} onAccept={() => setStep("register")} onDecline={() => setStep("declined")} />;
    case "declined":
      return <Message title="Thank you">You chose not to take part. No information has been stored. You may close this window.</Message>;
    case "register":
      return <Registration pilot={pilot} onSubmit={register} busy={busy} serverError={error} />;
    case "instructions":
      return session && <Instructions config={session.config} participantId={session.participant_id} pilot={session.session_type === "pilot"} refreshHz={refresh?.hz ?? null} onStart={() => void startExperiment()} busy={measuring} otherOpen={otherOpen} />;
    case "experiment":
      if (!session || !queueRef.current) return null;
      return (
        <ExperimentScreen config={session.config} plan={session.plan} start={start} refresh={refresh ?? { hz: 60, frameMs: 1000 / 60 }}
          queue={queueRef.current} pilot={session.session_type === "pilot"} onEvent={event} onFinished={() => void finish()} onWithdraw={withdraw} />
      );
    case "finishing":
      return <Message title="Saving your data…">Please wait a moment. {pendingCount > 0 && `${pendingCount} trial(s) still uploading.`}</Message>;
    case "complete":
      return (
        <Message title="Thank you — you have finished!" pilot={session?.session_type === "pilot"}>
          <p>Your participant ID is <strong className="font-mono text-lg">{session?.participant_id}</strong>. Please keep it if you may want to withdraw your data later.</p>
          {saveState?.ok ? (
            <Alert kind="success">All {saveState.saved} experimental trials were saved successfully.</Alert>
          ) : (
            <>
              <Alert kind="error">
                Not all data could be confirmed as saved ({saveState?.saved ?? 0} of {saveState?.planned ?? "?"} trials on the server; {saveState?.pending ?? 0} waiting to upload).
                {saveState?.error && <> Error: {saveState.error}</>} Please call the researcher — do not close this window.
              </Alert>
              <div className="flex flex-wrap gap-3">
                <Button onClick={() => void finish()}>Retry upload</Button>
                <Button variant="secondary" onClick={downloadBackup}>Download backup file (for the researcher)</Button>
              </div>
            </>
          )}
          <p className="text-sm text-slate-600 dark:text-slate-400">The study investigates how different kinds of mental activity affect short-term memory for spatial patterns. Please do not discuss the task with other people who may take part.</p>
        </Message>
      );
    case "withdrawn":
      return <Message title="You have stopped the study">Thank you for your time. Your session has been marked as withdrawn{session ? <> (participant ID <span className="font-mono">{session.participant_id}</span>)</> : null}. Please tell the researcher if you would like your data deleted.</Message>;
  }
}
