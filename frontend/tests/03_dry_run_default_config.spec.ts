/**
 * TECHNICAL DRY RUN with the real default configuration (500/500/3000/1000/2000 ms, 66 trials) in
 * PILOT mode on an isolated test database, driven by an automated in-page "participant". Records planned
 * vs measured timing and captures screenshots for the report appendix.
 * This is SOFTWARE verification only — it is NOT human pilot testing.
 * Run with:  SMIT_DRY_RUN=1 npx playwright test tests/03_dry_run_default_config.spec.ts
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { expect, test, type Page } from "@playwright/test";
import { adminToken } from "./helpers";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../..");
const SHOTS = path.join(ROOT, "docs/screenshots");
const ART = path.join(ROOT, "tests/artifacts");

test.skip(!process.env.SMIT_DRY_RUN, "set SMIT_DRY_RUN=1 to run the ~10 minute full-length dry run");
test.setTimeout(25 * 60_000);

async function shot(page: Page, name: string) {
  fs.mkdirSync(SHOTS, { recursive: true });
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

/** In-page automated participant: answers during response windows (with a delay) and clicks through screens. */
const AUTOPILOT = `
(() => {
  let k = 0, last = "";
  const key = (c) => window.dispatchEvent(new KeyboardEvent("keydown", { key: c, bubbles: true }));
  const btn = (t) => [...document.querySelectorAll("button")].find((b) => b.textContent.trim() === t && !b.disabled);
  setInterval(() => {
    if (window.__smitPause) return;
    const st = document.querySelector("[data-testid=stage]");
    if (st) {
      const ph = st.dataset.phase || "";
      if (ph !== last) {
        last = ph;
        const [cond, p] = ph.split(":");
        if (p === "probe") setTimeout(() => key(k++ % 3 ? "f" : "j"), 400 + (k % 5) * 80);
        if (p === "interference" && cond !== "A") setTimeout(() => key(k++ % 2 ? "f" : "j"), 1000);
      }
      return;
    }
    last = "";
    for (const t of ["Start", "Start block", "Start the main task", "Continue"]) { const b = btn(t); if (b) { b.click(); return; } }
  }, 30);
})();`;

test("full-length dry run of the default configuration with timing log and screenshots", async ({ page, request, context }) => {
  const token = await adminToken(request);
  const H = { Authorization: `Bearer ${token}` };
  const configs = await (await request.get("/api/admin/configs", { headers: H })).json();
  const def = configs.find((c: any) => c.version_number === 1);
  expect(def.deviations_from_specification).toEqual([]);
  const launch = await (await request.post("/api/admin/pilot/launch", { headers: H, data: { config_id: def.id } })).json();

  await page.goto(launch.url);
  await shot(page, "01_welcome");
  await page.getByRole("button", { name: "Continue" }).click();
  await shot(page, "02_consent");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /I consent/ }).click();
  await page.locator('input[name="age"]').fill("25");
  await page.locator('select[name="gender"]').selectOption("Prefer not to answer");
  await page.locator('input[name="academic_course"]').fill("Automated dry run");
  await page.locator('input[name="email"]').fill("dryrun@example.test");
  await shot(page, "03_registration");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Instructions" })).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 2000 });
  await shot(page, "04_instructions");
  await page.setViewportSize({ width: 1280, height: 860 });
  await page.getByRole("button", { name: /Start practice/ }).click();
  await expect(page.getByText(/^Practice · Hold$/)).toBeVisible();
  await shot(page, "05_practice_intro");
  await page.evaluate(AUTOPILOT);

  // Screenshots of each phase as it appears (polling the stage's data-phase attribute)
  const phaseShots: [string, string][] = [["A:fixation", "06_fixation"], ["A:memory", "07_memory_stimulus"], ["A:interference", "08_control_hold"],
    ["A:retention", "11_retention"], ["A:probe", "12_recognition_probe"], ["A:feedback", "13_practice_feedback"],
    ["B:interference", "09_numerical_interference"], ["C:interference", "10_visual_interference"]];
  for (const [phase, name] of phaseShots) {
    await page.waitForFunction((p) => document.querySelector("[data-testid=stage]")?.getAttribute("data-phase") === p, phase, { timeout: 120_000, polling: 10 });
    await page.waitForTimeout(phase.endsWith("interference") ? 120 : 40);
    await shot(page, name);
  }
  // Pause the autopilot on informative screens just long enough to capture them
  await page.waitForFunction(() => document.body.innerText.includes("Practice complete"), null, { timeout: 120_000, polling: 20 });
  await page.evaluate(() => { (window as any).__smitPause = true; });
  await shot(page, "14_practice_complete");
  await page.evaluate(() => { (window as any).__smitPause = false; });
  await page.waitForFunction(() => document.body.innerText.includes("Block 1 of 3"), null, { timeout: 60_000, polling: 20 });
  await page.evaluate(() => { (window as any).__smitPause = true; });
  await shot(page, "15_block_instructions");
  await page.evaluate(() => { (window as any).__smitPause = false; });
  await page.waitForFunction(() => document.body.innerText.includes("Short break"), null, { timeout: 6 * 60_000, polling: 100 });
  await shot(page, "16_break");
  await expect(page.getByText("Thank you — you have finished!")).toBeVisible({ timeout: 15 * 60_000 });
  await expect(page.getByText(/All 60 experimental trials were saved successfully/)).toBeVisible();
  await shot(page, "17_completion");

  // Timing log
  const parts = await (await request.get("/api/admin/participants?scope=pilot", { headers: H })).json();
  const sess = parts.find((p: any) => p.age === 25).sessions[0];
  const detail = await (await request.get(`/api/admin/sessions/${sess.session_id}`, { headers: H })).json();
  fs.mkdirSync(ART, { recursive: true });
  fs.writeFileSync(path.join(ART, "dry_run_session.json"), JSON.stringify({ session: detail.session, timing_summary: detail.timing_summary, flags: detail.flags,
    trials: detail.trials.map((t: any) => ({ n: t.trial_number, practice: t.practice_trial, cond: t.condition, fix: t.actual_fixation_duration_ms,
      mem: t.measured_stimulus_duration_ms, int: t.measured_interference_duration_ms, ret: t.measured_retention_duration_ms, iti: t.inter_trial_interval_ms,
      planned_iti: t.planned_iti_ms, rt: t.reaction_time_ms, resp: t.participant_response, sec: t.interference_response, flag: t.timing_quality_flag,
      dropped: t.dropped_frames, refresh: t.refresh_rate_hz })) }, null, 1));
  const main = detail.trials.filter((t: any) => !t.practice_trial);
  expect(main).toHaveLength(60);
  expect(detail.session.completion_status).toBe("completed");

  // Researcher dashboard screenshots (pages without research results)
  const admin = await context.newPage();
  await admin.goto("/researcher");
  await admin.getByLabel("Password").fill("e2e-test-password");
  await admin.getByRole("button", { name: "Sign in" }).click();
  await expect(admin.getByRole("heading", { name: "Overview" })).toBeVisible();
  await shot(admin, "20_dashboard_overview");
  await admin.getByRole("link", { name: "Configuration" }).click();
  await expect(admin.getByText("Versions")).toBeVisible();
  await shot(admin, "21_dashboard_configuration");
  await admin.getByRole("link", { name: "Pilot mode" }).click();
  await admin.getByRole("button", { name: "Inspect" }).first().click();
  await expect(admin.getByText("Timing (measured − planned, ms)")).toBeVisible();
  await shot(admin, "22_dashboard_pilot_timing");
  await admin.getByRole("link", { name: "Import / Export" }).click();
  await shot(admin, "23_dashboard_import");
});
