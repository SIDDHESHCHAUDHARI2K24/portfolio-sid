import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon, FilterIcon } from 'lucide-react'
import { useState } from 'react'

interface TagRef {
  id: string
  slug: string
  label: string
}

interface Post {
  id: string
  title: string
  summary: string | null
  url: string
  platform: string
  published_date: string | null
  collections: string[]
  sort_order: number
  created_at: string
  updated_at: string
  topic_tags: TagRef[]
  audience_override: string[] | null
  status: string
  publish_at: string | null
  published_at: string | null
}

const statusColors: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'secondary',
  scheduled: 'outline',
  published: 'default',
}

const platformLabels: Record<string, string> = {
  substack: 'Substack',
  medium: 'Medium',
  youtube: 'YouTube',
  other: 'Other',
}

const collectionLabels: Record<string, string> = {
  tech_rabbithole: 'Tech Rabbithole',
  how_i_use_ai: 'How I Use AI',
  vc_for_founders: 'VC for Founders',
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function PostList() {
  const queryClient = useQueryClient()
  const [platformFilter, setPlatformFilter] = useState<string | null>(null)

  const { data: posts = [], isLoading } = useQuery<Post[]>({
    queryKey: ['admin', 'posts'],
    queryFn: () => apiFetch<Post[]>('/admin/posts'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/posts/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'posts'] })
    },
  })

  const filtered = platformFilter
    ? posts.filter((p) => p.platform === platformFilter)
    : posts

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading posts...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Posts</h1>
        <Link to="/posts/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Post
          </Button>
        </Link>
      </div>

      <div className="flex items-center gap-2">
        <FilterIcon className="size-4 text-muted-foreground" />
        <select
          value={platformFilter ?? ''}
          onChange={(e) => setPlatformFilter(e.target.value || null)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:border-ring"
        >
          <option value="">All platforms</option>
          <option value="substack">Substack</option>
          <option value="medium">Medium</option>
          <option value="youtube">YouTube</option>
          <option value="other">Other</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No posts found.{' '}
            <Link to="/posts/new" className="text-primary underline">
              Create one
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Title</th>
                <th className="px-4 py-3 text-left font-medium">Platform</th>
                <th className="px-4 py-3 text-left font-medium">Collections</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Published Date</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((post) => (
                <tr key={post.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{post.title}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="capitalize">
                      {platformLabels[post.platform] ?? post.platform}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {post.collections.map((c) => (
                        <Badge key={c} variant="secondary" className="text-xs">
                          {collectionLabels[c] ?? c}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={statusColors[post.status] ?? 'secondary'} className="capitalize">
                      {post.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(post.published_date)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/posts/${post.id}/edit`}>
                        <Button variant="ghost" size="icon-sm" title="Edit">
                          <PencilIcon className="size-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete "${post.title}"?`)) {
                            deleteMutation.mutate(post.id)
                          }
                        }}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2Icon className="size-4 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
