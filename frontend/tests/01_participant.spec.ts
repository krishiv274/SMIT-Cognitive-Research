import { expect, test } from "@playwright/test";
import { adminToken, completeParticipantFlow, createAndLockShortConfig } from "./helpers";

test.describe.configure({ mode: "serial" });

test("main study is closed until a configuration is locked", async ({ page }) => {
  await page.goto("/participate");
  await expect(page.getByText("The study is not open yet")).toBeVisible();
});

test("consent can be declined without storing data", async ({ page, request }) => {
  const token = await adminToken(request);
  await createAndLockShortConfig(request, token);
  await page.goto("/participate");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("button", { name: /I consent/ })).toBeDisabled();
  await page.getByRole("button", { name: /do not wish/ }).click();
  await expect(page.getByText("No information has been stored")).toBeVisible();
  const ov = await (await request.get("/api/admin/overview", { headers: { Authorization: `Bearer ${token}` } })).json();
  expect(ov.registered_participants).toBe(0);
});

test("registration validates age and email", async ({ page }) => {
  await page.goto("/participate");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /I consent/ }).click();
  await page.locator('input[name="age"]').fill("16");
  await page.locator('input[name="email"]').fill("not-an-email");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("You must be 18 or older to take part.")).toBeVisible();
  await expect(page.getByText("Please enter a valid email address.")).toBeVisible();
});

test("complete participant workflow: practice, three blocks, completion and saved data", async ({ page, request }) => {
  const token = await adminToken(request);
  const H = { Authorization: `Bearer ${token}` };
  const pid = await completeParticipantFlow(page, { age: "22", gender: "Female", course: "BSc Psychology", email: "e2e.participant1@example.test" });
  await expect(page.getByText(/All 12 experimental trials were saved successfully/)).toBeVisible();
  await expect(page.getByText(pid)).toBeVisible();

  const ov = await (await request.get("/api/admin/overview", { headers: H })).json();
  expect(ov.completed_participants).toBe(1);
  const parts = await (await request.get("/api/admin/participants?scope=main", { headers: H })).json();
  const s = parts[0].sessions[0];
  expect(s.completion_status).toBe("completed");
  const detail = await (await request.get(`/api/admin/sessions/${s.session_id}`, { headers: H })).json();
  const main = detail.trials.filter((t: any) => !t.practice_trial);
  const practice = detail.trials.filter((t: any) => t.practice_trial);
  expect(main).toHaveLength(12);
  expect(practice).toHaveLength(6);
  // condition transitions follow the assigned counterbalanced order
  const order = main.sort((a: any, b: any) => a.trial_number - b.trial_number).map((t: any) => t.condition);
  const blocks = [order.slice(0, 4), order.slice(4, 8), order.slice(8, 12)].map((b: string[]) => b[0]);
  expect(blocks.join("")).toBe(s.condition_order);
  // timing measured for every trial, close to plan in a headless browser
  for (const t of main) {
    expect(t.measured_stimulus_duration_ms).not.toBeNull();
    expect(Math.abs(t.measured_stimulus_duration_ms - t.planned_stimulus_duration_ms)).toBeLessThan(60);
    expect(Math.abs(t.measured_interference_duration_ms - t.planned_interference_duration_ms)).toBeLessThan(80);
  }
  // emails never appear in de-identified exports
  const exp = await request.get("/api/admin/export?fmt=json&scope=main", { headers: H });
  expect(await exp.text()).not.toContain("example.test");
});

test("second participant receives the next counterbalancing order", async ({ page, request }) => {
  const token = await adminToken(request);
  const H = { Authorization: `Bearer ${token}` };
  await completeParticipantFlow(page, { age: "30", gender: "Male", course: "BTech CSE", email: "e2e.participant2@example.test" });
  const ov = await (await request.get("/api/admin/overview", { headers: H })).json();
  expect(ov.condition_order_distribution.ABC).toBe(1);
  expect(ov.condition_order_distribution.ACB).toBe(1);
});

test("duplicate email registration is rejected for the main study", async ({ page }) => {
  await page.goto("/participate");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /I consent/ }).click();
  await page.locator('input[name="age"]').fill("25");
  await page.locator('select[name="gender"]').selectOption("Other");
  await page.locator('input[name="academic_course"]').fill("MA English");
  await page.locator('input[name="email"]').fill("E2E.participant1@example.test");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText(/already registered/)).toBeVisible();
});

test("an interrupted session can be resumed without creating a duplicate session", async ({ page, request }) => {
  const token = await adminToken(request);
  const H = { Authorization: `Bearer ${token}` };
  await page.goto("/participate");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: /I consent/ }).click();
  await page.locator('input[name="age"]').fill("40");
  await page.locator('select[name="gender"]').selectOption("Prefer not to answer");
  await page.locator('input[name="academic_course"]').fill("PhD Physics");
  await page.locator('input[name="email"]').fill("e2e.participant3@example.test");
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: /Start practice/ }).click();
  // finish practice quickly, start main, run a few trials, then "crash" (reload)
  const end = Date.now() + 120_000;
  while (Date.now() < end) {
    if (await page.getByRole("button", { name: "Start the main task" }).isVisible()) break;
    if (await page.getByTestId("stage").isVisible()) { await page.keyboard.press("f"); await page.waitForTimeout(150); }
    else if (await page.getByRole("button", { name: "Start" }).isVisible()) await page.getByRole("button", { name: "Start" }).click();
    else await page.waitForTimeout(150);
  }
  await page.getByRole("button", { name: "Start the main task" }).click();
  await page.getByRole("button", { name: "Start block" }).click();
  await page.waitForTimeout(6000);
  await page.reload();
  await expect(page.getByText("Unfinished session found")).toBeVisible();
  await page.getByRole("button", { name: "Resume this session" }).click();
  await expect(page.getByText(/resuming/)).toBeVisible();
  const before = await (await request.get("/api/admin/participants?scope=main", { headers: H })).json();
  const p3 = before.find((p: any) => p.age === 40);
  expect(p3.sessions).toHaveLength(1);
  expect(p3.sessions[0].interruptions).toBeGreaterThanOrEqual(1);
});
