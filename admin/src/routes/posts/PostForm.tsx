import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { TagSelect } from '@/components/fields/TagSelect'
import { AudienceOverrideSelect } from '@/components/fields/AudienceOverrideSelect'
import { PublishStatusField } from '@/components/fields/PublishStatusField'
import { CollectionsSelect } from '@/components/fields/CollectionsSelect'
import { MarkdownEditor } from './MarkdownEditor'
import {
  buildPostPayload,
  describeSaveError,
  postToForm,
  withPlatform,
  withTitle,
  type Post,
  validatePostForm,
  type FormState,
} from './postFormUtils'
import { LinkFields } from './LinkFields'
import { ArrowLeftIcon, SaveIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

function emptyForm(): FormState {
  return {
    title: '',
    summary: '',
    url: '',
    slug: '',
    body: '',
    platform: 'substack',
    published_date: '',
    collections: [],
    tag_slugs: [],
    audience_override: null,
    status: 'draft',
    publish_at: '',
  }
}

export default function PostForm() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const isEdit = !!id
  const [form, setForm] = useState<FormState>(emptyForm())
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [serverError, setServerError] = useState('')
  // Once the user edits the slug by hand, stop auto-suggesting it from the title.
  const slugTouched = useRef(false)

  const { data: post, isLoading } = useQuery<Post>({
    queryKey: ['admin', 'posts', id],
    queryFn: () => apiFetch<Post>(`/admin/posts/${id}`),
    enabled: isEdit,
  })

  useEffect(() => {
    if (post) {
      slugTouched.current = !!post.slug
      setForm(postToForm(post))
    }
  }, [post])

  const handleSaveError = (err: unknown, fallback: string) => {
    const { message, fieldErrors } = describeSaveError(err, fallback)
    if (fieldErrors) setErrors(fieldErrors)
    setServerError(message)
  }

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch('/admin/posts', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      navigate('/posts')
    },
    onError: (err) => {
      handleSaveError(err, 'Failed to create post.')
    },
  })

  const updateMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch(`/admin/posts/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      navigate('/posts')
    },
    onError: (err) => {
      handleSaveError(err, 'Failed to update post.')
    },
  })

  const validate = (): boolean => {
    const errs = validatePostForm(form)
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setServerError('')
    if (!validate()) return

    const payload = buildPostPayload(form)

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
        <p className="text-muted-foreground">Loading post...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate('/posts')}>
          <ArrowLeftIcon className="size-4" />
        </Button>
        <h1 className="text-2xl font-semibold">{isEdit ? 'Edit' : 'New'} Post</h1>
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
                onChange={(e) => {
                  const title = e.target.value
                  setForm((f) => withTitle(f, title, slugTouched.current))
                }}
                className={cn(errors.title && 'border-destructive')}
                placeholder="My latest blog post"
              />
              {errors.title && <p className="text-sm text-destructive">{errors.title}</p>}
            </div>
            <div>
              <Label>Platform</Label>
              <Select
                value={form.platform}
                onValueChange={(v) => setForm((f) => withPlatform(f, v, slugTouched.current))}
              >
                <Select.Trigger className={cn(errors.platform && 'border-destructive')}>
                  <Select.Value />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="substack">Substack</Select.Item>
                  <Select.Item value="medium">Medium</Select.Item>
                  <Select.Item value="youtube">YouTube</Select.Item>
                  <Select.Item value="other">Other</Select.Item>
                  <Select.Item value="internal">Native article</Select.Item>
                </Select.Content>
              </Select>
              {errors.platform && <p className="text-sm text-destructive">{errors.platform}</p>}
            </div>
            <LinkFields
              form={form}
              errors={errors}
              onUrlChange={(v) => setForm((f) => ({ ...f, url: v }))}
              onSlugChange={(v) => {
                slugTouched.current = true
                setForm((f) => ({ ...f, slug: v }))
              }}
            />
            <div>
              <Label>Published Date</Label>
              <Input
                type="date"
                value={form.published_date}
                onChange={(e) => setForm((f) => ({ ...f, published_date: e.target.value }))}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Content</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label>Summary</Label>
              <Textarea
                value={form.summary}
                onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
                rows={3}
                placeholder="Brief summary of this post..."
              />
            </div>
            {form.platform === 'internal' && (
              <MarkdownEditor
                value={form.body}
                error={errors.body}
                onChange={(v) => setForm((f) => ({ ...f, body: v }))}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Classification</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <CollectionsSelect
              value={form.collections}
              onChange={(v) => setForm((f) => ({ ...f, collections: v }))}
            />
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
          <Button type="button" variant="outline" onClick={() => navigate('/posts')}>
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
