import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    // Hydration-safe bootstrap: cookie/sessionStorage/URL params can only be
    // read after mount, so initial state is set from an effect on purpose.
    // Lazy useState initializers would run during SSR render and mismatch.
    files: [
      "components/CategoryProvider.tsx",
      "components/intro/IntroOverlay.tsx",
      "components/timeline/TimelineClient.tsx",
    ],
    rules: {
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
