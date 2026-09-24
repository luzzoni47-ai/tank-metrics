import { notFound } from 'next/navigation'
import { formatDate, getPost, renderPortableText, sanityImageUrl } from '@/lib/sanity'

export const dynamicParams = true

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const post = await getPost(slug)
  if (!post) notFound()
  const image = sanityImageUrl(post.featuredImage)
  return (
    <main className="article-shell">
      <p className="eyebrow">{formatDate(post.publishedAt)}</p>
      <h1>{post.title}</h1>
      {post.excerpt && <p className="article-excerpt">{post.excerpt}</p>}
      {image && <img className="article-image" src={image} alt="" />}
      <div className="article-body">{renderPortableText(post.body)}</div>
    </main>
  )
}
