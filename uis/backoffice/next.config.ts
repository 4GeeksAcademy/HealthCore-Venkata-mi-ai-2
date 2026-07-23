import path from "path";
import type { NextConfig } from "next";

const healthcoreSrc = path.resolve(process.cwd(), "../../src");

const nextConfig: NextConfig = {
  // Allow importing Milestone 2 TypeScript from repo root `src/`.
  turbopack: {
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
};

export default nextConfig;
