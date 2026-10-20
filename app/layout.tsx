import type { Metadata } from 'next'
import Link from 'next/link'
import Script from 'next/script'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tank Metrics',
  description: 'Insights, stories, and updates from Tank Metrics.',
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
        <header className="site-header">
          <Link className="brand" href="/">Tank Metrics</Link>
          <nav aria-label="Main navigation">
            <Link href="/">Home</Link>
            <Link href="/blog">Blog</Link>
          </nav>
        </header>
        {children}
        <footer className="site-footer">© {new Date().getFullYear()} Tank Metrics</footer>
      </body>
    </html>
  )
}
