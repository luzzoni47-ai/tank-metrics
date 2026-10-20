import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))

// tools/clean_urls.py owns the public URL shape. Read it here so the routing
// table and the links inside the HTML can never drift apart.
const urlMap = JSON.parse(readFileSync(join(here, 'tools/url-map.json'), 'utf8'))

// clean path (e.g. /sip-calculator) -> static file (e.g. /site/tools/sip-calculator.html)
const cleanRewrites = Object.entries(urlMap).map(([clean, file]) => ({ source: clean, destination: file }))

// The same table, inverted, retires the .html URLs that Google already has.
const htmlRedirects = Object.entries(urlMap).map(([clean, file]) => ({
  source: file,
  destination: clean,
  permanent: true,
}))

/** The static pages under /site are the site of record, so they win over the
 * unused App Router blog scaffold that also declares /blog. */
/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return {
      // beforeFiles keeps a clean URL in the address bar; afterFiles would
      // resolve the destination first and expose /site/*.html again.
      beforeFiles: [
        { source: '/', destination: '/site/index.html' },
        ...cleanRewrites,
      ],
      afterFiles: [],
      fallback: [],
    }
  },
  async redirects() {
    return [
      ...htmlRedirects,
      // Static blog posts are now nested under /blog/*.
      { source: '/site/blog-:slug.html', destination: '/blog/:slug', permanent: true },
      { source: '/calculators', destination: '/', permanent: true },
    ]
  },
}

export default nextConfig
