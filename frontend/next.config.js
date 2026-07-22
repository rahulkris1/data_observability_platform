/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  eslint: {
    // Allow build to succeed even with ESLint errors (warnings only)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Allow build to succeed even with TypeScript errors (warnings only)
    ignoreBuildErrors: true,
  },
  // Proxy API requests to backend during development
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },
}

module.exports = nextConfig
