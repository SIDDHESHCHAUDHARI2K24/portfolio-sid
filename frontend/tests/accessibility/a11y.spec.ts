import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const ROUTES = ['/', '/timeline', '/projects', '/skills', '/certifications', '/contact'];

for (const route of ROUTES) {
  const name = route === '/' ? 'homepage' : route.slice(1);

  test(`axe: ${name}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState('networkidle');
    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(
      (v) => v.impact === 'serious' || v.impact === 'critical',
    );
    expect(serious, `Axe violations on ${route}: ${JSON.stringify(serious, null, 2)}`).toEqual([]);
  });
}
