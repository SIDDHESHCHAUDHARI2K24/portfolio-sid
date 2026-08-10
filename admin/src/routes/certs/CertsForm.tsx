import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
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

interface Certification {
  id: string
  title: string
  issuer: string
  kind: string
  issued_date: string
  expires_date: string | null
  credential_url: string | null
  file_key: string | null
  file_type: string | null
  sort_order: number
  status: string
  publish_at: string | null
  published_at: string | null
  audience_override: string[] | null
  topic_tags: TagRef[]
}

interface FormState {
  title: string
  issuer: string
  kind: string
  issued_date: string
  expires_date: string
  credential_url: string
  file_key: string
  file_type: string
  sort_order: number
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
    issuer: '',
    kind: 'technical',
    issued_date: '',
    expires_date: '',
    credential_url: '',
    file_key: '',
    file_type: '',
    sort_order: 0,
    tag_slugs: [],
    audience_override: null,
    status: 'draft',
    publish_at: '',
  }
}

export default function CertsForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: cert, isLoading } = useQuery<Certification>({
    queryKey: ['admin', 'certifications', id],
    queryFn: () => apiFetch<Certification>(`/admin/certifications/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (cert) {
      setForm({
        title: cert.title,
        issuer: cert.issuer,
        kind: cert.kind,
        issued_date: toDateInput(cert.issued_date),
        expires_date: toDateInput(cert.expires_date),
        credential_url: cert.credential_url ?? '',
        file_key: cert.file_key ?? '',
        file_type: cert.file_type ?? '',
        sort_order: cert.sort_order,
        tag_slugs: cert.topic_tags.map((t) => t.slug),
        audience_override: cert.audience_override ?? null,
        status: cert.status,
        publish_at: toDatetimeLocal(cert.publish_at),
      })
    }
  }, [cert])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/certifications', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/certs')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create certification.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/certifications/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/certs')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update certification.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.title.trim()) errs.title = 'Title is required'
    if (!form.issuer.trim()) errs.issuer = 'Issuer is required'
    if (!form.issued_date) errs.issued_date = 'Issued date is required'
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
      issuer: form.issuer.trim(),
      kind: form.kind,
      issued_date: form.issued_date,
      expires_date: form.expires_date || null,
      credential_url: form.credential_url.trim() || null,
      file_key: form.file_key.trim() || null,
      file_type: form.file_type || null,
      sort_order: form.sort_order,
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
        <p className="text-muted-foreground">Loading certification...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/certs')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">
          {isEdit ? 'Edit' : 'New'} Certification
        </h1>
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
                placeholder="AWS Solutions Architect"
              />
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
            </div>
            <div>
              <Label>Issuer</Label>
              <Input
                value={form.issuer}
                onChange={(e) => setForm((f) => ({ ...f, issuer: e.target.value }))}
                className={cn(errors.issuer && 'border-destructive')}
                placeholder="Amazon Web Services"
              />
              {errors.issuer && <p className="text-sm text-destructive">{errors.issuer}</p>}
            </div>
            <div>
              <Label>Kind</Label>
              <Select
                value={form.kind}
                onValueChange={(v) => setForm((f) => ({ ...f, kind: v }))}
              >
                <Select.Trigger>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="technical">Technical</Select.Item>
                  <Select.Item value="business">Business</Select.Item>
                </Select.Content>
              </Select>
            </div>
            <div>
              <Label>Issued Date</Label>
              <Input
                type="date"
                value={form.issued_date}
                onChange={(e) => setForm((f) => ({ ...f, issued_date: e.target.value }))}
                className={cn(errors.issued_date && 'border-destructive')}
              />
              {errors.issued_date && <p className="text-sm text-destructive">{errors.issued_date}</p>}
            </div>
            <div>
              <Label>Expires Date (optional)</Label>
              <Input
                type="date"
                value={form.expires_date}
                onChange={(e) => setForm((f) => ({ ...f, expires_date: e.target.value }))}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Links & File</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Credential URL</Label>
              <Input
                value={form.credential_url}
                onChange={(e) => setForm((f) => ({ ...f, credential_url: e.target.value }))}
                placeholder="https://www.credly.com/..."
              />
            </div>
            <div>
              <Label>File Type</Label>
              <Select
                value={form.file_type}
                onValueChange={(v) => setForm((f) => ({ ...f, file_type: v }))}
              >
                <Select.Trigger>
                  <Select.Value placeholder="None" />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="">None</Select.Item>
                  <Select.Item value="pdf">PDF</Select.Item>
                  <Select.Item value="image">Image</Select.Item>
                </Select.Content>
              </Select>
            </div>
            <div>
              <Label>File Key (R2)</Label>
              <Input
                value={form.file_key}
                onChange={(e) => setForm((f) => ({ ...f, file_key: e.target.value }))}
                placeholder="certs/aws-sa.pdf"
              />
            </div>
            <div>
              <Label>Sort Order</Label>
              <Input
                type="number"
                value={form.sort_order}
                onChange={(e) =>
                  setForm((f) => ({ ...f, sort_order: parseInt(e.target.value) || 0 }))
                }
                placeholder="0"
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
          <Button type="button" variant="outline" onClick={() => navigate('/certs')}>
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
