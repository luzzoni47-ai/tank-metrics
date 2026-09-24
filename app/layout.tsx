import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tank Metrics',
  description: 'Insights, stories, and updates from Tank Metrics.',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
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
