import path from "node:path";
import { fileURLToPath } from "node:url";
const __dirname = path.dirname(fileURLToPath(import.meta.url));
import { expect, test, type Page } from "@playwright/test";
import { ADMIN_PASSWORD } from "./helpers";

test.describe.configure({ mode: "serial" });
const FIXTURE = path.resolve(__dirname, "../../tests/artifacts/SYNTHETIC_e2e.xlsx");

async function login(page: Page) {
  await page.goto("/researcher");
  await page.getByLabel("Password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
}

test("researcher login is required and wrong passwords are rejected", async ({ page }) => {
  await page.goto("/researcher/participants");
  await page.getByLabel("Password").fill("wrong");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Incorrect password")).toBeVisible();
});

test("overview, participants, configuration, pilot and audit pages", async ({ page }) => {
  await login(page);
  await expect(page.getByText(/Main study open with locked configuration/)).toBeVisible();
  await expect(page.getByText("Condition-order distribution (counterbalancing)")).toBeVisible();
  await page.getByRole("link", { name: "Participants" }).click();
  await expect(page.getByText("P001", { exact: true })).toBeVisible();
  await expect(page.getByText("e2e.participant1@example.test")).toHaveCount(0);
  await page.getByRole("button", { name: "details" }).first().click();
  await expect(page.getByText("Timing (measured − planned, ms)")).toBeVisible();
  await page.getByRole("button", { name: "Close" }).click();
  await page.getByRole("link", { name: "Configuration" }).click();
  await expect(page.getByText("locked · ACTIVE")).toBeVisible();
  await page.getByRole("button", { name: /Copy to draft|Edit/ }).first().click();
  await page.getByLabel("Memory stimulus exposure (ms)").fill("450");
  await page.getByRole("button", { name: "Save as new draft version" }).click();
  await expect(page.getByText(/Saved draft SMIT-v3/)).toBeVisible();
  await page.getByRole("link", { name: "Pilot mode" }).click();
  await page.getByRole("button", { name: "Preview stimuli" }).click();
  await expect(page.getByText(/Stimulus preview/)).toBeVisible();
  const [popup] = await Promise.all([page.waitForEvent("popup"), page.getByRole("button", { name: /Start pilot session/ }).click()]);
  await expect(popup.getByText("PILOT MODE")).toBeVisible();
  await popup.close();
  await page.getByRole("link", { name: "Audit log" }).click();
  await expect(page.getByText("config_created").first()).toBeVisible();
  await page.getByRole("button", { name: /Dark mode/ }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
});

test("dataset upload: validation preview, confirm, automatic analysis", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Import / Export" }).click();
  await page.getByTestId("file-input").setInputFiles(FIXTURE);
  await expect(page.getByText(/Validation passed/)).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText(/experimental_trials: 1440/)).toBeVisible();
  await page.getByRole("button", { name: "Confirm import" }).click();
  await expect(page.getByText(/Imported 24 participants, 24 sessions and 1584 trials/)).toBeVisible({ timeout: 120_000 });
  // uploading the same file again is refused
  await page.getByTestId("file-input").setInputFiles(FIXTURE);
  await expect(page.getByText(/Validation failed/)).toBeVisible({ timeout: 60_000 });
  await expect(page.getByText(/already imported/)).toBeVisible();
});

test("statistical analysis dashboard", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Analysis" }).click();
  await page.getByRole("button", { name: "Run Analysis" }).click();
  await expect(page.getByText(/Hypothesis outcomes/)).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText(/Confirmatory analysis — Recognition accuracy/)).toBeVisible();
  await expect(page.getByText(/Test selection:/).first()).toBeVisible();
  await expect(page.locator("img[alt='Mean recognition accuracy by interference condition']")).toBeVisible({ timeout: 30_000 });
  await expect(page.locator(".js-plotly-plot").first()).toBeVisible({ timeout: 30_000 });
});

test("report and presentation generation and download", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Reports" }).click();
  await page.getByRole("button", { name: "Generate Research Report" }).click();
  await expect(page.getByText(/Final report generated/)).toBeVisible({ timeout: 120_000 });
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "PDF" }).first().click()]);
  expect(dl.suggestedFilename()).toBe("SMIT_Research_Report.pdf");
  await page.getByRole("button", { name: "Regenerate presentation" }).click();
  await expect(page.getByText(/Presentation generated/)).toBeVisible({ timeout: 120_000 });
  const [dl2] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "PowerPoint (.pptx)" }).first().click()]);
  expect(dl2.suggestedFilename()).toBe("SMIT_Presentation.pptx");
});

test("templates download from the dashboard", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Import / Export" }).click();
  const [dl] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Full workbook (recommended)" }).click()]);
  expect(dl.suggestedFilename()).toBe("SMIT_Data_Collection_Template.xlsx");
});
