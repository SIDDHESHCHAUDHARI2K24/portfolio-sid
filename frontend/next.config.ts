import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "media.siddhesh-chaudhari.com",
        pathname: "/**",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "9000",
        pathname: "/**",
      },
    ],
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
