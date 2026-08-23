import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { PublishStatusField } from '@/components/fields/PublishStatusField'
import { MarkdownField } from '@/components/fields/MarkdownField'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface OverviewIntroAdmin {
  id: string
  audience: string
  headline: string
  body: string
  hero_image_key: string | null
  cta_label: string | null
  cta_url: string | null
  status: string
  publish_at: string | null
  published_at: string | null
}

interface FormState {
  audience: string
  headline: string
  body: string
  hero_image_key: string
  cta_label: string
  cta_url: string
  status: string
  publish_at: string
}

const AUDIENCE_OPTIONS = [
  { value: 'default', label: 'Default' },
  { value: 'recruiters', label: 'Recruiters' },
  { value: 'techies', label: 'Techies' },
  { value: 'investors', label: 'Investors' },
  { value: 'founders', label: 'Founders' },
  { value: 'personal', label: 'Personal' },
]

function toDatetimeLocal(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr.slice(0, 16)
  return d.toISOString().slice(0, 16)
}

function emptyForm(): FormState {
  return {
    audience: 'default',
    headline: '',
    body: '',
    hero_image_key: '',
    cta_label: '',
    cta_url: '',
    status: 'draft',
    publish_at: '',
  }
}

export default function OverviewForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: intro, isLoading } = useQuery<OverviewIntroAdmin>({
    queryKey: ['admin', 'overview', id],
    queryFn: () => apiFetch<OverviewIntroAdmin>(`/admin/overview/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (intro) {
      setForm({
        audience: intro.audience,
        headline: intro.headline,
        body: intro.body,
        hero_image_key: intro.hero_image_key ?? '',
        cta_label: intro.cta_label ?? '',
        cta_url: intro.cta_url ?? '',
        status: intro.status,
        publish_at: toDatetimeLocal(intro.publish_at),
      })
    }
  }, [intro])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/overview', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['overview'] })
      navigate('/overview')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create intro.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/overview/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['overview'] })
      navigate('/overview')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update intro.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!isEdit && !form.audience) errs.audience = 'Audience is required'
    if (!form.headline.trim()) errs.headline = 'Headline is required'
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
      headline: form.headline.trim(),
      body: form.body,
      hero_image_key: form.hero_image_key.trim() || null,
      cta_label: form.cta_label.trim() || null,
      cta_url: form.cta_url.trim() || null,
      status: form.status,
      publish_at: form.publish_at ? new Date(form.publish_at).toISOString() : null,
    }

    if (!isEdit) {
      payload.audience = form.audience
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
        <p className="text-muted-foreground">Loading intro...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/overview')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Overview Intro</h1>
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
              <Label>Audience</Label>
              <Select
                value={form.audience}
                onValueChange={(v) => setForm((f) => ({ ...f, audience: v }))}
                disabled={isEdit}
              >
                <Select.Trigger className={cn(errors.audience && 'border-destructive')}>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  {AUDIENCE_OPTIONS.map((opt) => (
                    <Select.Item key={opt.value} value={opt.value}>
                      {opt.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select>
              {errors.audience && <p className="text-sm text-destructive">{errors.audience}</p>}
            </div>
            <div>
              <Label>Headline</Label>
              <Input
                value={form.headline}
                onChange={(e) => setForm((f) => ({ ...f, headline: e.target.value }))}
                className={cn(errors.headline && 'border-destructive')}
                placeholder="A brief introduction headline"
              />
              {errors.headline && <p className="text-sm text-destructive">{errors.headline}</p>}
            </div>
            <div>
              <Label>CTA Label</Label>
              <Input
                value={form.cta_label}
                onChange={(e) => setForm((f) => ({ ...f, cta_label: e.target.value }))}
                placeholder="Learn more"
              />
            </div>
            <div>
              <Label>CTA URL</Label>
              <Input
                value={form.cta_url}
                onChange={(e) => setForm((f) => ({ ...f, cta_url: e.target.value }))}
                placeholder="/about or https://..."
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <MarkdownField
              label="Body"
              value={form.body}
              onChange={(v) => setForm((f) => ({ ...f, body: v }))}
            />
            <div>
              <Label>Hero Image Key</Label>
              <Input
                value={form.hero_image_key}
                onChange={(e) => setForm((f) => ({ ...f, hero_image_key: e.target.value }))}
                placeholder="hero/default.webp"
              />
              <p className="text-xs text-muted-foreground mt-1">
                R2 storage key for the hero image (e.g. hero/some-file.webp)
              </p>
            </div>
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
          <Button type="button" variant="outline" onClick={() => navigate('/overview')}>
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
