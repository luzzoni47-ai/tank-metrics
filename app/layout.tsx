import type { Metadata } from 'next'
import Script from 'next/script'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tank Metrics',
  description: 'Free business and money calculators for India — valuation, EMI, GST, tax and more.',
  icons: {
    // Keep these in step with tools/make_favicon.py: Google only shows a
    // favicon whose side is a multiple of 48px, and a `sizes` that disagrees
    // with the real file (this used to claim 64x64 over a 256x256 png) makes
    // Google distrust the icon and keep the old cached one.
    icon: [
      { url: '/site/favicon.ico', sizes: 'any' },
      { url: '/site/favicon.svg', type: 'image/svg+xml' },
      { url: '/site/favicon.png', type: 'image/png', sizes: '192x192' },
    ],
    apple: { url: '/site/favicon.png', sizes: '192x192' },
  },
  manifest: '/site/manifest.webmanifest',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Script
          src="https://www.googletagmanager.com/gtag/js?id=G-MHZ0V6HFC6"
          strategy="afterInteractive"
        />
        <Script id="google-analytics" strategy="afterInteractive">
          {`
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-MHZ0V6HFC6');
  `}
        </Script>
        {children}
      </body>
    </html>
  )
}
