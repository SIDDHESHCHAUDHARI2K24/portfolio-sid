import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Skill {
  id: string
  name: string
  section: string
  subsection: string | null
  icon_slug: string | null
  icon_key: string | null
  sort_order: number
}

interface FormState {
  name: string
  section: string
  subsection: string
  icon_slug: string
  icon_key: string
  sort_order: number
}

const SECTIONS = [
  { value: 'languages', label: 'Languages' },
  { value: 'tools', label: 'Tools & Platforms' },
  { value: 'frameworks', label: 'Frameworks & Libraries' },
  { value: 'ai', label: 'AI & Data' },
  { value: 'business', label: 'Business & Strategy' },
]

function cdnPreviewUrl(slug: string): string {
  return `https://cdn.jsdelivr.net/npm/simple-icons@14/icons/${encodeURIComponent(slug)}.svg`
}

function emptyForm(): FormState {
  return {
    name: '',
    section: 'languages',
    subsection: '',
    icon_slug: '',
    icon_key: '',
    sort_order: 0,
  }
}

export default function SkillsForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')
  const [iconPreviewFailed, setIconPreviewFailed] = useState(false)

  const { data: skill, isLoading } = useQuery<Skill>({
    queryKey: ['admin', 'skills', id],
    queryFn: () => apiFetch<Skill>(`/admin/skills/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (skill) {
      setForm({
        name: skill.name,
        section: skill.section,
        subsection: skill.subsection ?? '',
        icon_slug: skill.icon_slug ?? '',
        icon_key: skill.icon_key ?? '',
        sort_order: skill.sort_order,
      })
      setIconPreviewFailed(false)
    }
  }, [skill])

  useEffect(() => {
    if (form.icon_slug) {
      setIconPreviewFailed(false)
    }
  }, [form.icon_slug])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/skills', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/skills')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create skill.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/skills/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      navigate('/skills')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update skill.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    if (!form.section) errs.section = 'Section is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setServerError('')
    if (!validate()) return

    const payload: Record<string, unknown> = {
      name: form.name.trim(),
      section: form.section,
      subsection: form.subsection.trim() || null,
      icon_slug: form.icon_slug.trim() || null,
      icon_key: form.icon_key.trim() || null,
      sort_order: form.sort_order,
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
        <p className="text-muted-foreground">Loading skill...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/skills')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Skill</h1>
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
              <Label>Name</Label>
              <Input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className={cn(errors.name && 'border-destructive')}
                placeholder="Python"
              />
              {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
            </div>
            <div>
              <Label>Section</Label>
              <Select
                value={form.section}
                onValueChange={(v) => setForm((f) => ({ ...f, section: v }))}
              >
                <Select.Trigger className={cn(errors.section && 'border-destructive')}>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  {SECTIONS.map((s) => (
                    <Select.Item key={s.value} value={s.value}>
                      {s.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select>
              {errors.section && <p className="text-sm text-destructive">{errors.section}</p>}
            </div>
            <div>
              <Label>Subsection</Label>
              <Input
                value={form.subsection}
                onChange={(e) => setForm((f) => ({ ...f, subsection: e.target.value }))}
                placeholder="Product Management"
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
            <CardTitle className="text-base">Icon</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label>Simple Icons Slug</Label>
              <div className="flex items-center gap-2">
                <Input
                  value={form.icon_slug}
                  onChange={(e) => {
                    setForm((f) => ({ ...f, icon_slug: e.target.value }))
                    setIconPreviewFailed(false)
                  }}
                  placeholder="python"
                  className="flex-1"
                />
                {form.icon_slug && !iconPreviewFailed && (
                  <img
                    src={cdnPreviewUrl(form.icon_slug)}
                    alt=""
                    className="h-5 w-5 shrink-0"
                    onError={() => setIconPreviewFailed(true)}
                  />
                )}
                {form.icon_slug && iconPreviewFailed && (
                  <span className="text-xs text-destructive shrink-0">Invalid slug</span>
                )}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Slug from{' '}
                <a
                  href="https://simpleicons.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline"
                >
                  simpleicons.org
                </a>
                . Leave empty for text-only.
              </p>
            </div>
            <div>
              <Label>R2 Fallback Key</Label>
              <Input
                value={form.icon_key}
                onChange={(e) => setForm((f) => ({ ...f, icon_key: e.target.value }))}
                placeholder="icons/custom-python.svg"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Fallback image from R2 if the Simple Icons slug fails.
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/skills')}>
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
