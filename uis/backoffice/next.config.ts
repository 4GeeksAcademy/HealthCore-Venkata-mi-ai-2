import path from "path";
import type { NextConfig } from "next";

const healthcoreSrc = path.resolve(process.cwd(), "../../src");

const nextConfig: NextConfig = {
  poweredByHeader: false,
  compress: true,
  // Allow importing Milestone 2 TypeScript from repo root `src/`.
  // Pin turbopack root to the monorepo so @hc aliases resolve (Next infers
  // this from the root lockfile; setting it avoids a wrong-root warning).
  turbopack: {
    root: path.resolve(process.cwd(), "../.."),
    resolveAlias: {
      "@hc": healthcoreSrc,
    },
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@hc": healthcoreSrc,
    };
    return config;
  },
  async rewrites() {
    const internal =
      process.env.HEALTHCORE_API_INTERNAL_URL?.replace(/\/$/, "") ||
      "http://api:8001";
    return [{ source: "/hc-api/:path*", destination: `${internal}/:path*` }];
  },
};

export default nextConfig;
