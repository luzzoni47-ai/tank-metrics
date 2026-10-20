import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="blog-intro">
        <p className="eyebrow">Tank Metrics</p>
        <h1>Clarity for every tank.</h1>
        <p className="lede">Practical thinking and perspectives on keeping complex systems moving.</p>
        <p style={{ marginTop: 32 }}><Link className="read-more" href="/blog">Explore the blog <span aria-hidden="true">→</span></Link></p>
      </section>
    </main>
  )
}
