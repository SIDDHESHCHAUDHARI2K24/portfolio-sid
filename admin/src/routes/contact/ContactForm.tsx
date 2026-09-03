import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { SaveIcon, CheckIcon, AlertCircleIcon } from 'lucide-react'

interface ContactProfile {
  email: string
  linkedin_url: string
  linkedin_label: string
  cal_url: string
  cal_label: string
  github_url: string
  consent_text: string
}

const EMPTY: ContactProfile = {
  email: '',
  linkedin_url: '',
  linkedin_label: '',
  cal_url: '',
  cal_label: '',
  github_url: '',
  consent_text: '',
}

export default function ContactFormPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ContactProfile>(EMPTY)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const { data, isLoading } = useQuery<ContactProfile>({
    queryKey: ['admin', 'contact'],
    queryFn: () => apiFetch<ContactProfile>('/admin/contact'),
  })

  useEffect(() => {
    if (data) setForm(data)
  }, [data])

  const mutation = useMutation({
    mutationFn: (body: ContactProfile) =>
      apiFetch<ContactProfile>('/admin/contact', {
        method: 'PUT',
        body: JSON.stringify(body),
      }),
    onSuccess: (updated) => {
      setForm(updated)
      setSaved(true)
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['admin', 'contact'] })
    },
    onError: (err: unknown) => {
      setSaved(false)
      setError(err instanceof ApiError ? err.message : 'Failed to save contact details')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSaved(false)
    mutation.mutate(form)
  }

  const set = (key: keyof ContactProfile) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({ ...prev, [key]: e.target.value }))
    setSaved(false)
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Contact details</CardTitle>
          <CardDescription>
            Content shown on the public <span className="font-medium">/contact</span> page —
            email, links, and the form consent text. Saving revalidates the page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading contact details...</p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={form.email} onChange={set('email')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="linkedin_url">LinkedIn URL</Label>
                <Input id="linkedin_url" value={form.linkedin_url} onChange={set('linkedin_url')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="linkedin_label">LinkedIn display label</Label>
                <Input id="linkedin_label" value={form.linkedin_label} onChange={set('linkedin_label')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cal_url">Booking (Cal.com) URL</Label>
                <Input id="cal_url" value={form.cal_url} onChange={set('cal_url')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="cal_label">Booking display label</Label>
                <Input id="cal_label" value={form.cal_label} onChange={set('cal_label')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="github_url">GitHub URL</Label>
                <Input id="github_url" value={form.github_url} onChange={set('github_url')} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="consent_text">Consent text</Label>
                <Textarea id="consent_text" rows={3} value={form.consent_text} onChange={set('consent_text')} />
              </div>

              <div className="flex items-center gap-3">
                <Button type="submit" disabled={mutation.isPending}>
                  <SaveIcon className="mr-2 size-4" />
                  {mutation.isPending ? 'Saving...' : 'Save'}
                </Button>
                {saved && (
                  <span className="flex items-center gap-1 text-sm text-green-600">
                    <CheckIcon className="size-4" /> Saved
                  </span>
                )}
                {error && (
                  <span className="flex items-center gap-1 text-sm text-red-600">
                    <AlertCircleIcon className="size-4" /> {error}
                  </span>
                )}
              </div>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
