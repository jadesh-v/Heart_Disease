/** @type {import('next').NextConfig} */
const path = require("path");
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nextConfig = {
  reactStrictMode: true,
  // Silence the "multiple lockfiles" workspace-root warning
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_BASE}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
