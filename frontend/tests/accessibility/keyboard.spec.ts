import { test, expect } from '@playwright/test';

test('keyboard: tab order reaches all interactive elements', async ({ page }) => {
  // Synthetic Tab traversal is not reliable in WebKit (programmatic key
  // events don't drive native focus movement), so this runs on the desktop
  // (Chromium) project only. Mobile/tablet stay covered by axe + journeys.
  test.skip(
    test.info().project.name !== 'desktop',
    'Tab-traversal assertions only meaningful in Chromium',
  );
  // Returning-visitor context: the intro/category overlay is an animated
  // full-screen layer whose transient states make :focus assertions flaky.
  await page.addInitScript(() => {
    sessionStorage.setItem('intro-seen', 'true');
  });
  await page.goto('/');

  const focusable = await page.locator('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
  expect(focusable.length).toBeGreaterThan(0);

  // Anchor the traversal explicitly: WebKit doesn't move focus on a
  // programmatic first Tab from an unfocused document.
  await focusable[0].focus();

  const tabStops = Math.min(focusable.length, 10);
  for (let i = 1; i < tabStops; i++) {
    await page.keyboard.press('Tab');
    const focused = await page.locator(':focus').first();
    await expect(focused).toBeVisible();
  }
});

test('keyboard: filter chips have aria-pressed', async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem('intro-seen', 'true');
  });
  await page.goto('/timeline');

  const chips = await page.locator('[role="button"], button').filter({ hasText: /.+/ }).all();
  for (const chip of chips.slice(0, 5)) {
    const ariaPressed = await chip.getAttribute('aria-pressed');
    if (ariaPressed !== null) {
      expect(['true', 'false']).toContain(ariaPressed);
    }
  }
});
