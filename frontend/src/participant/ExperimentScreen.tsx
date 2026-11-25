/**
 * Runs practice and experimental blocks. Between trials the canvas stays mounted; between blocks
 * standardised instruction/break screens are shown. No performance information is shown during
 * experimental trials (feedback only in practice).
 */
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { browserClock } from "../engine/clock";
import { CanvasRenderer } from "../engine/renderer";
import { TrialRunner } from "../engine/trialRunner";
import type { UploadQueue } from "../engine/uploadQueue";
import type { Condition, ExperimentConfig, PlanTrial, TrialPlan } from "../types";
import { Button } from "../components/ui";
import { Key } from "./screens";

export type StartPoint = { phase: "practice" } | { phase: "main"; blockIndex: number; trialIndex: number };

interface Props {
  config: ExperimentConfig;
  plan: TrialPlan;
  start: StartPoint;
  refresh: { hz: number; frameMs: number };
  queue: UploadQueue;
  pilot: boolean;
  onEvent: (event: string, detail?: string) => void;
  onFinished: () => void;
  onWithdraw: () => void;
}

type Step =
  | { kind: "practice_cond_intro"; cond: Condition; index: number }
  | { kind: "running"; trials: PlanTrial[]; practice: boolean; next: Step }
  | { kind: "practice_end" }
  | { kind: "block_intro"; blockIndex: number; resume: boolean }
  | { kind: "break"; nextBlock: number }
  | { kind: "paused"; resumeStep: Step }
  | { kind: "done" };

const COND_TEXT: Record<Condition, { name: string; body: (c: ExperimentConfig) => string }> = {
  A: { name: "Hold", body: () => "In this block the middle phase is EMPTY. Just keep the blue pattern in mind until the second blue grid appears." },
  B: { name: "Equation", body: (c) => `In this block an EQUATION appears in the middle phase. Decide whether it is correct: ${c.keys.secondary_true.toUpperCase()} = True, ${c.keys.secondary_false.toUpperCase()} = False — and keep remembering the blue pattern.` },
  C: {
    name: "Symmetry",
    body: (c) => c.secondary_tasks.visual.probe === "symmetry"
      ? `In this block an ORANGE grid appears in the middle phase. Is the orange pattern symmetrical (left mirrors right)? ${c.keys.secondary_true.toUpperCase()} = Yes, ${c.keys.secondary_false.toUpperCase()} = No. Do NOT remember the orange pattern — keep remembering the blue one.`
      : `In this block an ORANGE grid appears in the middle phase. Is its centre square filled? ${c.keys.secondary_true.toUpperCase()} = Yes, ${c.keys.secondary_false.toUpperCase()} = No. Keep remembering the blue pattern.`,
  },
};

export function requestFullscreen(): void {
  const el = document.documentElement;
  if (!document.fullscreenElement && el.requestFullscreen) el.requestFullscreen().catch(() => undefined);
}

export default function ExperimentScreen({ config, plan, start, refresh, queue, pilot, onEvent, onFinished, onWithdraw }: Props) {
  const practiceAttempt = useRef(1);
  const [step, setStep] = useState<Step>(() =>
    start.phase === "practice" ? { kind: "practice_cond_intro", cond: "A", index: 0 } : { kind: "block_intro", blockIndex: start.blockIndex, resume: start.trialIndex > 0 },
  );
  const resumeTrialIndex = useRef(start.phase === "main" ? start.trialIndex : 0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const runnerRef = useRef<TrialRunner | null>(null);
  const pauseRequested = useRef(false);
  const [breakLeft, setBreakLeft] = useState(0);

  const practiceGroups = useCallback(() => {
    const groups: { cond: Condition; trials: PlanTrial[] }[] = [];
    for (const t of plan.practice) {
      const last = groups[groups.length - 1];
      if (last && last.cond === t.condition) last.trials.push(t);
      else groups.push({ cond: t.condition, trials: [t] });
    }
    return groups;
  }, [plan.practice]);

  const afterPracticeGroup = (index: number): Step => {
    const groups = practiceGroups();
    return index + 1 < groups.length ? { kind: "practice_cond_intro", cond: groups[index + 1].cond, index: index + 1 } : { kind: "practice_end" };
  };

  const startBlock = (blockIndex: number) => {
    requestFullscreen();
    const block = plan.blocks[blockIndex];
    const from = resumeTrialIndex.current;
    resumeTrialIndex.current = 0;
    onEvent("block_started", `block ${blockIndex + 1} (${block.condition})${from ? ` resumed at trial ${from + 1}` : ""}`);
    const next: Step = blockIndex + 1 < plan.blocks.length ? { kind: "break", nextBlock: blockIndex + 1 } : { kind: "done" };
    setStep({ kind: "running", trials: block.trials.slice(from), practice: false, next });
  };

  // Global key handling for intro screens (Space continues) and Esc (pause request)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        pauseRequested.current = true;
        return;
      }
      if (step.kind === "running") {
        const r = runnerRef.current;
        if (r && r.handleKey(e.key, e.timeStamp, e.repeat)) e.preventDefault();
        if (["f", "j", " "].includes(e.key.toLowerCase())) e.preventDefault();
        return;
      }
      if (e.key === " " && !e.repeat) {
        e.preventDefault();
        if (step.kind === "practice_cond_intro") runGroup(step.index);
        else if (step.kind === "block_intro") startBlock(step.blockIndex);
        else if (step.kind === "break" && breakLeft <= 0) setStep({ kind: "block_intro", blockIndex: step.nextBlock, resume: false });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // Focus-loss detection (window blur, tab hidden) and fullscreen exits
  useEffect(() => {
    const lost = () => runnerRef.current?.markFocusLoss();
    const vis = () => { if (document.hidden) lost(); };
    const fs = () => { if (!document.fullscreenElement) onEvent("fullscreen_exit"); };
    window.addEventListener("blur", lost);
    document.addEventListener("visibilitychange", vis);
    document.addEventListener("fullscreenchange", fs);
    return () => {
      window.removeEventListener("blur", lost);
      document.removeEventListener("visibilitychange", vis);
      document.removeEventListener("fullscreenchange", fs);
    };
  }, [onEvent]);

  const runGroup = (index: number) => {
    requestFullscreen();
    const groups = practiceGroups();
    if (index === 0) onEvent(practiceAttempt.current === 1 ? "practice_started" : "practice_repeated");
    setStep({ kind: "running", trials: groups[index].trials, practice: true, next: afterPracticeGroup(index) });
  };

  // Trial loop
  useEffect(() => {
    if (step.kind !== "running") return;
    let cancelled = false;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const renderer = new CanvasRenderer(canvas, config);
    renderer.clear();
    (async () => {
      for (const trial of step.trials) {
        if (cancelled) return;
        const runner = new TrialRunner(trial, config, renderer, browserClock, {
          practice: step.practice, practiceAttempt: practiceAttempt.current, frameMs: refresh.frameMs, refreshHz: refresh.hz,
        });
        runnerRef.current = runner;
        const result = await runner.run();
        runnerRef.current = null;
        if (cancelled) return;
        queue.enqueue(result);
        if (pauseRequested.current) {
          pauseRequested.current = false;
          onEvent("interrupted", `paused after ${step.practice ? "practice " : ""}trial ${trial.trial_number}`);
          const idx = step.trials.indexOf(trial);
          const rest = step.trials.slice(idx + 1);
          const resumeStep: Step = rest.length ? { ...step, trials: rest } : step.next;
          setStep({ kind: "paused", resumeStep });
          return;
        }
      }
      if (!cancelled) {
        if (step.next.kind === "break") setBreakLeft(config.timing.break_min_s);
        setStep(step.next);
      }
    })();
    return () => {
      cancelled = true;
      runnerRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  // Break countdown
  useEffect(() => {
    if (step.kind !== "break" || breakLeft <= 0) return;
    const t = setTimeout(() => setBreakLeft((x) => x - 1), 1000);
    return () => clearTimeout(t);
  }, [step, breakLeft]);

  useEffect(() => {
    if (step.kind === "done") onFinished();
  }, [step, onFinished]);

  const K = (s: string) => s.toUpperCase();
  const panel = (children: ReactNode) => (
    <div className="flex min-h-full items-center justify-center px-4" style={{ background: config.grid.background_color }}>
      <div className="max-w-2xl rounded-xl bg-white p-8 text-slate-900 shadow">{children}</div>
    </div>
  );

  if (step.kind === "running") {
    return (
      <div className="stage" style={{ background: config.grid.background_color }} data-testid="stage">
        <canvas ref={canvasRef} aria-label="experiment display" />
      </div>
    );
  }
  if (step.kind === "practice_cond_intro") {
    const c = COND_TEXT[step.cond];
    return panel(
      <>
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Practice{practiceAttempt.current > 1 ? ` (attempt ${practiceAttempt.current})` : ""} · {c.name}</p>
        <p className="mt-3 text-lg">{c.body(config)}</p>
        <p className="mt-3">Then decide whether the second blue grid is the same: <Key k={K(config.keys.same)} /> = Same, <Key k={K(config.keys.different)} /> = Different. You will get feedback after each practice trial.</p>
        <p className="mt-6 text-center font-semibold">Press SPACE to start</p>
        <div className="mt-3 text-center"><Button onClick={() => runGroup(step.index)}>Start</Button></div>
      </>,
    );
  }
  if (step.kind === "practice_end") {
    const canRepeat = practiceAttempt.current <= config.trials.max_practice_repeats;
    return panel(
      <>
        <h1 className="text-2xl font-bold">Practice complete</h1>
        <p className="mt-3">The main task has <strong>{plan.blocks.length} blocks of {plan.blocks[0].trials.length} trials</strong>, with a short break between blocks. There is <strong>no feedback</strong> in the main task.</p>
        <p className="mt-2">If anything is unclear, ask the researcher now{canRepeat ? " or repeat the practice" : ""}.</p>
        <div className="mt-6 flex flex-wrap justify-between gap-3">
          {canRepeat ? <Button variant="secondary" onClick={() => { practiceAttempt.current += 1; setStep({ kind: "practice_cond_intro", cond: "A", index: 0 }); }}>Repeat practice</Button> : <span />}
          <Button onClick={() => { onEvent("main_started"); setStep({ kind: "block_intro", blockIndex: 0, resume: false }); }}>Start the main task</Button>
        </div>
      </>,
    );
  }
  if (step.kind === "block_intro") {
    const b = plan.blocks[step.blockIndex];
    const c = COND_TEXT[b.condition];
    return panel(
      <>
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Block {step.blockIndex + 1} of {plan.blocks.length} · {c.name}{step.resume ? " · resuming" : ""}</p>
        <p className="mt-3 text-lg">{c.body(config)}</p>
        <p className="mt-3">Then: <Key k={K(config.keys.same)} /> = Same, <Key k={K(config.keys.different)} /> = Different. Be as fast and accurate as you can.</p>
        <p className="mt-6 text-center font-semibold">Press SPACE to start the block</p>
        <div className="mt-3 text-center"><Button onClick={() => startBlock(step.blockIndex)}>Start block</Button></div>
      </>,
    );
  }
  if (step.kind === "break") {
    return panel(
      <>
        <h1 className="text-2xl font-bold">Short break</h1>
        <p className="mt-3">You have finished block {step.nextBlock} of {plan.blocks.length}. Rest your eyes for a moment.</p>
        {breakLeft > 0 ? <p className="mt-6 text-center text-lg tabular-nums">You can continue in {breakLeft} s</p> : <p className="mt-6 text-center font-semibold">Press SPACE to continue</p>}
        <div className="mt-3 text-center"><Button disabled={breakLeft > 0} onClick={() => setStep({ kind: "block_intro", blockIndex: step.nextBlock, resume: false })}>Continue</Button></div>
      </>,
    );
  }
  if (step.kind === "paused") {
    return panel(
      <>
        <h1 className="text-2xl font-bold">Paused</h1>
        <p className="mt-3">The task is paused. You can continue, or stop taking part. Stopping is your right and has no consequences.</p>
        <div className="mt-6 flex flex-wrap justify-between gap-3">
          <Button variant="danger" onClick={onWithdraw}>Stop and withdraw</Button>
          <Button onClick={() => { onEvent("resumed"); requestFullscreen(); setStep(step.resumeStep); }}>Continue the task</Button>
        </div>
      </>,
    );
  }
  return panel(<p>Saving…{pilot ? " (pilot)" : ""}</p>);
}
