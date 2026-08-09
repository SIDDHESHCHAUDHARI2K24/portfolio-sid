import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { ClockIcon, TagsIcon } from 'lucide-react'

interface TimelineEntry {
  id: string
  kind: string
  title: string
  status: string
  topic_tags: { id: string; slug: string; label: string }[]
}

export default function Dashboard() {
  const { data: entries = [], isLoading } = useQuery<TimelineEntry[]>({
    queryKey: ['admin', 'timeline'],
    queryFn: () => apiFetch<TimelineEntry[]>('/admin/timeline'),
  })

  const stats = {
    total: entries.length,
    published: entries.filter((e) => e.status === 'published').length,
    draft: entries.filter((e) => e.status === 'draft').length,
    scheduled: entries.filter((e) => e.status === 'scheduled').length,
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Welcome to the portfolio admin panel.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Entries
            </CardTitle>
            <ClockIcon className="size-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{isLoading ? '...' : stats.total}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Published
            </CardTitle>
            <span className="size-2 rounded-full bg-green-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{isLoading ? '...' : stats.published}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Drafts
            </CardTitle>
            <span className="size-2 rounded-full bg-amber-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{isLoading ? '...' : stats.draft}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Scheduled
            </CardTitle>
            <span className="size-2 rounded-full bg-blue-500" />
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{isLoading ? '...' : stats.scheduled}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Quick Links</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Link
            to="/timeline"
            className="flex items-center gap-2 rounded-md border border-border px-4 py-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <ClockIcon className="size-4" />
            Manage Timeline
          </Link>
          <Link
            to="/tag-map"
            className="flex items-center gap-2 rounded-md border border-border px-4 py-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <TagsIcon className="size-4" />
            Manage Tag Map
          </Link>
        </CardContent>
      </Card>
    </div>
  )
}
