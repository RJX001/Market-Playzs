import type { NextConfig } from "next";

const API_PROXY_ORIGIN =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

const nextConfig: NextConfig = {
  transpilePackages: ["@marketplays/shared"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_PROXY_ORIGIN}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
