import Link from 'next/link'

export const metadata = { title: 'Page not found | Tank Metrics' }

export default function NotFound() {
  return (
    <>
      <div className="nf-stripe" />
      <main className="nf-wrap">
        <h1>404</h1>
        <h2>This page could not be found</h2>
        <p>
          The link may be old or mistyped. Every Tank Metrics calculator is one
          click away on the home page — all free, all instant, nothing you type
          ever leaves your browser.
        </p>
        <Link className="nf-cta" href="/">
          Browse all 100 calculators →
        </Link>
      </main>
    </>
  )
}
