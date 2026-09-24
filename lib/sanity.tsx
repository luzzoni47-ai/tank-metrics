import { createClient } from '@sanity/client'

export const sanity = createClient({
  projectId: '2nhnwemv',
  dataset: 'production',
  apiVersion: '2026-09-24',
  useCdn: true,
})

export type BlogPost = {
  _id: string
  title: string
  slug: { current: string }
  excerpt?: string
  featuredImage?: { asset?: { _ref?: string } }
  publishedAt?: string
  body?: Array<{
    _key: string
    _type: string
    style?: string
    children?: Array<{ text?: string; marks?: string[] }>
    markDefs?: Array<{ _key: string; _type: string; href?: string }>
  }>
}

export async function getPosts() {
  return sanity.fetch<BlogPost[]>(
    `*[_type == "post"] | order(publishedAt desc) { _id, title, slug, excerpt, featuredImage, publishedAt }`,
    {},
    { next: { revalidate: 60 } },
  )
}

export async function getPost(slug: string) {
  return sanity.fetch<BlogPost | null>(
    `*[_type == "post" && slug.current == $slug][0] { _id, title, slug, excerpt, featuredImage, publishedAt, body }`,
    { slug },
    { next: { revalidate: 60 } },
  )
}

export function sanityImageUrl(image?: BlogPost['featuredImage']) {
  const ref = image?.asset?._ref
  if (!ref) return null
  const [, id, dimensions, format] = ref.split('-')
  if (!id || !dimensions || !format) return null
  return `https://cdn.sanity.io/images/2nhnwemv/production/${id}-${dimensions}.${format}`
}

export function formatDate(date?: string) {
  if (!date) return 'Unpublished'
  return new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(date))
}

export function renderPortableText(blocks?: BlogPost['body']) {
  return (blocks ?? []).map((block) => {
    const text = (block.children ?? []).map((child) => child.text ?? '').join('')
    if (block._type !== 'block') return null
    if (block.style === 'h2') return <h2 key={block._key}>{text}</h2>
    if (block.style === 'h3') return <h3 key={block._key}>{text}</h3>
    if (block.style === 'blockquote') return <blockquote key={block._key}>{text}</blockquote>
    return <p key={block._key}>{text}</p>
  })
}
import React from 'react'
