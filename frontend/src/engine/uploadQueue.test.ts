import { describe, expect, it, vi } from "vitest";
import { UploadQueue, memoryStore } from "./uploadQueue";
import type { TrialResult } from "../types";

const trial = (n: number, practice = false): TrialResult => ({
  trial_number: n, practice_trial: practice, practice_attempt: practice ? 1 : 0, participant_response: "same",
  reaction_time_ms: 600, response_timeout: false, premature_keypresses: 0, interference_response: null,
  interference_reaction_time_ms: null, actual_fixation_duration_ms: 500, measured_stimulus_duration_ms: 500,
  measured_post_stimulus_blank_ms: null, measured_interference_duration_ms: 3000, measured_retention_duration_ms: 1000,
  inter_trial_interval_ms: 1000, refresh_rate_hz: 60, dropped_frames: 0, focus_loss: false, event_timestamps: {},
});

describe("UploadQueue", () => {
  it("removes trials only after the server confirms them", async () => {
    const store = memoryStore();
    const send = vi.fn(async (ts: TrialResult[]) => ({ saved: ts.map((t) => t.trial_number), duplicates: [] }));
    const q = new UploadQueue("s1", send, store);
    q.enqueue(trial(1));
    await q.flush();
    expect(q.pending()).toHaveLength(0);
    expect(send).toHaveBeenCalled();
  });

  it("keeps trials queued when the network fails and retries later", async () => {
    vi.useFakeTimers();
    const store = memoryStore();
    let fail = true;
    const send = vi.fn(async (ts: TrialResult[]) => {
      if (fail) throw new Error("offline");
      return { saved: ts.map((t) => t.trial_number), duplicates: [] };
    });
    const q = new UploadQueue("s2", send, store, 1000);
    q.enqueue(trial(1));
    q.enqueue(trial(2));
    await vi.runOnlyPendingTimersAsync();
    expect(q.pending().length).toBe(2);
    expect(q.lastError).toBe("offline");
    // survives a "page reload": a new queue over the same storage sees the pending trials
    const q2 = new UploadQueue("s2", send, store, 1000);
    expect(q2.pending().map((t) => t.trial_number)).toEqual([1, 2]);
    fail = false;
    await q2.flush();
    expect(q2.pending()).toHaveLength(0);
    q.dispose();
    vi.useRealTimers();
  });

  it("treats server-reported duplicates as delivered (no double counting)", async () => {
    const store = memoryStore();
    const send = vi.fn(async (ts: TrialResult[]) => ({ saved: [], duplicates: ts.map((t) => t.trial_number) }));
    const q = new UploadQueue("s3", send, store);
    q.enqueue(trial(5));
    await q.flush();
    expect(q.pending()).toHaveLength(0);
  });

  it("does not duplicate a trial enqueued twice", () => {
    const store = memoryStore();
    const q = new UploadQueue("s4", async () => { throw new Error("x"); }, store, 100000);
    q.enqueue(trial(3));
    q.enqueue(trial(3));
    expect(q.pending()).toHaveLength(1);
    q.dispose();
  });
});
