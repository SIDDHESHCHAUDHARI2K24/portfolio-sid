export interface TagRef {
  id: string;
  slug: string;
  label: string;
}

export interface AttachmentRef {
  id: string;
  kind: string;
  label: string;
  sort_order: number;
  url: string;
}

export interface Project {
  id: string;
  title: string;
  slug: string;
  summary: string | null;
  description: string | null;
  video_url: string | null;
  timeline_entry_id: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
  topic_tags: TagRef[];
  attachments: AttachmentRef[];
}
