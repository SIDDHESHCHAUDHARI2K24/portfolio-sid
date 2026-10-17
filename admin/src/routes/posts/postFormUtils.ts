import { ApiError } from '@/lib/api'

interface TagRef {
  id: string
  slug: string
  label: string
}

export interface FormState {
  title: string
  summary: string
  url: string
  slug: string
  body: string
  platform: string
  published_date: string
  collections: string[]
  tag_slugs: string[]
  audience_override: string[] | null
  status: string
  publish_at: string
}

const BODY_MAX_BYTES = 100 * 1024

export function slugify(title: string): string {
  return title
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 200)
    .replace(/-+$/, '')
}

// FastAPI 422 detail: pydantic-shaped [{loc: [..., field], msg}] or a plain string.
function fieldErrorsFrom(data: unknown): Record<string, string> {
  const detail = (data as { detail?: unknown } | null)?.detail
  const out: Record<string, string> = {}
  if (Array.isArray(detail)) {
    for (const e of detail as { loc?: unknown[]; msg?: string }[]) {
      const field = e.loc?.[e.loc.length - 1]
      if (typeof field === 'string' && e.msg) out[field] = e.msg
    }
  }
  return out
}

export function describeSaveError(
  err: unknown,
  fallback: string,
): { message: string; fieldErrors?: Record<string, string> } {
  if (!(err instanceof ApiError) || err.status !== 422) return { message: fallback }
  const fieldErrors = fieldErrorsFrom(err.data)
  if (Object.keys(fieldErrors).length === 0) return { message: String(err.message) }
  return { message: 'Please fix the highlighted fields.', fieldErrors }
}

export function validatePostForm(form: FormState): Record<string, string> {
  const errs: Record<string, string> = {}
  if (!form.title.trim()) errs.title = 'Title is required'
  if (!form.platform) errs.platform = 'Platform is required'
  if (form.platform === 'internal') {
    Object.assign(errs, validateInternal(form))
  } else if (!form.url.trim()) {
    errs.url = 'URL is required'
  }
  if (form.status === 'scheduled' && !form.publish_at) {
    errs.publish_at = 'Publish date is required when scheduled'
  }
  return errs
}

function validateInternal(form: FormState): Record<string, string> {
  const errs: Record<string, string> = {}
  const slug = form.slug.trim().toLowerCase()
  if (!slug) errs.slug = 'Slug is required'
  else if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(slug)) {
    errs.slug = 'Use lowercase letters, digits and single hyphens'
  }
  if (!form.body.trim()) errs.body = 'Body is required'
  else if (new TextEncoder().encode(form.body).length > BODY_MAX_BYTES) {
    errs.body = 'Body must be at most 100 KB'
  }
  return errs
}

export function buildPostPayload(form: FormState): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    title: form.title.trim(),
    summary: form.summary.trim() || null,
    platform: form.platform,
    published_date: form.published_date || null,
    collections: form.collections,
    tag_slugs: form.tag_slugs,
    audience_override: form.audience_override,
    status: form.status,
    publish_at: form.publish_at ? new Date(form.publish_at).toISOString() : null,
  }
  if (form.platform === 'internal') {
    // Internal posts have no url; body and slug are what the site serves.
    payload.url = null
    payload.slug = form.slug.trim().toLowerCase()
    payload.body = form.body
  } else {
    payload.url = form.url.trim()
  }
  return payload
}

export interface Post {
  id: string
  title: string
  summary: string | null
  url: string | null
  slug: string | null
  body: string | null
  platform: string
  published_date: string | null
  collections: string[]
  sort_order: number
  created_at: string
  updated_at: string
  topic_tags: TagRef[]
  audience_override: string[] | null
  status: string
  publish_at: string | null
  published_at: string | null
}

function toDateInput(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr.slice(0, 10)
  return d.toISOString().slice(0, 10)
}

function toDatetimeLocal(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr.slice(0, 16)
  return d.toISOString().slice(0, 16)
}

export function postToForm(post: Post): FormState {
  return {
    title: post.title,
    summary: post.summary ?? '',
    url: post.url ?? '',
    slug: post.slug ?? '',
    body: post.body ?? '',
    platform: post.platform,
    published_date: toDateInput(post.published_date),
    collections: post.collections,
    tag_slugs: post.topic_tags.map((t) => t.slug),
    audience_override: post.audience_override ?? null,
    status: post.status,
    publish_at: toDatetimeLocal(post.publish_at),
  }
}

/** Title edit: while the slug is untouched, an internal post's slug follows the title. */
export function withTitle(f: FormState, title: string, slugTouched: boolean): FormState {
  const follow = f.platform === 'internal' && !slugTouched
  return { ...f, title, slug: follow ? slugify(title) : f.slug }
}

/** Platform change: switching to internal suggests a slug from the title if none yet. */
export function withPlatform(f: FormState, platform: string, slugTouched: boolean): FormState {
  const suggest = platform === 'internal' && !slugTouched && !f.slug
  return { ...f, platform, slug: suggest ? slugify(f.title) : f.slug }
}
