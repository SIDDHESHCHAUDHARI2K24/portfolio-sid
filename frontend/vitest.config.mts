import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "."),
    },
  },
  test: {
    // Unit tests live beside their sources. tests/** holds Playwright
    // e2e/a11y/visual specs (run by `npx playwright test`), which vitest's
    // default include glob would otherwise swallow and fail to load.
    include: ["**/*.{test,spec}.{ts,tsx}"],
    exclude: ["**/node_modules/**", "**/.next/**", "tests/**"],
  },
});
