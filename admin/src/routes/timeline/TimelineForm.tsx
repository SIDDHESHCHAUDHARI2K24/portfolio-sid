import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
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

interface TimelineEntry {
  id: string
  kind: string
  title: string
  organisation: string
  location: string | null
  start_date: string
  end_date: string | null
  summary: string | null
  highlights: string[] | null
  external_url: string | null
  sort_order: number
  status: string
  publish_at: string | null
  published_at: string | null
  audience_override: string[] | null
  topic_tags: TagRef[]
}

interface FormState {
  kind: string
  title: string
  organisation: string
  location: string
  start_date: string
  end_date: string
  summary: string
  highlights: string
  external_url: string
  tag_slugs: string[]
  audience_override: string[] | null
  status: string
  publish_at: string
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

function emptyForm(): FormState {
  return {
    kind: 'experience',
    title: '',
    organisation: '',
    location: '',
    start_date: '',
    end_date: '',
    summary: '',
    highlights: '',
    external_url: '',
    tag_slugs: [],
    audience_override: null,
    status: 'draft',
    publish_at: '',
  }
}

export default function TimelineForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: entry, isLoading } = useQuery<TimelineEntry>({
    queryKey: ['admin', 'timeline', id],
    queryFn: () => apiFetch<TimelineEntry>(`/admin/timeline/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (entry) {
      setForm({
        kind: entry.kind,
        title: entry.title,
        organisation: entry.organisation,
        location: entry.location ?? '',
        start_date: toDateInput(entry.start_date),
        end_date: toDateInput(entry.end_date),
        summary: entry.summary ?? '',
        highlights: entry.highlights?.join('\n') ?? '',
        external_url: entry.external_url ?? '',
        tag_slugs: entry.topic_tags.map((t) => t.slug),
        audience_override: entry.audience_override ?? null,
        status: entry.status,
        publish_at: toDatetimeLocal(entry.publish_at),
      })
    }
  }, [entry])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/timeline', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/timeline')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create entry.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/timeline/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/timeline')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update entry.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.kind) errs.kind = 'Kind is required'
    if (!form.title.trim()) errs.title = 'Title is required'
    if (!form.organisation.trim()) errs.organisation = 'Organisation is required'
    if (!form.start_date) errs.start_date = 'Start date is required'
    if (form.end_date && form.start_date && form.end_date < form.start_date) {
      errs.end_date = 'End date must be on or after start date'
    }
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

    const highlights = form.highlights
      .split('\n')
      .map((h) => h.trim())
      .filter(Boolean)

    const payload: Record<string, unknown> = {
      kind: form.kind,
      title: form.title.trim(),
      organisation: form.organisation.trim(),
      location: form.location.trim() || null,
      start_date: form.start_date,
      end_date: form.end_date || null,
      summary: form.summary.trim() || null,
      highlights: highlights.length > 0 ? highlights : null,
      external_url: form.external_url.trim() || null,
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
        <p className="text-muted-foreground">Loading entry...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/timeline')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Timeline Entry</h1>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {serverError && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {serverError}
          </div>
        )}

        {/* Basic fields */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Basic Details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Kind</Label>
              <Select
                value={form.kind}
                onValueChange={(v) => setForm((f) => ({ ...f, kind: v }))}
              >
                <Select.Trigger className={cn(errors.kind && 'border-destructive')}>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="education">Education</Select.Item>
                  <Select.Item value="experience">Experience</Select.Item>
                </Select.Content>
              </Select>
              {errors.kind && <p className="text-sm text-destructive">{errors.kind}</p>}
            </div>
            <div>
              <Label>Title</Label>
              <Input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                className={cn(errors.title && 'border-destructive')}
                placeholder="Software Engineer"
              />
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
            </div>
            <div>
              <Label>Organisation</Label>
              <Input
                value={form.organisation}
                onChange={(e) => setForm((f) => ({ ...f, organisation: e.target.value }))}
                className={cn(errors.organisation && 'border-destructive')}
                placeholder="Acme Corp"
              />
              {errors.organisation && <p className="text-sm text-destructive">{errors.organisation}</p>}
            </div>
            <div>
              <Label>Location</Label>
              <Input
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                placeholder="San Francisco, CA"
              />
            </div>
            <div>
              <Label>Start Date</Label>
              <Input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm((f) => ({ ...f, start_date: e.target.value }))}
                className={cn(errors.start_date && 'border-destructive')}
              />
              {errors.start_date && <p className="text-sm text-destructive">{errors.start_date}</p>}
            </div>
            <div>
              <Label>End Date</Label>
              <Input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm((f) => ({ ...f, end_date: e.target.value }))}
                className={cn(errors.end_date && 'border-destructive')}
              />
              {errors.end_date && <p className="text-sm text-destructive">{errors.end_date}</p>}
            </div>
          </CardContent>
        </Card>

        {/* Content fields */}
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
              <Label className="text-sm">Highlights (one per line)</Label>
              <Textarea
                value={form.highlights}
                onChange={(e) => setForm((f) => ({ ...f, highlights: e.target.value }))}
                rows={4}
                placeholder="Led a team of 5 engineers&#10;Reduced latency by 40%"
              />
            </div>
            <div>
              <Label>External URL</Label>
              <Input
                value={form.external_url}
                onChange={(e) => setForm((f) => ({ ...f, external_url: e.target.value }))}
                placeholder="https://example.com"
              />
            </div>
          </CardContent>
        </Card>

        {/* Classification */}
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

        {/* Publishing */}
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
          <Button type="button" variant="outline" onClick={() => navigate('/timeline')}>
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
