import { describe, expect, it } from "vitest";
import { evaluateDevice, type DeviceFacts } from "./deviceCheck";

const MAC_CHROME_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36";

const good: DeviceFacts = {
  userAgent: MAC_CHROME_UA, uaPlatform: "macOS", uaBrands: ["Chromium", "Google Chrome", "Not=A?Brand"],
  maxTouchPoints: 0, screenWidth: 1512, screenHeight: 982, devicePixelRatio: 2,
  batteryApi: true, charging: true, batteryLevel: 0.8, refreshHz: 120, windowFocused: true,
};
const failed = (f: Partial<DeviceFacts>) => evaluateDevice({ ...good, ...f }).items.filter((i) => !i.ok).map((i) => i.id);

describe("device check", () => {
  it("passes a 14-inch MacBook Pro in Chrome at 120 Hz", () => {
    const r = evaluateDevice(good);
    expect(r.ok).toBe(true);
    expect(r.proMotion).toBe(true);
  });

  it("blocks Windows and iPad", () => {
    expect(failed({ uaPlatform: "Windows", userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/158" })).toContain("mac");
    expect(failed({ uaPlatform: null, uaBrands: [], maxTouchPoints: 5, userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/19.0 Safari/605.1.15" })).toContain("mac");
  });

  it("blocks Safari and Edge", () => {
    expect(failed({ uaPlatform: null, uaBrands: [], batteryApi: false, charging: null, userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/19.0 Safari/605.1.15" })).toContain("chrome");
    expect(failed({ uaBrands: ["Chromium", "Microsoft Edge"] })).toContain("chrome");
  });

  it("does not require the charger", () => {
    expect(evaluateDevice({ ...good, charging: false, batteryLevel: 0.4 }).ok).toBe(true);
    expect(evaluateDevice({ ...good, batteryApi: false, charging: null, batteryLevel: null }).ok).toBe(true);
  });

  it("blocks Low Power Mode on a ProMotion MacBook Pro (60 Hz) and Energy Saver anywhere (30 Hz)", () => {
    expect(failed({ refreshHz: 60 })).toEqual(["display"]);
    expect(failed({ refreshHz: 30 })).toEqual(["display"]);
    expect(failed({ refreshHz: 30, screenWidth: 1470, screenHeight: 956 })).toEqual(["display"]);
  });

  it("accepts 60 Hz on a Mac whose display is not a 120 Hz panel", () => {
    expect(evaluateDevice({ ...good, refreshHz: 60, screenWidth: 1470, screenHeight: 956 }).ok).toBe(true);
  });

  it("does not trust a measurement taken while the window was in the background", () => {
    expect(failed({ windowFocused: false })).toEqual(["display"]);
  });
});
