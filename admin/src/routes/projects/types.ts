export interface TagRef {
  id: string
  slug: string
  label: string
}

export interface AttachmentRef {
  id: string
  kind: string
  label: string
  sort_order: number
  url: string
  storage_key?: string
}

export interface Project {
  id: string
  title: string
  slug: string
  summary: string | null
  description: string | null
  video_url: string | null
  timeline_entry_id: string | null
  sort_order: number
  status: string
  publish_at: string | null
  published_at: string | null
  audience_override: string[] | null
  topic_tags: TagRef[]
  attachments: AttachmentRef[]
  created_at?: string
  updated_at?: string
}
