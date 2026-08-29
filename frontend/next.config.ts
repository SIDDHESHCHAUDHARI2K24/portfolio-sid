import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

// Media is served by the backend: prod mounts /media on the admin custom domain
// (NEXT_PUBLIC_API_BASE_URL), dev serves it from MinIO at localhost:9000.
// Derive the allowed image host from the API base URL so remotePatterns tracks
// the same origin that returns media URLs in API payloads.
const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
const apiHost = (() => {
  try {
    return apiBase ? new URL(apiBase).hostname : "";
  } catch {
    return "";
  }
})();

type RemotePattern = {
  protocol: "http" | "https";
  hostname: string;
  port?: string;
  pathname: string;
};

const remotePatterns: RemotePattern[] = [
  { protocol: "http", hostname: "localhost", port: "9000", pathname: "/**" },
  { protocol: "http", hostname: "localhost", port: "3000", pathname: "/**" },
];
if (apiHost) {
  remotePatterns.push({
    protocol: apiBase.startsWith("https") ? "https" : "http",
    hostname: apiHost,
    pathname: "/**",
  });
}

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns,
  },
};

const sentryConfig = withSentryConfig(nextConfig, {
  org: "",
  project: "",
  silent: true,
  telemetry: false,
  disableLogger: true,
});

export default process.env.GLITCHTIP_DSN ? sentryConfig : nextConfig;
