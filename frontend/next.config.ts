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
  // Admin host serves /media via proxy to the private backend — allow it
  { protocol: "https", hostname: "admin.siddhesh-chaudhari.com", pathname: "/**" },
  // Railway internal backend also appears in MEDIA_BASE_URL during migration
  { protocol: "http", hostname: "backend.railway.internal", pathname: "/**" },
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
  // Private backend: browser fetches via relative "/api" proxied to the
  // Railway internal backend at runtime (inside private network). Build/SSR
  // fetches use BACKEND_URL directly (see lib/api.ts) with a public-proxy
  // fallback when the builder cannot resolve *.railway.internal. This keeps the
  // backend out of the public CORS surface while still allowing the public
  // site to read content. Rewrites themselves are runtime-only; the backend
  // value is resolved when the server starts, so the builder never needs to
  // fetch it — but we keep the default in sync with the Railway PORT (8080).
  async rewrites() {
    const backend = process.env.BACKEND_URL ?? "http://backend.railway.internal:8080";
    return [
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
      { source: "/media/:path*", destination: `${backend}/media/:path*` },
    ];
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
