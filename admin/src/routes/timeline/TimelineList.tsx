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

interface TimelineEntry {
  id: string
  kind: string
  title: string
  organisation: string
  location: string | null
  start_date: string
  end_date: string | null
  summary: string | null
  highlights: string[] | null
  external_url: string | null
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

function kindLabel(kind: string) {
  return kind === 'education' ? 'Education' : kind === 'experience' ? 'Experience' : kind
}

export default function TimelineList() {
  const queryClient = useQueryClient()
  const [kindFilter, setKindFilter] = useState<string | null>(null)

  const { data: entries = [], isLoading } = useQuery<TimelineEntry[]>({
    queryKey: ['admin', 'timeline'],
    queryFn: () => apiFetch<TimelineEntry[]>('/admin/timeline'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/timeline/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'timeline'] })
    },
  })

  const filtered = kindFilter
    ? entries.filter((e) => e.kind === kindFilter)
    : entries

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading timeline...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Timeline</h1>
        <Link to="/timeline/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Entry
          </Button>
        </Link>
      </div>

      <div className="flex items-center gap-2">
        <FilterIcon className="size-4 text-muted-foreground" />
        <select
          value={kindFilter ?? ''}
          onChange={(e) => setKindFilter(e.target.value || null)}
          className="h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:border-ring"
        >
          <option value="">All kinds</option>
          <option value="education">Education</option>
          <option value="experience">Experience</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No timeline entries found.{' '}
            <Link to="/timeline/new" className="text-primary underline">
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
                <th className="px-4 py-3 text-left font-medium">Kind</th>
                <th className="px-4 py-3 text-left font-medium">Organisation</th>
                <th className="px-4 py-3 text-left font-medium">Dates</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{entry.title}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="capitalize">
                      {kindLabel(entry.kind)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{entry.organisation}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(entry.start_date)} — {entry.end_date ? formatDate(entry.end_date) : 'Present'}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={statusColors[entry.status] ?? 'secondary'} className="capitalize">
                      {entry.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/timeline/${entry.id}/edit`}>
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
