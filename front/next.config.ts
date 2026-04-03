import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  experimental: {
    // ... other experimental options if any
  },
  // @ts-ignore - Turbopack root config might not be in official types yet
  turbopack: {
    root: '..',
  },
};

export default nextConfig;
