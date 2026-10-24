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
/** Content Security Policy.
 *
 * The site is a set of static pages with their logic inline, so 'unsafe-inline'
 * is required for scripts and styles; hashes would have to be regenerated for
 * all 111 files on every edit. The policy still blocks the important classes of
 * attack: no third-party script origins, no framing (clickjacking), no object
 * embeds, and no form posts to another origin. */
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com",
  "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  "font-src 'self' https://fonts.gstatic.com",
  "img-src 'self' data:",
  // script.google.com is the contact form's Apps Script endpoint; it
  // answers from script.googleusercontent.com after the redirect.
  "connect-src 'self' https://www.google-analytics.com https://analytics.google.com https://region1.google-analytics.com https://www.googletagmanager.com https://script.google.com https://script.googleusercontent.com",
  // The PWA needs to load its manifest and its service worker.
  "manifest-src 'self'",
  "worker-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
  "upgrade-insecure-requests",
].join('; ')

const securityHeaders = [
  { key: 'Content-Security-Policy', value: csp },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), payment=()' },
]

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async headers() {
    return [{ source: '/:path*', headers: securityHeaders }]
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
      // /site/index.html is served directly as well as /, which is the same
      // page twice. The canonical tag already points home, but a redirect is
      // stronger: it stops Google spending crawl budget on a duplicate and
      // consolidates every signal on /.
      { source: '/site/index.html', destination: '/', permanent: true },
      // The bare /site path also served the home page, byte for byte the same
      // document as /. Exact matches only: /site/style.css and friends must
      // keep working, so this is not a /site/:path* wildcard.
      { source: '/site', destination: '/', permanent: true },
      { source: '/site/', destination: '/', permanent: true },
      // Static blog posts live at the root now.
      { source: '/site/blog-:slug.html', destination: '/:slug', permanent: true },
      { source: '/calculators', destination: '/', permanent: true },
    ]
  },
}

export default nextConfig
