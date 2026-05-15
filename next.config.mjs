/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  serverExternalPackages: [
    "node-telegram-bot-api",
    "@cypress/request",
    "@cypress/request-promise",
    "yahoo-finance2",
    "chrome-remote-interface",
    "ws",
    "bufferutil",
    "utf-8-validate",
  ],
  webpack: (config, { isServer }) => {
    if (isServer) {
      // Prevent webpack from trying to bundle Node-only packages
      const externals = Array.isArray(config.externals) ? config.externals : [];
      config.externals = [
        ...externals,
        ({ request }, callback) => {
          if (
            request?.startsWith("@cypress/") ||
            request === "node-telegram-bot-api" ||
            request === "chrome-remote-interface"
          ) {
            return callback(null, `commonjs ${request}`);
          }
          callback();
        },
      ];
    }
    return config;
  },
  async headers() {
    return [
      {
        source: "/api/webhook/:path*",
        headers: [{ key: "Cache-Control", value: "no-store" }],
      },
    ];
  },
};

export default nextConfig;
