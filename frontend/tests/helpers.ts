import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const ADMIN_PASSWORD = "e2e-test-password";

export async function adminToken(request: APIRequestContext): Promise<string> {
  const r = await request.post("/api/admin/login", { data: { password: ADMIN_PASSWORD } });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).token;
}

/** A short configuration so the full workflow runs in ~2 minutes (E2E only — never used for real data). */
export function shortConfig(base: Record<string, any>) {
  const c = structuredClone(base);
  c.name = "E2E short test configuration (software testing only)";
  c.timing = { ...c.timing, fixation_ms: 150, memory_stimulus_ms: 300, interference_ms: 900, retention_ms: 300,
    recognition_deadline_ms: 1200, iti_min_ms: 150, iti_max_ms: 250, practice_feedback_ms: 400, break_min_s: 1 };
  c.trials = { ...c.trials, trials_per_condition: 4, practice_per_condition: 2 };
  c.analysis = { ...c.analysis, min_valid_trials_per_condition: 3 };
  return c;
}

export async function createAndLockShortConfig(request: APIRequestContext, token: string): Promise<string> {
  const H = { Authorization: `Bearer ${token}` };
  const base = await (await request.get("/api/admin/configs/default", { headers: H })).json();
  const created = await request.post("/api/admin/configs", { headers: H, data: { config: shortConfig(base), notes: "E2E" } });
  expect(created.ok()).toBeTruthy();
  const row = await created.json();
  const locked = await request.post(`/api/admin/configs/${row.id}/lock`, { headers: H, data: { justification: "E2E automated software test configuration" } });
  expect(locked.ok()).toBeTruthy();
  return (await locked.json()).experiment_version;
}

/**
 * Drive the participant through the whole task. Keys are pressed continuously; the trial engine
 * accepts only responses inside response windows and ignores/counts the rest.
 */
export async function completeParticipantFlow(page: Page, opts: { age: string; gender: string; course: string; email: string }) {
  await page.goto("/participate");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /I consent/ }).click();
  await page.locator('input[name="age"]').fill(opts.age);
  await page.locator('select[name="gender"]').selectOption(opts.gender);
  await page.locator('input[name="academic_course"]').fill(opts.course);
  await page.locator('input[name="email"]').fill(opts.email);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Instructions" })).toBeVisible();
  const pid = (await page.locator("span.font-mono").first().textContent())?.trim() ?? "";
  await page.getByRole("button", { name: /Start practice/ }).click();

  const keys = ["f", "j"];
  let i = 0;
  let sawNextBlockHelp = false;
  const deadline = Date.now() + 8 * 60_000;
  while (Date.now() < deadline) {
    if (await page.getByText("Thank you — you have finished!").isVisible()) break;
    if (await page.getByRole("button", { name: "Start the main task" }).isVisible()) {
      await page.getByRole("button", { name: "Start the main task" }).click();
      continue;
    }
    if (!sawNextBlockHelp && await page.getByTestId("next-block-instructions").isVisible()) {
      sawNextBlockHelp = true;
      await page.screenshot({ path: "../tests/artifacts/break_next_block_instructions.png" });
    }
    const cont = page.getByRole("button", { name: /^(Start|Start block|Continue)$/ });
    if (await page.getByTestId("stage").isVisible()) {
      await page.keyboard.press(keys[i++ % 2]);
      await page.waitForTimeout(170);
    } else if (await cont.isVisible() && await cont.isEnabled()) {
      await cont.click();
    } else {
      await page.waitForTimeout(200);
    }
  }
  await expect(page.getByText("Thank you — you have finished!")).toBeVisible();
  expect(sawNextBlockHelp, "the break screen shows how the next block works").toBe(true);
  return pid;
}
