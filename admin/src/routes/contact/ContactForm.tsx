import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { SaveIcon, CheckIcon, AlertCircleIcon, PlusIcon, Trash2Icon, ArrowUpIcon, ArrowDownIcon } from 'lucide-react'

interface ContactItem {
  id?: string
  kind: string
  label: string
  url: string
}

interface ContactProfile {
  consent_text: string
  items: ContactItem[]
}

const KIND_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'github', label: 'GitHub' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'tiktok', label: 'TikTok' },
  { value: 'x', label: 'X / Twitter' },
  { value: 'youtube', label: 'YouTube' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'cal', label: 'Book a call' },
  { value: 'phone', label: 'Phone' },
  { value: 'website', label: 'Website' },
  { value: 'generic', label: 'Other' },
]

const EMPTY_ITEM: ContactItem = { kind: 'generic', label: '', url: '' }

export default function ContactFormPage() {
  const queryClient = useQueryClient()
  const [consentText, setConsentText] = useState('')
  const [items, setItems] = useState<ContactItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  const { data, isLoading } = useQuery<ContactProfile>({
    queryKey: ['admin', 'contact'],
    queryFn: () => apiFetch<ContactProfile>('/admin/contact'),
  })

  useEffect(() => {
    if (data) {
      setConsentText(data.consent_text)
      setItems(data.items.map(({ id, kind, label, url }) => ({ id, kind, label, url })))
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: (body: { consent_text: string; items: ContactItem[] }) =>
      apiFetch<ContactProfile>('/admin/contact', {
        method: 'PUT',
        body: JSON.stringify({ ...body, items: body.items.map(({ kind, label, url }) => ({ kind, label, url })) }),
      }),
    onSuccess: (updated) => {
      setConsentText(updated.consent_text)
      setItems(updated.items.map(({ id, kind, label, url }) => ({ id, kind, label, url })))
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
    mutation.mutate({ consent_text: consentText, items })
  }

  const setItem = (index: number, patch: Partial<ContactItem>) => {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)))
    setSaved(false)
  }

  const addItem = () => {
    setItems((prev) => [...prev, { ...EMPTY_ITEM }])
    setSaved(false)
  }

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, i) => i !== index))
    setSaved(false)
  }

  const moveItem = (index: number, direction: -1 | 1) => {
    setItems((prev) => {
      const target = index + direction
      if (target < 0 || target >= prev.length) return prev
      const next = [...prev]
      const [item] = next.splice(index, 1)
      next.splice(target, 0, item)
      return next
    })
    setSaved(false)
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Contact details</CardTitle>
          <CardDescription>
            Content shown on the public <span className="font-medium">/contact</span> page —
            emails and links in the order below. Saving revalidates the page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-muted-foreground">Loading contact details...</p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="consent_text">Consent text</Label>
                <Textarea
                  id="consent_text"
                  rows={3}
                  value={consentText}
                  onChange={(e) => {
                    setConsentText(e.target.value)
                    setSaved(false)
                  }}
                />
              </div>

              <div className="space-y-3">
                <Label>Contact items</Label>
                {items.length === 0 && (
                  <p className="text-sm text-muted-foreground">No items yet — add one below.</p>
                )}
                {items.map((item, index) => (
                  <div key={index} className="rounded-md border border-border p-3 space-y-2">
                    <div className="grid grid-cols-[1fr_auto] gap-2">
                      <Select
                        value={item.kind}
                        onValueChange={(v) => setItem(index, { kind: v })}
                      >
                        <Select.Trigger>
                          <Select.Value />
                        </Select.Trigger>
                        <Select.Content>
                          {KIND_OPTIONS.map((option) => (
                            <Select.Item key={option.value} value={option.value}>
                              {option.label}
                            </Select.Item>
                          ))}
                        </Select.Content>
                      </Select>
                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          disabled={index === 0}
                          onClick={() => moveItem(index, -1)}
                          aria-label="Move up"
                        >
                          <ArrowUpIcon className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          disabled={index === items.length - 1}
                          onClick={() => moveItem(index, 1)}
                          aria-label="Move down"
                        >
                          <ArrowDownIcon className="size-4" />
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => removeItem(index)}
                          aria-label="Remove item"
                        >
                          <Trash2Icon className="size-4" />
                        </Button>
                      </div>
                    </div>
                    <Input
                      placeholder="Label (e.g. siddheshcoursemail@gmail.com)"
                      value={item.label}
                      onChange={(e) => setItem(index, { label: e.target.value })}
                    />
                    <Input
                      placeholder="URL (https://…, mailto:…, tel:…)"
                      value={item.url}
                      onChange={(e) => setItem(index, { url: e.target.value })}
                    />
                  </div>
                ))}
                <Button type="button" variant="outline" onClick={addItem}>
                  <PlusIcon className="mr-2 size-4" />
                  Add item
                </Button>
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
