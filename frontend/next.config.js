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
}

module.exports = nextConfig
