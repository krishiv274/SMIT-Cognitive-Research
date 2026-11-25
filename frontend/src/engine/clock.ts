/**
 * Frame clock abstraction. In the browser this wraps requestAnimationFrame and
 * performance.now(); in unit tests a FakeClock simulates a display with a fixed
 * refresh rate so phase timing can be verified deterministically.
 */
export interface FrameClock {
  now(): number;
  requestFrame(cb: (timestamp: number) => void): number;
  cancelFrame(id: number): void;
}

export const browserClock: FrameClock = {
  now: () => performance.now(),
  requestFrame: (cb) => requestAnimationFrame(cb),
  cancelFrame: (id) => cancelAnimationFrame(id),
};

/** Deterministic clock for tests: frames occur every `frameMs`, optionally with injected delays. */
export class FakeClock implements FrameClock {
  private t = 0;
  private nextId = 1;
  private queue = new Map<number, (ts: number) => void>();
  /** extra delay (ms) to add before specific frame numbers (simulates dropped frames) */
  public frameDelays = new Map<number, number>();
  public frameCount = 0;

  constructor(public frameMs = 1000 / 60) {}

  now(): number {
    return this.t;
  }

  requestFrame(cb: (ts: number) => void): number {
    const id = this.nextId++;
    this.queue.set(id, cb);
    return id;
  }

  cancelFrame(id: number): void {
    this.queue.delete(id);
  }

  /** Advance one display frame and run all callbacks registered before it. */
  tick(): void {
    this.frameCount += 1;
    this.t += this.frameMs + (this.frameDelays.get(this.frameCount) ?? 0);
    const cbs = [...this.queue.values()];
    this.queue.clear();
    for (const cb of cbs) cb(this.t);
  }

  /** Advance until `ms` of simulated time have elapsed (or callbacks run out). */
  advance(ms: number): void {
    const end = this.t + ms;
    while (this.t + this.frameMs <= end + 1e-9) this.tick();
  }

  get pending(): number {
    return this.queue.size;
  }
}

/**
 * Estimate the display refresh rate from requestAnimationFrame intervals.
 * Returns the median interval-based rate, snapped to a common nominal rate when within 3 %.
 */
export function estimateRefreshRate(clock: FrameClock = browserClock, frames = 90): Promise<{ hz: number; frameMs: number; intervals: number[] }> {
  return new Promise((resolve) => {
    const stamps: number[] = [];
    const step = (ts: number) => {
      stamps.push(ts);
      if (stamps.length <= frames) clock.requestFrame(step);
      else {
        const intervals = stamps.slice(1).map((s, i) => s - stamps[i]);
        const hz = snapRefreshRate(1000 / median(intervals));
        resolve({ hz, frameMs: 1000 / hz, intervals });
      }
    };
    clock.requestFrame(step);
  });
}

export const NOMINAL_RATES = [30, 50, 60, 72, 75, 90, 100, 120, 144, 165, 170, 180, 240, 360];

export function snapRefreshRate(hz: number): number {
  for (const r of NOMINAL_RATES) if (Math.abs(hz - r) / r < 0.03) return r;
  return Math.round(hz * 10) / 10;
}

export function median(xs: number[]): number {
  if (!xs.length) return NaN;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** Number of whole frames closest to a planned duration (lecture: durations are integer multiples of a frame). */
export function framesFor(plannedMs: number, frameMs: number): number {
  return Math.max(1, Math.round(plannedMs / frameMs));
}
