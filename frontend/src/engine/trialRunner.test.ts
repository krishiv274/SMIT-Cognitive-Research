import { describe, expect, it } from "vitest";
import { FakeClock, framesFor, median, snapRefreshRate } from "./clock";
import { RecordingRenderer } from "./renderer";
import { TrialRunner } from "./trialRunner";
import type { ExperimentConfig, PlanTrial, TrialResult } from "../types";
import defaultConfig from "../../../experiment/configuration/default_config.json";

const cfg = defaultConfig as unknown as ExperimentConfig;

function makeTrial(over: Partial<PlanTrial> = {}): PlanTrial {
  return {
    trial_number: 1, block_number: 1, condition: "B", practice: false,
    original_pattern: [0, 2, 4, 6], recognition_pattern: [0, 2, 4, 6], trial_type: "same", correct_answer: "same",
    interference_type: "numerical", interference: { text: "7 + 6 = 13", correct: "true" },
    planned_iti_ms: 1000, planned_fixation_ms: 500, planned_memory_stimulus_ms: 500, planned_post_stimulus_blank_ms: 0,
    planned_interference_ms: 3000, planned_retention_ms: 1000, planned_recognition_deadline_ms: 2000,
    ...over,
  };
}

/** Run a trial on a simulated display; `script` is called every frame to inject key presses. */
async function simulate(trial: PlanTrial, hz = 60, script?: (r: TrialRunner, clock: FakeClock) => void,
                        practice = false, delays?: Map<number, number>): Promise<{ res: TrialResult; renderer: RecordingRenderer }> {
  const clock = new FakeClock(1000 / hz);
  if (delays) clock.frameDelays = delays;
  const renderer = new RecordingRenderer();
  const runner = new TrialRunner(trial, cfg, renderer, clock, { practice, frameMs: 1000 / hz, refreshHz: hz });
  let done: TrialResult | null = null;
  runner.run().then((r) => { done = r; });
  for (let i = 0; i < 2000 && !done; i++) {
    script?.(runner, clock);
    clock.tick();
    await Promise.resolve();
  }
  await Promise.resolve();
  if (!done) throw new Error("trial did not finish");
  return { res: done, renderer };
}

describe("clock helpers", () => {
  it("snaps refresh rates and converts durations to frames", () => {
    expect(snapRefreshRate(59.7)).toBe(60);
    expect(snapRefreshRate(143.2)).toBe(144);
    expect(snapRefreshRate(83)).toBe(83);
    expect(framesFor(500, 1000 / 60)).toBe(30);
    expect(framesFor(20, 1000 / 60)).toBe(1); // lecture example: 20 ms → 16.67 ms on a 60 Hz display
    expect(median([3, 1, 2])).toBe(2);
  });
});

describe("phase timing (planned vs measured)", () => {
  for (const hz of [60, 120, 144]) {
    it(`matches planned durations to within one frame at ${hz} Hz`, async () => {
      const { res } = await simulate(makeTrial(), hz, (r, c) => {
        if (r.currentPhase === "probe" && c.now() > 6000 && res0.length === 0) { r.handleKey("f", c.now() + 1); res0.push(1); }
      });
      const F = 1000 / hz;
      expect(Math.abs((res.actual_fixation_duration_ms ?? 0) - 500)).toBeLessThanOrEqual(F / 2 + 0.1);
      expect(Math.abs((res.measured_stimulus_duration_ms ?? 0) - 500)).toBeLessThanOrEqual(F / 2 + 0.1);
      expect(Math.abs((res.measured_interference_duration_ms ?? 0) - 3000)).toBeLessThanOrEqual(F / 2 + 0.1);
      expect(Math.abs((res.measured_retention_duration_ms ?? 0) - 1000)).toBeLessThanOrEqual(F / 2 + 0.1);
      expect(res.dropped_frames).toBe(0);
      res0.length = 0;
    });
  }
  const res0: number[] = [];

  it("rounds 500 ms at 75 Hz to the nearest whole frame (37 or 38 frames)", async () => {
    const { res } = await simulate(makeTrial(), 75);
    const frames = (res.measured_stimulus_duration_ms ?? 0) / (1000 / 75);
    expect(Math.abs(frames - Math.round(frames))).toBeLessThan(0.01);
    expect([37, 38]).toContain(Math.round(frames));
  });

  it("detects dropped frames and the resulting timing deviation", async () => {
    // A stall in the middle of a phase is absorbed (the phase still ends on time) ...
    const mid = await simulate(makeTrial(), 60, undefined, false, new Map([[40, 100]]));
    expect(mid.res.dropped_frames).toBeGreaterThan(0);
    expect(Math.abs((mid.res.measured_stimulus_duration_ms ?? 0) - 500)).toBeLessThan(9);
    // ... but a stall exactly when the memory grid should disappear (frame 62) lengthens it and is measured.
    const end = await simulate(makeTrial(), 60, undefined, false, new Map([[62, 100]]));
    expect(end.res.dropped_frames).toBeGreaterThan(0);
    expect((end.res.measured_stimulus_duration_ms ?? 0) - 500).toBeGreaterThan(50);
  });
});

describe("response handling", () => {
  it("records a correct same response with RT from probe onset", async () => {
    let probeOnsetSeen: number | null = null;
    const { res } = await simulate(makeTrial(), 60, (r, c) => {
      if (r.currentPhase === "probe") {
        if (probeOnsetSeen === null) probeOnsetSeen = c.now();
        else if (c.now() - probeOnsetSeen > 400 && res1.length === 0) { r.handleKey("f", c.now() + 3); res1.push(1); }
      }
    });
    expect(res.participant_response).toBe("same");
    expect(res.response_timeout).toBe(false);
    expect(res.reaction_time_ms).toBeGreaterThan(380);
    expect(res.reaction_time_ms).toBeLessThan(460);
  });
  const res1: number[] = [];

  it("ignores duplicate and auto-repeat key presses after the first response", async () => {
    let pressed = 0;
    const { res } = await simulate(makeTrial(), 60, (r, c) => {
      if (r.currentPhase === "probe" && pressed < 3) {
        pressed += 1;
        if (pressed === 1) return; // wait for onset frame
        r.handleKey(pressed === 2 ? "j" : "f", c.now() + 1, pressed === 3);
      }
    });
    expect(res.participant_response).toBe("different");
  });

  it("times out when no response is given within the deadline", async () => {
    const { res } = await simulate(makeTrial(), 60);
    expect(res.response_timeout).toBe(true);
    expect(res.participant_response).toBeNull();
    expect(res.reaction_time_ms).toBeNull();
    expect(res.interference_response).toBeNull();
  });

  it("rejects responses after the response window", async () => {
    let onset: number | null = null;
    const { res } = await simulate(makeTrial(), 60, (r, c) => {
      if (r.currentPhase === "probe") {
        if (onset === null) onset = c.now();
        else r.handleKey("f", onset + 2100);
      }
    });
    expect(res.response_timeout).toBe(true);
  });

  it("counts premature key presses during fixation/memory/retention and ignores them", async () => {
    const { res } = await simulate(makeTrial({ condition: "A", interference: null, interference_type: "none" }), 60, (r, c) => {
      if (["fixation", "memory", "retention"].includes(r.currentPhase) && c.frameCount % 20 === 0) r.handleKey("j", c.now());
    });
    expect(res.premature_keypresses).toBeGreaterThan(0);
    expect(res.participant_response).toBeNull();
  });

  it("records the secondary-task response and RT and keeps the interference phase length fixed", async () => {
    let onset: number | null = null;
    let answered = false;
    const { res, renderer } = await simulate(makeTrial(), 60, (r, c) => {
      if (r.currentPhase === "interference") {
        if (onset === null) onset = c.now();
        else if (!answered && c.now() - onset > 900) { r.handleKey("f", c.now()); answered = true; }
      }
    });
    expect(res.interference_response).toBe("true");
    expect(res.interference_reaction_time_ms).toBeGreaterThan(880);
    expect(Math.abs((res.measured_interference_duration_ms ?? 0) - 3000)).toBeLessThan(9);
    expect(renderer.log).toContain("equation:7 + 6 = 13");
  });

  it("ignores non-response keys", async () => {
    const r = new TrialRunner(makeTrial(), cfg, new RecordingRenderer(), new FakeClock(), { practice: false, frameMs: 16.67, refreshHz: 60 });
    expect(r.handleKey("x", 10)).toBe(false);
  });
});

describe("focus loss and practice feedback", () => {
  it("flags focus loss", async () => {
    const { res } = await simulate(makeTrial(), 60, (r, c) => { if (c.frameCount === 50) r.markFocusLoss(); });
    expect(res.focus_loss).toBe(true);
  });

  it("shows feedback only on practice trials", async () => {
    const p = await simulate(makeTrial({ practice: true }), 60, undefined, true);
    expect(p.renderer.log.some((l) => l.startsWith("feedback:Too slow"))).toBe(true);
    expect(p.res.practice_trial).toBe(true);
    const m = await simulate(makeTrial(), 60);
    expect(m.renderer.log.some((l) => l.startsWith("feedback"))).toBe(false);
  });

  it("draws the visual distractor in the distractor colour, not the memory colour", async () => {
    const t = makeTrial({ condition: "C", interference_type: "visual", interference: { text: "1-3-5-7", correct: "true", pattern: [1, 3, 5, 7], question: "symmetry" } });
    const { renderer } = await simulate(t, 60);
    expect(renderer.log).toContain(`grid:1-3-5-7:${cfg.grid.visual_interference_highlight_color}`);
    expect(renderer.log).toContain(`grid:0-2-4-6:${cfg.grid.memory_highlight_color}`);
  });
});
