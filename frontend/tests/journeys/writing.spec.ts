import { test, expect } from "@playwright/test";

/**
 * Journey: themed page -> native article -> back.
 * Needs at least one published internal post in the how_i_use_ai collection
 * (seed_demo.py or the admin); skipped when the API has none.
 */
test("themed page -> native article -> back", async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("intro-seen", "true");
  });
  await page.goto("/how-i-use-ai");

  const card = page.locator('a[href^="/writing/"]').first();
  test.skip((await card.count()) === 0, "no published internal post in how_i_use_ai");

  const title = (await card.locator("h2").innerText()).trim();
  const href = (await card.getAttribute("href")) as string;
  // internal cards open in the same tab (no target=_blank)
  await expect(card).not.toHaveAttribute("target", "_blank");

  await card.click();
  await expect(page).toHaveURL(new RegExp(`${href}$`));
  await expect(page.getByRole("heading", { level: 1, name: title })).toBeVisible();
  await expect(page.locator("article time")).toBeVisible();
  // canonical points at the single /writing/<slug> URL
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/writing\//);
  // raw HTML in the body never becomes an element
  await expect(page.locator("article script")).toHaveCount(0);

  await page.goBack();
  await expect(page).toHaveURL(/\/how-i-use-ai$/);
  await expect(page.getByRole("heading", { level: 1, name: "How I Use AI" })).toBeVisible();
});

test("unknown slug is a 404", async ({ page }) => {
  const resp = await page.goto("/writing/does-not-exist-xyz");
  expect(resp?.status()).toBe(404);
});
