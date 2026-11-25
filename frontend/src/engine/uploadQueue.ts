/**
 * Reliable trial upload: every trial is persisted to localStorage BEFORE it is sent, and removed
 * only after the server confirms it (or reports it as a duplicate). If the network or server fails,
 * trials stay queued and are retried; if the browser is closed, they are retried on resume.
 */
import type { TrialResult } from "../types";

export interface KV {
  getItem(k: string): string | null;
  setItem(k: string, v: string): void;
  removeItem(k: string): void;
}

export type Sender = (trials: TrialResult[]) => Promise<{ saved: number[]; duplicates: number[] }>;

export function trialKey(t: Pick<TrialResult, "practice_trial" | "practice_attempt" | "trial_number">): string {
  return `${t.practice_trial ? "P" : "M"}${t.practice_attempt}-${t.trial_number}`;
}

export class UploadQueue {
  private key: string;
  private sending = false;
  private retryTimer: ReturnType<typeof setTimeout> | null = null;
  public lastError: string | null = null;
  public onChange?: () => void;

  constructor(sessionId: string, private send: Sender, private store: KV, private retryMs = 2000) {
    this.key = `smit_queue_${sessionId}`;
  }

  pending(): TrialResult[] {
    try {
      return JSON.parse(this.store.getItem(this.key) || "[]");
    } catch {
      return [];
    }
  }

  private write(items: TrialResult[]): void {
    try {
      if (items.length) this.store.setItem(this.key, JSON.stringify(items));
      else this.store.removeItem(this.key);
    } catch {
      /* storage full or unavailable: items stay in memory only via retry */
    }
    this.onChange?.();
  }

  enqueue(t: TrialResult): void {
    const items = this.pending().filter((x) => trialKey(x) !== trialKey(t));
    items.push(t);
    this.write(items);
    void this.flush();
  }

  /** Try to send everything pending. Resolves true when the queue is empty. */
  async flush(): Promise<boolean> {
    if (this.sending) return this.pending().length === 0;
    const items = this.pending();
    if (!items.length) return true;
    this.sending = true;
    // Send one homogeneous group (practice attempt n, or main trials) at a time so that the
    // server's confirmation by trial_number is unambiguous.
    const g = items[0];
    const batch = items.filter((x) => x.practice_trial === g.practice_trial && x.practice_attempt === g.practice_attempt).slice(0, 50);
    try {
      const res = await this.send(batch);
      const done = new Set([...res.saved, ...res.duplicates]);
      const sent = batch.filter((x) => done.has(x.trial_number)).map(trialKey);
      const remaining = this.pending().filter((x) => !sent.includes(trialKey(x)));
      this.lastError = null;
      this.write(remaining);
      this.sending = false;
      if (remaining.length) return this.flush();
      return true;
    } catch (e) {
      this.lastError = e instanceof Error ? e.message : String(e);
      this.sending = false;
      this.onChange?.();
      if (!this.retryTimer) {
        this.retryTimer = setTimeout(() => {
          this.retryTimer = null;
          void this.flush();
        }, this.retryMs);
      }
      return false;
    }
  }

  dispose(): void {
    if (this.retryTimer) clearTimeout(this.retryTimer);
  }
}

export const memoryStore = (): KV & { data: Map<string, string> } => {
  const data = new Map<string, string>();
  return {
    data,
    getItem: (k) => data.get(k) ?? null,
    setItem: (k, v) => void data.set(k, v),
    removeItem: (k) => void data.delete(k),
  };
};

export function safeLocalStorage(): KV {
  try {
    const t = "__smit_test__";
    localStorage.setItem(t, "1");
    localStorage.removeItem(t);
    return localStorage;
  } catch {
    return memoryStore();
  }
}
