/**
 * Pre-test device check: the task may only run on a Mac in Google Chrome with no power saving throttling
 * the display.
 *
 * Browsers cannot read macOS Low Power Mode or Chrome's Energy Saver directly, so the check uses what they
 * cause: macOS Low Power Mode caps a ProMotion MacBook Pro display at 60 Hz, and Chrome's Energy Saver caps
 * frames at 30 Hz. The charging state is recorded for reference only; it never blocks the test.
 */
import { estimateRefreshRate } from "../engine/clock";

export interface DeviceFacts {
  userAgent: string;
  uaPlatform: string | null; // navigator.userAgentData.platform (Chromium only)
  uaBrands: string[]; // navigator.userAgentData.brands
  maxTouchPoints: number;
  screenWidth: number;
  screenHeight: number;
  devicePixelRatio: number;
  batteryApi: boolean;
  charging: boolean | null;
  batteryLevel: number | null;
  refreshHz: number | null;
  windowFocused: boolean;
}

export type CheckId = "mac" | "chrome" | "display";

export interface CheckItem {
  id: CheckId;
  label: string;
  ok: boolean;
  detail: string;
  fix?: string;
}

export interface DeviceCheckResult {
  ok: boolean;
  items: CheckItem[];
  proMotion: boolean;
  facts: DeviceFacts;
}

/** Below this the display is being throttled (background window, Chrome Energy Saver, power saving). */
export const MIN_REFRESH_HZ = 50;
/** A ProMotion (120 Hz) MacBook Pro measured below this is in macOS Low Power Mode (capped at 60 Hz). */
export const MIN_PROMOTION_HZ = 100;

/** "Looks like" screen sizes (points) of 14-inch and 16-inch ProMotion MacBook Pro built-in displays. */
const PROMOTION_SIZES = new Set([
  "1512x982", "1352x878", "1800x1169", "1147x745", // 14-inch
  "1728x1117", "1496x967", "2056x1329", "1312x848", // 16-inch
]);

export function isProMotionMacBookPro(f: Pick<DeviceFacts, "screenWidth" | "screenHeight" | "devicePixelRatio">): boolean {
  return f.devicePixelRatio >= 2 && PROMOTION_SIZES.has(`${f.screenWidth}x${f.screenHeight}`);
}

export function evaluateDevice(f: DeviceFacts): DeviceCheckResult {
  const items: CheckItem[] = [];

  const macOS = f.uaPlatform ? f.uaPlatform === "macOS" : /Macintosh|Mac OS X/.test(f.userAgent);
  const iPad = /Macintosh/.test(f.userAgent) && f.maxTouchPoints > 1; // iPadOS reports itself as a Mac
  const mac = macOS && !iPad;
  items.push({
    id: "mac", label: "MacBook (macOS)", ok: mac,
    detail: mac ? "macOS detected." : iPad ? "This looks like an iPad." : "This computer is not a Mac.",
    fix: "Please use one of the study MacBooks.",
  });

  const brands = f.uaBrands.map((b) => b.toLowerCase());
  const chrome = brands.length ? brands.some((b) => b === "google chrome") : /Chrome\//.test(f.userAgent) && !/Edg\/|OPR\/|Brave/.test(f.userAgent);
  items.push({
    id: "chrome", label: "Google Chrome", ok: chrome,
    detail: chrome ? "Google Chrome detected." : "This is not Google Chrome.",
    fix: "Open this link in Google Chrome.",
  });

  const proMotion = isProMotionMacBookPro(f);
  const minHz = proMotion ? MIN_PROMOTION_HZ : MIN_REFRESH_HZ;
  const hz = f.refreshHz;
  const displayOk = hz !== null && f.windowFocused && hz >= minHz;
  let detail: string;
  if (hz === null) detail = "Display speed could not be measured.";
  else if (!f.windowFocused) detail = `Measured about ${hz} Hz, but this window was not in front.`;
  else if (displayOk) detail = `About ${hz} Hz — full speed.`;
  else if (proMotion && hz >= MIN_REFRESH_HZ) detail = `Only about ${hz} Hz (this MacBook Pro normally runs at 120 Hz) — Low Power Mode is probably on.`;
  else detail = `Only about ${hz} Hz — power saving (Low Power Mode or Chrome Energy Saver) or a background window is slowing the display.`;
  items.push({
    id: "display", label: "Power saving off (display at full speed)", ok: displayOk, detail,
    fix: "Turn off Low Power Mode (System Settings → Battery → Low Power Mode: Never) and Chrome Energy Saver "
      + "(Chrome menu → Settings → Performance → Energy Saver: off), keep this window in front, then press Check again.",
  });

  return { ok: items.every((i) => i.ok), items, proMotion, facts: f };
}

interface BatteryLike { charging: boolean; level: number }
type NavigatorExtras = Navigator & {
  userAgentData?: { platform?: string; brands?: { brand: string }[] };
  getBattery?: () => Promise<BatteryLike>;
};

/** Collect the facts in the browser (measures the refresh rate for ~0.75 s). */
export async function collectDeviceFacts(): Promise<DeviceFacts> {
  const nav = navigator as NavigatorExtras;
  let charging: boolean | null = null;
  let level: number | null = null;
  const batteryApi = typeof nav.getBattery === "function";
  if (batteryApi) {
    try {
      const b = await nav.getBattery!();
      charging = b.charging;
      level = b.level;
    } catch {
      charging = null;
    }
  }
  const focusedBefore = document.hasFocus() && !document.hidden;
  const r = await estimateRefreshRate();
  const focusedAfter = document.hasFocus() && !document.hidden;
  return {
    userAgent: navigator.userAgent,
    uaPlatform: nav.userAgentData?.platform ?? null,
    uaBrands: nav.userAgentData?.brands?.map((b) => b.brand) ?? [],
    maxTouchPoints: navigator.maxTouchPoints ?? 0,
    screenWidth: window.screen.width,
    screenHeight: window.screen.height,
    devicePixelRatio: window.devicePixelRatio,
    batteryApi,
    charging,
    batteryLevel: level,
    refreshHz: r.hz,
    windowFocused: focusedBefore && focusedAfter,
  };
}

export async function runDeviceCheck(): Promise<DeviceCheckResult> {
  return evaluateDevice(await collectDeviceFacts());
}

/** Short machine-readable summary stored with the session. */
export function summariseCheck(r: DeviceCheckResult): string {
  return r.items.map((i) => `${i.id}:${i.ok ? "ok" : "fail"}`).join(" ") + (r.proMotion ? " promotion" : "");
}
