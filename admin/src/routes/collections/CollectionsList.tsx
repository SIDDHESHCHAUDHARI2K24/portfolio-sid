import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'
import { useMemo } from 'react'

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

const KIND_LABELS: Record<string, string> = {
  book: 'Book',
  anime: 'Anime',
  manhwa: 'Manhwa',
}

const STATUS_LABELS: Record<string, string> = {
  reading: 'Reading',
  completed: 'Completed',
  want_to_read: 'Want to Read',
}

export default function CollectionsList() {
  const queryClient = useQueryClient()

  const { data: items = [], isLoading } = useQuery<Item[]>({
    queryKey: ['admin', 'collections'],
    queryFn: () => apiFetch<Item[]>('/admin/collections'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/collections/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'collections'] })
    },
  })

  const grouped = useMemo(() => {
    const map: Record<string, Item[]> = { book: [], anime: [], manhwa: [] }
    for (const item of items) {
      if (map[item.kind]) map[item.kind].push(item)
    }
    return map
  }, [items])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading collections...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Collections</h1>
        <Link to="/collections/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Item
          </Button>
        </Link>
      </div>

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No collection items yet.{' '}
            <Link to="/collections/new" className="text-primary underline">
              Add one
            </Link>
          </CardContent>
        </Card>
      ) : (
        ['book', 'anime', 'manhwa'].map((kind) => {
          const entries = grouped[kind]
          if (!entries || entries.length === 0) return null
          return (
            <div key={kind}>
              <h2 className="text-sm font-semibold uppercase text-muted-foreground mb-2">
                {KIND_LABELS[kind] ?? kind}
              </h2>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="px-4 py-3 text-left font-medium">Title</th>
                      <th className="px-4 py-3 text-left font-medium">Creator</th>
                      <th className="px-4 py-3 text-left font-medium">Section</th>
                      <th className="px-4 py-3 text-left font-medium">Status</th>
                      <th className="px-4 py-3 text-left font-medium">Publish</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((item) => (
                      <tr key={item.id} className="border-b border-border hover:bg-muted/30">
                        <td className="px-4 py-3 font-medium">{item.title}</td>
                        <td className="px-4 py-3 text-muted-foreground">{item.creator ?? '—'}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {item.section ??
                            (item.kind === 'book' ? '—' : 'N/A')}
                        </td>
                        <td className="px-4 py-3">
                          {item.status ? (
                            <Badge variant="outline">
                              {STATUS_LABELS[item.status] ?? item.status}
                            </Badge>
                          ) : (
                            '—'
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={item.status_ === 'published' ? 'default' : 'secondary'}>
                            {item.status_}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <Link to={`/collections/${item.id}/edit`}>
                              <Button variant="ghost" size="icon-sm" title="Edit">
                                <PencilIcon className="size-4" />
                              </Button>
                            </Link>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              title="Delete"
                              onClick={() => {
                                if (confirm(`Delete "${item.title}"?`)) {
                                  deleteMutation.mutate(item.id)
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
            </div>
          )
        })
      )}
    </div>
  )
}
