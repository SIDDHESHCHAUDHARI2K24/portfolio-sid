import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { TagSelect } from '@/components/fields/TagSelect'
import { AudienceOverrideSelect } from '@/components/fields/AudienceOverrideSelect'
import { PublishStatusField } from '@/components/fields/PublishStatusField'
import { MarkdownField } from '@/components/fields/MarkdownField'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TagRef {
  id: string
  slug: string
  label: string
}

interface AttachmentRef {
  id: string
  kind: string
  label: string
  sort_order: number
  url: string
  storage_key: string
}

interface Project {
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
}

interface TimelineEntry {
  id: string
  title: string
  organisation: string
}

interface FormState {
  title: string
  slug: string
  summary: string
  description: string
  video_url: string
  timeline_entry_id: string
  tag_slugs: string[]
  audience_override: string[] | null
  status: string
  publish_at: string
}

function toDatetimeLocal(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr.slice(0, 16)
  return d.toISOString().slice(0, 16)
}

function emptyForm(): FormState {
  return {
    title: '',
    slug: '',
    summary: '',
    description: '',
    video_url: '',
    timeline_entry_id: '',
    tag_slugs: [],
    audience_override: null,
    status: 'draft',
    publish_at: '',
  }
}

export default function ProjectForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: project, isLoading } = useQuery<Project>({
    queryKey: ['admin', 'projects', id],
    queryFn: () => apiFetch<Project>(`/admin/projects/${id}`),
    enabled: isEdit,
  })

  const { data: timelineEntries = [] } = useQuery<TimelineEntry[]>({
    queryKey: ['admin', 'timeline'],
    queryFn: () => apiFetch<TimelineEntry[]>('/admin/timeline'),
  })

  useEffect(() => {
    if (project) {
      setForm({
        title: project.title,
        slug: project.slug,
        summary: project.summary ?? '',
        description: project.description ?? '',
        video_url: project.video_url ?? '',
        timeline_entry_id: project.timeline_entry_id ?? '',
        tag_slugs: project.topic_tags.map((t) => t.slug),
        audience_override: project.audience_override ?? null,
        status: project.status,
        publish_at: toDatetimeLocal(project.publish_at),
      })
    }
  }, [project])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/projects', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/projects')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create project.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/projects/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/projects')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update project.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.title.trim()) errs.title = 'Title is required'
    if (!form.slug.trim()) errs.slug = 'Slug is required'
    if (form.status === 'scheduled' && !form.publish_at) {
      errs.publish_at = 'Publish date is required when scheduled'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setServerError('')
    if (!validate()) return

    const payload: Record<string, unknown> = {
      title: form.title.trim(),
      slug: form.slug.trim(),
      summary: form.summary.trim() || null,
      description: form.description.trim() || null,
      video_url: form.video_url.trim() || null,
      timeline_entry_id: form.timeline_entry_id || null,
      tag_slugs: form.tag_slugs,
      audience_override: form.audience_override,
      status: form.status,
      publish_at: form.publish_at ? new Date(form.publish_at).toISOString() : null,
    }

    if (isEdit) {
      updateMutation.mutate(payload)
    } else {
      createMutation.mutate(payload)
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending

  if (isEdit && isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading project...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/projects')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Project</h1>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {serverError && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {serverError}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Basic Details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Title</Label>
              <Input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                className={cn(errors.title && 'border-destructive')}
                placeholder="My Awesome Project"
              />
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
            </div>
            <div>
              <Label>Slug</Label>
              <Input
                value={form.slug}
                onChange={(e) => setForm((f) => ({ ...f, slug: e.target.value }))}
                className={cn(errors.slug && 'border-destructive')}
                placeholder="my-project"
              />
              {errors.slug && <p className="text-sm text-destructive">{errors.slug}</p>}
            </div>
            <div>
              <Label>Video URL (YouTube)</Label>
              <Input
                value={form.video_url}
                onChange={(e) => setForm((f) => ({ ...f, video_url: e.target.value }))}
                placeholder="https://youtube.com/watch?v=..."
              />
            </div>
            <div>
              <Label>Linked Experience</Label>
              <select
                value={form.timeline_entry_id}
                onChange={(e) => setForm((f) => ({ ...f, timeline_entry_id: e.target.value }))}
                className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm outline-none focus-visible:border-ring"
              >
                <option value="">None</option>
                {timelineEntries.map((entry) => (
                  <option key={entry.id} value={entry.id}>
                    {entry.title} at {entry.organisation}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <MarkdownField
              label="Summary"
              value={form.summary}
              onChange={(v) => setForm((f) => ({ ...f, summary: v }))}
            />
            <div>
              <Label className="text-sm">Description (Markdown)</Label>
              <Textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                rows={10}
                placeholder="Full project description in markdown..."
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Classification</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label className="text-sm">Topic Tags</Label>
              <TagSelect
                value={form.tag_slugs}
                onChange={(slugs) => setForm((f) => ({ ...f, tag_slugs: slugs }))}
              />
            </div>
            <AudienceOverrideSelect
              value={form.audience_override}
              onChange={(v) => setForm((f) => ({ ...f, audience_override: v }))}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Publishing</CardTitle>
          </CardHeader>
          <CardContent>
            <PublishStatusField
              status={form.status}
              publishAt={form.publish_at}
              onStatusChange={(v) => setForm((f) => ({ ...f, status: v }))}
              onPublishAtChange={(v) => setForm((f) => ({ ...f, publish_at: v }))}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/projects')}>
            Cancel
          </Button>
          <Button type="submit" disabled={isPending} className="gap-1.5">
            <SaveIcon className="size-4" />
            {isPending ? 'Saving...' : isEdit ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </div>
  )
}
