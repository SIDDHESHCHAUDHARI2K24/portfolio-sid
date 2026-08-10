import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { PublishStatusField } from '@/components/fields/PublishStatusField'
import { ArrowLeftIcon, SaveIcon, SearchIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Item {
  id: string
  title: string
  creator: string | null
  kind: string
  section: string | null
  cover_key: string | null
  external_id: string | null
  external_source: string | null
  status: string | null
  note: string | null
  sort_order: number
  status_: string
  publish_at: string | null
}

interface FormState {
  title: string
  creator: string
  kind: string
  section: string
  note: string
  read_status: string
  cover_key: string
  external_id: string
  external_source: string
  sort_order: number
  publish_status: string
  publish_at: string
}

interface CoverLookupResult {
  status: string
  cover_key: string | null
}

const KINDS = [
  { value: 'book', label: 'Book' },
  { value: 'anime', label: 'Anime' },
  { value: 'manhwa', label: 'Manhwa' },
]

const READ_STATUSES = [
  { value: '', label: 'None' },
  { value: 'reading', label: 'Reading' },
  { value: 'completed', label: 'Completed' },
  { value: 'want_to_read', label: 'Want to Read' },
]

const SECTIONS = [
  { value: '', label: 'None' },
  { value: 'Tech', label: 'Tech' },
  { value: 'Business', label: 'Business' },
  { value: 'Personal Development', label: 'Personal Development' },
]

function toDatetimeLocal(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return ''
  return d.toISOString().slice(0, 16)
}

function emptyForm(): FormState {
  return {
    title: '',
    creator: '',
    kind: 'book',
    section: '',
    note: '',
    read_status: '',
    cover_key: '',
    external_id: '',
    external_source: '',
    sort_order: 0,
    publish_status: 'draft',
    publish_at: '',
  }
}

export default function CollectionsForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')
  const [coverLookup, setCoverLookup] = useState<CoverLookupResult | null>(null)
  const [lookupLoading, setLookupLoading] = useState(false)

  const { data: item, isLoading } = useQuery<Item>({
    queryKey: ['admin', 'collections', id],
    queryFn: () => apiFetch<Item>(`/admin/collections/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (item) {
      setForm({
        title: item.title,
        creator: item.creator ?? '',
        kind: item.kind,
        section: item.section ?? '',
        note: item.note ?? '',
        read_status: item.status ?? '',
        cover_key: item.cover_key ?? '',
        external_id: item.external_id ?? '',
        external_source: item.external_source ?? '',
        sort_order: item.sort_order,
        publish_status: item.status_,
        publish_at: toDatetimeLocal(item.publish_at),
      })
    }
  }, [item])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/collections', { method: 'POST', body: JSON.stringify(data) }),
    onSuccess: () => navigate('/collections'),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create item.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/collections/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
    onSuccess: () => navigate('/collections'),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update item.')
      }
    },
  })

  const handleLookup = async () => {
    if (!form.title.trim()) return
    setLookupLoading(true)
    setCoverLookup(null)
    try {
      const result = await apiFetch<CoverLookupResult>('/admin/collections/cover-lookup', {
        method: 'POST',
        body: JSON.stringify({ title: form.title.trim(), kind: form.kind }),
      })
      setCoverLookup(result)
      if (result.status === 'found' && result.cover_key) {
        setForm((f) => ({ ...f, cover_key: result.cover_key }))
      }
    } catch {
      setCoverLookup({ status: 'failed' })
    } finally {
      setLookupLoading(false)
    }
  }

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.title.trim()) errs.title = 'Title is required'
    if (form.publish_status === 'scheduled' && !form.publish_at) {
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
      creator: form.creator.trim() || null,
      kind: form.kind,
      section: form.kind === 'book' ? (form.section || null) : null,
      note: form.note.trim() || null,
      status: form.read_status || null,
      cover_key: form.cover_key.trim() || null,
      external_id: form.external_id.trim() || null,
      external_source: form.external_source || null,
      sort_order: form.sort_order,
      publish_status: form.publish_status,
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
        <p className="text-muted-foreground">Loading item...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/collections')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Item</h1>
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
              <div className="flex gap-2">
                <Input
                  value={form.title}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  className={cn('flex-1', errors.title && 'border-destructive')}
                  placeholder="The Pragmatic Programmer"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={handleLookup}
                  disabled={lookupLoading || !form.title.trim()}
                  title="Look up cover"
                >
                  <SearchIcon className="size-4" />
                </Button>
              </div>
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
              {coverLookup && (
                <p className={cn(
                  'text-xs mt-1',
                  coverLookup.status === 'found' ? 'text-green-600' :
                  coverLookup.status === 'no_match' ? 'text-yellow-600' :
                  'text-destructive'
                )}>
                  {coverLookup.status === 'found'
                    ? 'Cover found and stored.'
                    : coverLookup.status === 'no_match'
                    ? 'No cover found. Upload manually.'
                    : 'Lookup failed. Upload manually.'}
                </p>
              )}
              {lookupLoading && <p className="text-xs text-muted-foreground mt-1">Searching...</p>}
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
                  {KINDS.map((k) => (
                    <Select.Item key={k.value} value={k.value}>
                      {k.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select>
            </div>
            <div>
              <Label>Creator</Label>
              <Input
                value={form.creator}
                onChange={(e) => setForm((f) => ({ ...f, creator: e.target.value }))}
                placeholder="Author or studio"
              />
            </div>
            {form.kind === 'book' && (
              <div>
                <Label>Section</Label>
                <Select
                  value={form.section}
                  onValueChange={(v) => setForm((f) => ({ ...f, section: v }))}
                >
                  <Select.Trigger>
                    <Select.Value placeholder="None" />
                  </Select.Trigger>
                  <Select.Content>
                    {SECTIONS.map((s) => (
                      <Select.Item key={s.value} value={s.value}>
                        {s.label}
                      </Select.Item>
                    ))}
                  </Select.Content>
                </Select>
              </div>
            )}
            <div>
              <Label>Status</Label>
              <Select
                value={form.read_status}
                onValueChange={(v) => setForm((f) => ({ ...f, read_status: v }))}
              >
                <Select.Trigger>
                  <Select.Value placeholder="None" />
                </Select.Trigger>
                <Select.Content>
                  {READ_STATUSES.map((s) => (
                    <Select.Item key={s.value} value={s.value}>
                      {s.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cover & External</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Cover Key (R2)</Label>
              <Input
                value={form.cover_key}
                onChange={(e) => setForm((f) => ({ ...f, cover_key: e.target.value }))}
                placeholder="book-abc123.jpg"
              />
            </div>
            <div>
              <Label>External Source</Label>
              <Select
                value={form.external_source}
                onValueChange={(v) => setForm((f) => ({ ...f, external_source: v }))}
              >
                <Select.Trigger>
                  <Select.Value placeholder="None" />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="">None</Select.Item>
                  <Select.Item value="open_library">Open Library</Select.Item>
                  <Select.Item value="jikan">Jikan</Select.Item>
                  <Select.Item value="manual">Manual</Select.Item>
                </Select.Content>
              </Select>
            </div>
            <div>
              <Label>External ID</Label>
              <Input
                value={form.external_id}
                onChange={(e) => setForm((f) => ({ ...f, external_id: e.target.value }))}
                placeholder="OL123456"
              />
            </div>
            <div>
              <Label>Sort Order</Label>
              <Input
                type="number"
                value={form.sort_order}
                onChange={(e) => setForm((f) => ({ ...f, sort_order: parseInt(e.target.value) || 0 }))}
                placeholder="0"
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Note</CardTitle>
          </CardHeader>
          <CardContent>
            <Input
              value={form.note}
              onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))}
              placeholder="Personal notes..."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Publishing</CardTitle>
          </CardHeader>
          <CardContent>
            <PublishStatusField
              status={form.publish_status}
              publishAt={form.publish_at}
              onStatusChange={(v) => setForm((f) => ({ ...f, publish_status: v }))}
              onPublishAtChange={(v) => setForm((f) => ({ ...f, publish_at: v }))}
            />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/collections')}>
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
