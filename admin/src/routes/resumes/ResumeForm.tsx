import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResumeEntry {
  id: string
  variant: string
  label: string
  file_key: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface FormState {
  variant: string
  label: string
  file_key: string
  is_active: boolean
}

// 6 canonical variants per backend/scripts/resume_canon.json:resumes
const VARIANT_OPTIONS: { value: string; label: string }[] = [
  { value: 'business', label: 'Business / TPM' },
  { value: 'generic', label: 'Product Builder' },
  { value: 'vc', label: 'Venture Capital' },
  { value: 'ai_consultant', label: 'AI Consultant' },
  { value: 'ai_workflow', label: 'AI Workflow Engineer' },
  { value: 'product_engineer', label: 'Product Engineer' },
]

function emptyForm(): FormState {
  return {
    variant: 'business',
    label: '',
    file_key: '',
    is_active: true,
  }
}

export default function ResumeForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')

  const { data: entry, isLoading } = useQuery<ResumeEntry>({
    queryKey: ['admin', 'resumes', id],
    queryFn: () => apiFetch<ResumeEntry>(`/admin/resumes/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (entry) {
      setForm({
        variant: entry.variant,
        label: entry.label,
        file_key: entry.file_key,
        is_active: entry.is_active,
      })
    }
  }, [entry])

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/resumes', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      navigate('/resumes')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to create resume.')
      }
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/resumes/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
      navigate('/resumes')
    },
    onError: (err) => {
      if (err instanceof ApiError && err.status === 422) {
        setServerError(err.message)
      } else {
        setServerError('Failed to update resume.')
      }
    },
  })

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.variant) errs.variant = 'Variant is required'
    if (!form.label.trim()) errs.label = 'Label is required'
    if (!form.file_key.trim()) errs.file_key = 'File key is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setServerError('')
    if (!validate()) return

    const payload: Record<string, unknown> = {
      variant: form.variant,
      label: form.label.trim(),
      file_key: form.file_key.trim(),
      is_active: form.is_active,
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
        <p className="text-muted-foreground">Loading resume...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/resumes')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Resume</h1>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {serverError && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
            {serverError}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Resume Details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Variant</Label>
              <Select
                value={form.variant}
                onValueChange={(v) => setForm((f) => ({ ...f, variant: v }))}
              >
                <Select.Trigger className={cn(errors.variant && 'border-destructive')}>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  {VARIANT_OPTIONS.map((opt) => (
                    <Select.Item key={opt.value} value={opt.value}>
                      {opt.label}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select>
              {errors.variant && <p className="text-sm text-destructive">{errors.variant}</p>}
            </div>
            <div>
              <Label>Label</Label>
              <Input
                value={form.label}
                onChange={(e) => setForm((f) => ({ ...f, label: e.target.value }))}
                className={cn(errors.label && 'border-destructive')}
                placeholder="Engineering Resume"
              />
              {errors.label && <p className="text-sm text-destructive">{errors.label}</p>}
            </div>
            <div className="sm:col-span-2">
              <Label>File Key</Label>
              <Input
                value={form.file_key}
                onChange={(e) => setForm((f) => ({ ...f, file_key: e.target.value }))}
                className={cn(errors.file_key && 'border-destructive')}
                placeholder="resumes/engineering-v2.pdf"
              />
              {errors.file_key && <p className="text-sm text-destructive">{errors.file_key}</p>}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="is_active"
                  checked={form.is_active}
                  onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))}
                />
                <Label htmlFor="is_active">Active</Label>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/resumes')}>
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
