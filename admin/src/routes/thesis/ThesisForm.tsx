import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { TagSelect } from '@/components/fields/TagSelect'
import { AudienceOverrideSelect } from '@/components/fields/AudienceOverrideSelect'
import { PublishStatusField } from '@/components/fields/PublishStatusField'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TagRef {
  id: string
  slug: string
  label: string
}

interface ThesisEntry {
  id: string
  title: string
  summary: string | null
  drive_url: string
  published_date: string
  sort_order: number
  status: string
  publish_at: string | null
  published_at: string | null
  audience_override: string[] | null
  topic_tags: TagRef[]
}

interface FormState {
  title: string
  summary: string
  drive_url: string
  published_date: string
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
    title: '',
    summary: '',
    drive_url: '',
    published_date: '',
    tag_slugs: [],
    audience_override: null,
    status: 'draft',
    publish_at: '',
  }
}

export default function ThesisForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: entry, isLoading } = useQuery<ThesisEntry>({
    queryKey: ['admin', 'thesis', id],
    queryFn: () => apiFetch<ThesisEntry>(`/admin/thesis/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (entry) {
      setForm({
        title: entry.title,
        summary: entry.summary ?? '',
        drive_url: entry.drive_url,
        published_date: toDateInput(entry.published_date),
        tag_slugs: entry.topic_tags.map((t) => t.slug),
        audience_override: entry.audience_override ?? null,
        status: entry.status,
        publish_at: toDatetimeLocal(entry.publish_at),
      })
    }
  }, [entry])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/thesis', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thesis'] })
      navigate('/thesis')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create thesis.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/thesis/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['thesis'] })
      navigate('/thesis')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update thesis.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.title.trim()) errs.title = 'Title is required'
    if (!form.drive_url.trim()) errs.drive_url = 'Drive URL is required'
    if (!form.published_date) errs.published_date = 'Published date is required'
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
      summary: form.summary.trim() || null,
      drive_url: form.drive_url.trim(),
      published_date: form.published_date,
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
        <p className="text-muted-foreground">Loading thesis...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/thesis')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Thesis</h1>
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
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label>Title</Label>
              <Input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                className={cn(errors.title && 'border-destructive')}
                placeholder="My Investment Thesis"
              />
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
            </div>
            <div>
              <Label>Summary</Label>
              <Textarea
                value={form.summary}
                onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
                rows={4}
                placeholder="Brief summary of this thesis entry..."
              />
            </div>
            <div>
              <Label>Drive URL</Label>
              <Input
                value={form.drive_url}
                onChange={(e) => setForm((f) => ({ ...f, drive_url: e.target.value }))}
                className={cn(errors.drive_url && 'border-destructive')}
                placeholder="https://drive.google.com/..."
              />
              {errors.drive_url && <p className="text-sm text-destructive">{errors.drive_url}</p>}
            </div>
            <div>
              <Label>Published Date</Label>
              <Input
                type="date"
                value={form.published_date}
                onChange={(e) => setForm((f) => ({ ...f, published_date: e.target.value }))}
                className={cn(errors.published_date && 'border-destructive')}
              />
              {errors.published_date && <p className="text-sm text-destructive">{errors.published_date}</p>}
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
              error={errors.publish_at}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/thesis')}>
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
