import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "media.siddhesh-chaudhari.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
