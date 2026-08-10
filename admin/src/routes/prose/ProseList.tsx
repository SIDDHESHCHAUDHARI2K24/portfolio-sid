import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'
import { useMemo } from 'react'

interface Page {
  id: string
  slug: string
  title: string
  group: string
  status: string
  cta_label: string | null
  sort_order: number
}

const GROUP_LABELS: Record<string, string> = {
  hobbies: 'Hobbies',
  work_views: 'Work Views',
  investor_intro: 'Investor Intro',
}

export default function ProseList() {
  const queryClient = useQueryClient()

  const { data: pages = [], isLoading } = useQuery<Page[]>({
    queryKey: ['admin', 'prose'],
    queryFn: () => apiFetch<Page[]>('/admin/prose'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/prose/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'prose'] })
    },
  })

  const grouped = useMemo(() => {
    const map: Record<string, Page[]> = { hobbies: [], work_views: [], investor_intro: [] }
    for (const p of pages) {
      if (map[p.group]) map[p.group].push(p)
    }
    return map
  }, [pages])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading prose pages...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Prose Pages</h1>
        <Link to="/prose/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Page
          </Button>
        </Link>
      </div>

      {pages.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No prose pages yet.{' '}
            <Link to="/prose/new" className="text-primary underline">
              Create one
            </Link>
          </CardContent>
        </Card>
      ) : (
        ['hobbies', 'work_views', 'investor_intro'].map((group) => {
          const items = grouped[group]
          if (!items || items.length === 0) return null
          return (
            <div key={group}>
              <h2 className="text-sm font-semibold uppercase text-muted-foreground mb-2">
                {GROUP_LABELS[group] ?? group}
              </h2>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="px-4 py-3 text-left font-medium">Title</th>
                      <th className="px-4 py-3 text-left font-medium">Slug</th>
                      <th className="px-4 py-3 text-left font-medium">CTA</th>
                      <th className="px-4 py-3 text-left font-medium">Status</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((page) => (
                      <tr key={page.id} className="border-b border-border hover:bg-muted/30">
                        <td className="px-4 py-3 font-medium">{page.title}</td>
                        <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                          /{page.slug}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {page.cta_label ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={page.status === 'published' ? 'default' : 'secondary'}>
                            {page.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <Link to={`/prose/${page.id}/edit`}>
                              <Button variant="ghost" size="icon-sm" title="Edit">
                                <PencilIcon className="size-4" />
                              </Button>
                            </Link>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              title="Delete"
                              onClick={() => {
                                if (confirm(`Delete "${page.title}"?`)) {
                                  deleteMutation.mutate(page.id)
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
