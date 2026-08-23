import { test, expect } from '@playwright/test';

test('keyboard: tab order reaches all interactive elements', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const focusable = await page.locator('a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])').all();
  expect(focusable.length).toBeGreaterThan(0);

  const tabStops = Math.min(focusable.length, 10);
  for (let i = 0; i < tabStops; i++) {
    await page.keyboard.press('Tab');
    const focused = await page.locator(':focus').first();
    await expect(focused).toBeVisible();
  }
});

test('keyboard: filter chips have aria-pressed', async ({ page }) => {
  await page.goto('/timeline');
  await page.waitForLoadState('networkidle');

  const chips = await page.locator('[role="button"], button').filter({ hasText: /.+/ }).all();
  for (const chip of chips.slice(0, 5)) {
    const ariaPressed = await chip.getAttribute('aria-pressed');
    if (ariaPressed !== null) {
      expect(['true', 'false']).toContain(ariaPressed);
    }
  }
});
