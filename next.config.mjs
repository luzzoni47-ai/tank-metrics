/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // beforeFiles wins over app/page.tsx so the root serves the static app
    return {
      beforeFiles: [{ source: '/', destination: '/site/index.html' }],
      afterFiles: [],
      fallback: [],
    }
  },
  async redirects() {
    return [
      { source: '/blog', destination: '/site/blog.html', permanent: true },
      { source: '/about', destination: '/site/about.html', permanent: true },
      { source: '/contact', destination: '/site/contact.html', permanent: true },
      { source: '/privacy-policy', destination: '/site/privacy-policy.html', permanent: true },
      { source: '/terms-and-conditions', destination: '/site/terms-and-conditions.html', permanent: true },
      { source: '/disclaimer', destination: '/site/disclaimer.html', permanent: true },
      { source: '/calculators', destination: '/site/index.html', permanent: true },
    ]
  },
}

export default nextConfig
