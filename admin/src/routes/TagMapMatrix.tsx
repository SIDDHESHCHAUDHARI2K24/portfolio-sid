import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { PencilIcon, Trash2Icon, PlusIcon, XIcon, SaveIcon } from 'lucide-react'

interface Tag {
  id: string
  slug: string
  label: string
}

const AUDIENCES = ['recruiters', 'techies', 'investors', 'founders', 'personal']

type RelevanceMap = Record<string, string[]>

export default function TagMapMatrix() {
  const queryClient = useQueryClient()
  const [editingTagId, setEditingTagId] = useState<string | null>(null)
  const [editingTagLabel, setEditingTagLabel] = useState('')
  const [newTagSlug, setNewTagSlug] = useState('')
  const [newTagLabel, setNewTagLabel] = useState('')
  const [matrixError, setMatrixError] = useState('')
  const [tagError, setTagError] = useState('')

  const { data: tags = [], isLoading: tagsLoading } = useQuery<Tag[]>({
    queryKey: ['tags'],
    queryFn: () => apiFetch<Tag[]>('/admin/tags'),
  })

  const { data: tagMap = {}, isLoading: mapLoading } = useQuery<RelevanceMap>({
    queryKey: ['relevance-map'],
    queryFn: () => apiFetch<RelevanceMap>('/admin/relevance/map'),
  })

  const saveMutation = useMutation({
    mutationFn: (mapping: RelevanceMap) =>
      apiFetch('/admin/relevance/map', {
        method: 'PUT',
        body: JSON.stringify({ mapping }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['relevance-map'] })
      setMatrixError('')
    },
    onError: (err) => {
      setMatrixError(err instanceof ApiError ? err.message : 'Failed to save')
    },
  })

  const createTagMutation = useMutation({
    mutationFn: (data: { slug: string; label: string }) =>
      apiFetch('/admin/tags', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      setNewTagSlug('')
      setNewTagLabel('')
      setTagError('')
    },
    onError: (err) => {
      setTagError(err instanceof ApiError ? err.message : 'Failed to create tag')
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, label }: { id: string; label: string }) =>
      apiFetch(`/admin/tags/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ label }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      setEditingTagId(null)
      setTagError('')
    },
    onError: (err) => {
      setTagError(err instanceof ApiError ? err.message : 'Failed to rename tag')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/tags/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] })
      queryClient.invalidateQueries({ queryKey: ['relevance-map'] })
      setTagError('')
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        if (err.status === 422) {
          setTagError('Cannot delete tag: it is in use by content entries or the relevance map.')
        } else {
          setTagError(err.message)
        }
      } else {
        setTagError('Failed to delete tag')
      }
    },
  })

  const createTag = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTagSlug.trim() || !newTagLabel.trim()) return
    createTagMutation.mutate({
      slug: newTagSlug.trim().toLowerCase().replace(/\s+/g, '-'),
      label: newTagLabel.trim(),
    })
  }

  const handleCheckChange = (tagSlug: string, audience: string, checked: boolean) => {
    const updated = { ...tagMap }
    for (const aud of AUDIENCES) {
      if (!updated[aud]) updated[aud] = []
    }
    const current = new Set(updated[audience])
    if (checked) {
      current.add(tagSlug)
    } else {
      current.delete(tagSlug)
    }
    updated[audience] = Array.from(current)
    saveMutation.mutate(updated)
  }

  const isLoading = tagsLoading || mapLoading

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Audience-Tag Matrix</h1>
      </div>

      {matrixError && (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          {matrixError}
        </div>
      )}

      {/* Matrix */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Relevance Mapping</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading matrix...</p>
          ) : tags.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No topic tags yet. Create some below.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-3 py-2 text-left font-medium">Tag</th>
                    {AUDIENCES.map((aud) => (
                      <th key={aud} className="px-3 py-2 text-center font-medium capitalize">
                        {aud}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {tags.map((tag) => (
                    <tr key={tag.id} className="border-b border-border hover:bg-muted/30">
                      <td className="px-3 py-2.5 font-medium">
                        {tag.label}
                        <span className="ml-1 text-xs text-muted-foreground">#{tag.slug}</span>
                      </td>
                      {AUDIENCES.map((aud) => {
                        const audienceTags = tagMap[aud] ?? []
                        const checked = audienceTags.includes(tag.slug)
                        return (
                          <td key={aud} className="px-3 py-2.5 text-center">
                            <Checkbox
                              checked={checked}
                              onChange={(e) => {
                                const input = e.target as HTMLInputElement
                                handleCheckChange(tag.slug, aud, input.checked)
                              }}
                              disabled={saveMutation.isPending}
                            />
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {saveMutation.isPending && (
            <p className="mt-2 text-sm text-muted-foreground">Saving changes...</p>
          )}
        </CardContent>
      </Card>

      {/* Tag Management */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tag Management</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {tagError && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {tagError}
            </div>
          )}

          {/* Create tag */}
          <form onSubmit={createTag} className="flex items-end gap-2">
            <div className="flex-1">
              <label className="text-xs text-muted-foreground">Slug</label>
              <Input
                value={newTagSlug}
                onChange={(e) => setNewTagSlug(e.target.value)}
                placeholder="ai"
                className="h-8"
                disabled={createTagMutation.isPending}
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-muted-foreground">Label</label>
              <Input
                value={newTagLabel}
                onChange={(e) => setNewTagLabel(e.target.value)}
                placeholder="AI"
                className="h-8"
                disabled={createTagMutation.isPending}
              />
            </div>
            <Button
              type="submit"
              size="sm"
              className="gap-1"
              disabled={createTagMutation.isPending || !newTagSlug.trim() || !newTagLabel.trim()}
            >
              <PlusIcon className="size-3" />
              Create
            </Button>
          </form>

          {/* Existing tags */}
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <div key={tag.id} className="flex items-center gap-1">
                {editingTagId === tag.id ? (
                  <div className="flex items-center gap-1 rounded-md border border-input bg-background px-2 py-1">
                    <Input
                      value={editingTagLabel}
                      onChange={(e) => setEditingTagLabel(e.target.value)}
                      className="h-7 w-32 border-0 p-0 shadow-none"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          renameMutation.mutate({ id: tag.id, label: editingTagLabel })
                        } else if (e.key === 'Escape') {
                          setEditingTagId(null)
                        }
                      }}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => renameMutation.mutate({ id: tag.id, label: editingTagLabel })}
                      className="rounded p-0.5 hover:bg-accent"
                    >
                      <SaveIcon className="size-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingTagId(null)}
                      className="rounded p-0.5 hover:bg-accent"
                    >
                      <XIcon className="size-3" />
                    </button>
                  </div>
                ) : (
                  <Badge variant="secondary" className="flex items-center gap-1 pr-1">
                    {tag.label}
                    <button
                      type="button"
                      onClick={() => {
                        setEditingTagId(tag.id)
                        setEditingTagLabel(tag.label)
                      }}
                      className="rounded p-0.5 hover:bg-muted"
                      title="Rename"
                    >
                      <PencilIcon className="size-3" />
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (confirm(`Delete tag "${tag.label}"?`)) {
                          deleteMutation.mutate(tag.id)
                        }
                      }}
                      className="rounded p-0.5 hover:bg-muted"
                      title="Delete"
                    >
                      <Trash2Icon className="size-3 text-destructive" />
                    </button>
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
