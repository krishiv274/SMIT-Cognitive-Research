/**
 * SMIT trial engine — runs ONE trial as a frame-synchronised state machine.
 *
 * Timing model
 *  - Every screen change is drawn inside a requestAnimationFrame callback. The change becomes
 *    visible at the next display refresh, so the ONSET of a phase is taken as the timestamp of the
 *    next animation-frame callback after drawing.
 *  - A phase with planned duration D is replaced in the callback whose *next* frame is closest to
 *    onset + D, so phases last a whole number of frames (lecture slide 26: durations are integer
 *    multiples of the frame duration). Measured duration = onset(next phase) − onset(phase).
 *  - Reaction times use KeyboardEvent.timeStamp, which is on the same high-resolution clock as the
 *    frame timestamps (performance.now()), never Date.now().
 *
 * Response handling
 *  - Auto-repeat key events are ignored.
 *  - Only the FIRST valid key inside a response window is accepted (recognition probe window and
 *    secondary-task window); later presses are ignored.
 *  - F/J presses outside any response window are counted as premature key presses and ignored.
 *  - Recognition responses after the deadline are ignored (trial = timeout).
 */
import type { Answer, ExperimentConfig, PlanTrial, TF, TrialResult } from "../types";
import type { FrameClock } from "./clock";
import type { Renderer } from "./renderer";

type PhaseName = "fixation" | "memory" | "blank" | "interference" | "retention" | "probe" | "feedback" | "iti";

interface Phase {
  name: PhaseName;
  planned: number;
}

export interface TrialRunnerOptions {
  practice: boolean;
  practiceAttempt?: number;
  frameMs: number;
  refreshHz: number;
  /** Optional observer (e.g. sets a data attribute for automated tests). Must be cheap. */
  onPhase?: (phase: string) => void;
  /** Returns false when the experiment window does not have keyboard focus (checked every frame). A window
   *  that never had focus fires no blur event, so focus must be polled rather than only listened for. */
  isFocused?: () => boolean;
}

export function buildPhases(trial: PlanTrial, cfg: ExperimentConfig, practice: boolean): Phase[] {
  const phases: Phase[] = [
    { name: "fixation", planned: trial.planned_fixation_ms },
    { name: "memory", planned: trial.planned_memory_stimulus_ms },
  ];
  if (trial.planned_post_stimulus_blank_ms > 0) phases.push({ name: "blank", planned: trial.planned_post_stimulus_blank_ms });
  phases.push({ name: "interference", planned: trial.planned_interference_ms });
  if (trial.planned_retention_ms > 0) phases.push({ name: "retention", planned: trial.planned_retention_ms });
  phases.push({ name: "probe", planned: trial.planned_recognition_deadline_ms });
  if (practice) phases.push({ name: "feedback", planned: cfg.timing.practice_feedback_ms });
  phases.push({ name: "iti", planned: trial.planned_iti_ms });
  return phases;
}

export class TrialRunner {
  private phases: Phase[];
  private idx = 0;
  private drawn = false;
  private awaitingOnset = false;
  private onsets: Partial<Record<PhaseName, number>> = {};
  private lastTs: number | null = null;
  private frameId: number | null = null;
  private resolve!: (r: TrialResult) => void;
  private finished = false;
  private trialStart: number | null = null;

  // responses
  private response: Answer | null = null;
  private rt: number | null = null;
  private secondaryResponse: TF | null = null;
  private secondaryRt: number | null = null;
  private secondaryCleared = false;
  private premature = 0;
  private droppedFrames = 0;
  private focusLoss = false;
  private itiMeasured: number | null = null;

  constructor(
    private trial: PlanTrial,
    private cfg: ExperimentConfig,
    private renderer: Renderer,
    private clock: FrameClock,
    private opts: TrialRunnerOptions,
  ) {
    this.phases = buildPhases(trial, cfg, opts.practice);
  }

  /** Run the trial; resolves after the inter-trial interval. */
  run(): Promise<TrialResult> {
    return new Promise((resolve) => {
      this.resolve = resolve;
      this.frameId = this.clock.requestFrame(this.onFrame);
    });
  }

  get currentPhase(): PhaseName {
    return this.phases[Math.min(this.idx, this.phases.length - 1)].name;
  }

  markFocusLoss(): void {
    if (!this.finished) this.focusLoss = true;
  }

  abort(): void {
    if (this.frameId !== null) this.clock.cancelFrame(this.frameId);
    this.finished = true;
  }

  /** Feed a keydown event (key already lower-cased). Returns true if it was consumed as a response. */
  handleKey(key: string, timeStamp: number, repeat = false): boolean {
    if (this.finished || repeat) return false;
    const k = key.toLowerCase();
    const keys = this.cfg.keys;
    const isRespKey = k === keys.same || k === keys.different || k === keys.secondary_true || k === keys.secondary_false;
    if (!isRespKey) return false;
    const phase = this.currentPhase;
    const onset = this.onsets[phase];
    const onsetKnown = onset !== undefined && !this.awaitingOnset;

    if (phase === "interference" && this.trial.interference) {
      if (!onsetKnown || this.secondaryResponse !== null) {
        if (!onsetKnown) this.premature += 1;
        return false;
      }
      const t = timeStamp - (onset as number);
      if (t < 0) { this.premature += 1; return false; }
      if (k === keys.secondary_true) this.secondaryResponse = "true";
      else if (k === keys.secondary_false) this.secondaryResponse = "false";
      else return false;
      this.secondaryRt = t;
      return true;
    }
    if (phase === "probe") {
      if (!onsetKnown) { this.premature += 1; return false; }
      if (this.response !== null) return false; // duplicate key press — ignored
      const t = timeStamp - (onset as number);
      if (t < 0) { this.premature += 1; return false; }
      if (t > this.trial.planned_recognition_deadline_ms) return false; // outside response window
      if (k === keys.same) this.response = "same";
      else if (k === keys.different) this.response = "different";
      else return false;
      this.rt = t;
      return true;
    }
    if (phase === "feedback" || phase === "iti") return false; // after the response window: ignore silently
    this.premature += 1;
    return false;
  }

  private draw(phase: Phase): void {
    this.opts.onPhase?.(phase.name);
    const r = this.renderer;
    const g = this.cfg.grid;
    const keys = this.cfg.keys;
    const K = (s: string) => s.toUpperCase();
    switch (phase.name) {
      case "fixation":
        r.fixation();
        break;
      case "memory":
        r.grid(this.trial.original_pattern, g.memory_highlight_color);
        break;
      case "blank":
      case "retention":
        r.dot();
        break;
      case "interference": {
        const s = this.trial.interference;
        const cap = `${K(keys.secondary_true)} = ${this.trial.condition === "B" ? "True" : "Yes"}      ${K(keys.secondary_false)} = ${this.trial.condition === "B" ? "False" : "No"}`;
        if (!s) r.dot();
        else if (this.trial.condition === "B") r.equation(s.text, "Is the equation correct?", cap);
        else r.grid(s.pattern ?? [], g.visual_interference_highlight_color, cap,
          s.question === "centre" ? "Is the centre square filled?" : "Is the orange pattern symmetrical (left ↔ right)?");
        break;
      }
      case "probe":
        r.grid(this.trial.recognition_pattern, g.memory_highlight_color, `${K(keys.same)} = Same      ${K(keys.different)} = Different`);
        break;
      case "feedback":
        r.feedback(this.feedbackLines());
        break;
      case "iti":
        r.clear();
        break;
    }
  }

  private feedbackLines(): { text: string; color: string }[] {
    const lines: { text: string; color: string }[] = [];
    if (this.response === null) lines.push({ text: "Too slow", color: "#7a3d00" });
    else if (this.response === this.trial.correct_answer) lines.push({ text: "Correct", color: "#0b5d1e" });
    else lines.push({ text: "Incorrect", color: "#8b0000" });
    lines.push({ text: `The pattern was ${this.trial.correct_answer === "same" ? "the SAME" : "DIFFERENT (one square moved)"}.`, color: "#000000" });
    const s = this.trial.interference;
    if (s) {
      const task = this.trial.condition === "B" ? "Equation" : this.cfg.secondary_tasks.visual.probe === "symmetry" ? "Symmetry" : "Centre square";
      if (this.secondaryResponse === null) lines.push({ text: `${task}: no answer — please answer during the middle phase.`, color: "#7a3d00" });
      else lines.push({ text: `${task}: ${this.secondaryResponse === s.correct ? "correct" : "incorrect"}`, color: "#000000" });
    }
    return lines;
  }

  private onFrame = (ts: number): void => {
    if (this.finished) return;
    const F = this.opts.frameMs;
    if (this.lastTs !== null) {
      const interval = ts - this.lastTs;
      if (interval > 1.5 * F) this.droppedFrames += Math.max(1, Math.round(interval / F) - 1);
    }
    this.lastTs = ts;
    if (this.trialStart === null) this.trialStart = ts;
    if (!this.focusLoss && this.opts.isFocused && !this.opts.isFocused()) this.focusLoss = true;

    if (this.awaitingOnset) {
      this.onsets[this.phases[this.idx].name] = ts;
      this.awaitingOnset = false;
    }
    const phase = this.phases[this.idx];
    if (!this.drawn) {
      this.draw(phase);
      this.drawn = true;
      this.awaitingOnset = true;
      this.frameId = this.clock.requestFrame(this.onFrame);
      return;
    }
    const onset = this.onsets[phase.name] as number;
    const elapsed = ts - onset;
    // would the NEXT frame be at or past the planned end (within half a frame)?
    const due = elapsed + F >= phase.planned - F / 2;
    let advance = false;

    if (phase.name === "probe") {
      if (this.response !== null) advance = true;
      else if (elapsed >= phase.planned) advance = true; // deadline passed, timeout
    } else if (phase.name === "interference") {
      if (this.secondaryResponse !== null && !this.secondaryCleared && !due) {
        this.renderer.dot(); // remove secondary stimulus after the answer; phase length unchanged
        this.secondaryCleared = true;
      }
      advance = due;
    } else {
      advance = due;
    }

    if (advance) {
      if (phase.name === "iti") {
        this.itiMeasured = ts + F - onset;
        this.finish();
        return;
      }
      this.idx += 1;
      this.draw(this.phases[this.idx]);
      this.awaitingOnset = true;
    }
    this.frameId = this.clock.requestFrame(this.onFrame);
  };

  private dur(a: PhaseName, b: PhaseName): number | null {
    const x = this.onsets[a], y = this.onsets[b];
    return x === undefined || y === undefined ? null : round1(y - x);
  }

  private nextAfter(name: PhaseName): PhaseName {
    const i = this.phases.findIndex((p) => p.name === name);
    return this.phases[i + 1].name;
  }

  private finish(): void {
    this.finished = true;
    const has = (n: PhaseName) => this.phases.some((p) => p.name === n);
    const timeout = this.response === null;
    const stamps: Record<string, number> = {};
    for (const [k, v] of Object.entries(this.onsets)) stamps[`${k}_onset`] = round1((v as number) - (this.trialStart ?? 0));
    if (this.rt !== null) stamps.response_after_probe = round1(this.rt);
    if (this.secondaryRt !== null) stamps.secondary_response_after_onset = round1(this.secondaryRt);
    this.resolve({
      trial_number: this.trial.trial_number,
      practice_trial: this.opts.practice,
      practice_attempt: this.opts.practice ? (this.opts.practiceAttempt ?? 1) : 0,
      participant_response: this.response,
      reaction_time_ms: this.rt === null ? null : round1(this.rt),
      response_timeout: timeout,
      premature_keypresses: this.premature,
      interference_response: this.trial.interference ? this.secondaryResponse : null,
      interference_reaction_time_ms: this.secondaryRt === null ? null : round1(this.secondaryRt),
      actual_fixation_duration_ms: this.dur("fixation", "memory"),
      measured_stimulus_duration_ms: this.dur("memory", this.nextAfter("memory")),
      measured_post_stimulus_blank_ms: has("blank") ? this.dur("blank", "interference") : null,
      measured_interference_duration_ms: this.dur("interference", this.nextAfter("interference")),
      measured_retention_duration_ms: has("retention") ? this.dur("retention", "probe") : null,
      inter_trial_interval_ms: this.itiMeasured === null ? null : round1(this.itiMeasured),
      refresh_rate_hz: this.opts.refreshHz,
      dropped_frames: this.droppedFrames,
      focus_loss: this.focusLoss,
      event_timestamps: stamps,
    });
  }
}

function round1(x: number): number {
  return Math.round(x * 10) / 10;
}
