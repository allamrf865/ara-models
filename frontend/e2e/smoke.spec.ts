import { test, expect } from "@playwright/test";

test("landing page loads and shows progress", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1")).toContainText("ARA RADAR");
  await expect(page.locator("canvas")).toBeVisible();
});

test("redirects to dashboard after loading", async ({ page }) => {
  await page.goto("/");
  await page.waitForURL("/dashboard", { timeout: 10000 });
  await expect(page).toHaveURL("/dashboard");
});

test("dashboard loads without errors", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page.locator("h1")).toContainText("Dashboard");
  await expect(page.getByText("Top Candidates")).toBeVisible();
});

test("settings page is accessible", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.locator("h1")).toContainText("Settings");
  await expect(page.getByText("Alert Threshold")).toBeVisible();
});

test("model card page is accessible", async ({ page }) => {
  await page.goto("/about/model-card");
  await expect(page.locator("h1")).toContainText("Model Card");
});
