import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'

interface OverviewIntroAdmin {
  id: string
  audience: string
  headline: string
  body: string
  hero_image_key: string | null
  cta_label: string | null
  cta_url: string | null
  created_at: string
  updated_at: string
  status: string
  publish_at: string | null
  published_at: string | null
}

const audienceLabels: Record<string, string> = {
  default: 'Default',
  recruiters: 'Recruiters',
  techies: 'Techies',
  investors: 'Investors',
  founders: 'Founders',
  personal: 'Personal',
}

const statusColors: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'secondary',
  scheduled: 'outline',
  published: 'default',
}

export default function OverviewList() {
  const queryClient = useQueryClient()

  const { data: intros = [], isLoading } = useQuery<OverviewIntroAdmin[]>({
    queryKey: ['admin', 'overview'],
    queryFn: () => apiFetch<OverviewIntroAdmin[]>('/admin/overview'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/overview/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'overview'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading overview...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Overview</h1>
        <Link to="/overview/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Intro
          </Button>
        </Link>
      </div>

      {intros.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No overview intros found.{' '}
            <Link to="/overview/new" className="text-primary underline">
              Create one
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Audience</th>
                <th className="px-4 py-3 text-left font-medium">Headline</th>
                <th className="px-4 py-3 text-left font-medium">CTA</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {intros.map((intro) => (
                <tr key={intro.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="capitalize">
                      {audienceLabels[intro.audience] ?? intro.audience}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 font-medium max-w-xs truncate">{intro.headline}</td>
                  <td className="px-4 py-3 text-muted-foreground max-w-[200px] truncate">
                    {intro.cta_label || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={statusColors[intro.status] ?? 'secondary'} className="capitalize">
                      {intro.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/overview/${intro.id}/edit`}>
                        <Button variant="ghost" size="icon-sm" title="Edit">
                          <PencilIcon className="size-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete intro for "${audienceLabels[intro.audience] ?? intro.audience}"?`)) {
                            deleteMutation.mutate(intro.id)
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
