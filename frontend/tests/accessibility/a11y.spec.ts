import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const ROUTES = ['/', '/timeline', '/projects', '/skills', '/certifications', '/contact'];

for (const route of ROUTES) {
  const name = route === '/' ? 'homepage' : route.slice(1);

  test(`axe: ${name}`, async ({ page }) => {
    // Scan as a returning visitor: the intro/category gate is an animated
    // full-screen overlay that would otherwise cover the page under test.
    await page.addInitScript(() => {
      sessionStorage.setItem('intro-seen', 'true');
    });
    await page.goto(route);
    // networkidle never settles here (Turnstile/audio keep the network
    // busy); axe needs a stable DOM, not a quiet network.
    await page.evaluate(() => document.fonts.ready);
    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === 'serious' || v.impact === 'critical',
    );
    expect(serious, `Axe violations on ${route}: ${JSON.stringify(serious, null, 2)}`).toEqual([]);
  });
}
