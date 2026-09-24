import Link from 'next/link'
import { formatDate, getPosts, sanityImageUrl } from '@/lib/sanity'

export const metadata = { title: 'Blog | Tank Metrics', description: 'The latest from Tank Metrics.' }

export default async function BlogPage() {
  const posts = await getPosts()
  return (
    <main className="page-shell">
      <section className="blog-intro">
        <p className="eyebrow">Field notes</p>
        <h1>Ideas worth measuring.</h1>
        <p className="lede">Stories, practical guidance, and thoughtful updates from the Tank Metrics team.</p>
      </section>
      <section className="post-list" aria-label="Blog posts">
        {posts.length ? posts.map((post) => {
          const image = sanityImageUrl(post.featuredImage)
          return (
            <article className="post-card" key={post._id}>
              {image && <img src={image} alt="" />}
              <div className="post-card-copy">
                <p className="post-date">{formatDate(post.publishedAt)}</p>
                <h2><Link href={`/blog/${post.slug.current}`}>{post.title}</Link></h2>
                {post.excerpt && <p>{post.excerpt}</p>}
                <Link className="read-more" href={`/blog/${post.slug.current}`}>Read story <span aria-hidden="true">→</span></Link>
              </div>
            </article>
          )
        }) : <p className="empty-state">No posts published yet. Check back soon.</p>}
      </section>
    </main>
  )
}
