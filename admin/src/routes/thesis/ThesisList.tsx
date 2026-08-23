import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'

interface TagRef {
  id: string
  slug: string
  label: string
}

interface ThesisEntry {
  id: string
  title: string
  summary: string | null
  drive_url: string
  published_date: string
  sort_order: number
  status: string
  publish_at: string | null
  published_at: string | null
  audience_override: string[] | null
  topic_tags: TagRef[]
  created_at: string
  updated_at: string
}

const statusColors: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'secondary',
  scheduled: 'outline',
  published: 'default',
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function ThesisList() {
  const queryClient = useQueryClient()

  const { data: entries = [], isLoading } = useQuery<ThesisEntry[]>({
    queryKey: ['admin', 'thesis'],
    queryFn: () => apiFetch<ThesisEntry[]>('/admin/thesis'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/thesis/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'thesis'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading thesis...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Thesis</h1>
        <Link to="/thesis/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Thesis
          </Button>
        </Link>
      </div>

      {entries.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No thesis entries found.{' '}
            <Link to="/thesis/new" className="text-primary underline">
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
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-left font-medium">Published Date</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{entry.title}</td>
                  <td className="px-4 py-3">
                    <Badge variant={statusColors[entry.status] ?? 'secondary'} className="capitalize">
                      {entry.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(entry.published_date)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/thesis/${entry.id}/edit`}>
                        <Button variant="ghost" size="icon-sm" title="Edit">
                          <PencilIcon className="size-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete "${entry.title}"?`)) {
                            deleteMutation.mutate(entry.id)
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
