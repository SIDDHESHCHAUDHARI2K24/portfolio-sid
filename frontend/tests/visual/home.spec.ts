import { test, expect } from '@playwright/test';

const PUBLIC_ROUTES = [
  '/',
  '/timeline',
  '/projects',
  '/skills',
  '/certifications',
  '/tech-rabbithole',
  '/how-i-use-ai',
  '/vc-for-founders',
  '/thesis',
  '/books',
  '/anime-manga',
  '/contact',
  '/dealflow',
];

for (const route of PUBLIC_ROUTES) {
  const name = route === '/' ? 'homepage' : route.slice(1).replace(/\//g, '-');

  test(`visual: ${name}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
  });
}
