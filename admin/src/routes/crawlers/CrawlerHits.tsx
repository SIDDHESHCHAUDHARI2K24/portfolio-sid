import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useState } from 'react'

interface CrawlerHit {
  id: string
  user_agent: string
  path: string
  ip_hash: string
  agent_label: string | null
  timestamp: string
}

interface CrawlerSummaryRow {
  agent_label: string | null
  week_start: string
  count: number
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function truncateIpHash(hash: string) {
  return hash.slice(0, 12) + '...'
}

const AGENT_OPTIONS = [
  'GPTBot',
  'ClaudeBot',
  'PerplexityBot',
  'CCBot',
  'Google-Extended',
  'Bytespider',
]

export default function CrawlerHits() {
  const [agentFilter, setAgentFilter] = useState<string | null>(null)

  const params = new URLSearchParams()
  if (agentFilter) params.set('agent_label', agentFilter)

  const { data: hits = [], isLoading } = useQuery<CrawlerHit[]>({
    queryKey: ['admin', 'crawlers', 'hits', agentFilter],
    queryFn: () =>
      apiFetch<CrawlerHit[]>(
        `/admin/crawlers/hits?${params.toString()}`,
      ),
  })

  const { data: summary = [] } = useQuery<CrawlerSummaryRow[]>({
    queryKey: ['admin', 'crawlers', 'summary'],
    queryFn: () => apiFetch<CrawlerSummaryRow[]>('/admin/crawlers/summary'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading crawler hits...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Crawler Analytics</h1>

      <Card>
        <CardContent className="pt-6">
          <div className="rounded-md border border-yellow-500/30 bg-yellow-500/5 px-4 py-3 text-sm text-yellow-700 dark:text-yellow-400">
            <strong>Undercount caveat:</strong> Crawler hits are undercounted
            by design — edge-cached responses never reach the origin. Read
            this as &ldquo;which crawlers have visited&rdquo;, not &ldquo;how
            many times&rdquo;.
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-3 text-lg font-medium">Per-Agent Weekly Summary</h2>
        {summary.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No crawler data recorded yet.
            </CardContent>
          </Card>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Agent</th>
                  <th className="px-4 py-3 text-left font-medium">Week</th>
                  <th className="px-4 py-3 text-right font-medium">Hits</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-border hover:bg-muted/30"
                  >
                    <td className="px-4 py-3">
                      <Badge variant="outline">
                        {row.agent_label ?? 'Unknown'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {row.week_start}
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {row.count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-medium">Recent Hits</h2>
          <select
            value={agentFilter ?? ''}
            onChange={(e) => setAgentFilter(e.target.value || null)}
            className="h-8 rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:border-ring"
          >
            <option value="">All agents</option>
            {AGENT_OPTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>

        {hits.length === 0 ? (
          <Card>
            <CardContent className="py-8 text-center text-muted-foreground">
              No recent crawler hits.
            </CardContent>
          </Card>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left font-medium">Agent</th>
                  <th className="px-4 py-3 text-left font-medium">Path</th>
                  <th className="px-4 py-3 text-left font-medium">IP Hash</th>
                </tr>
              </thead>
              <tbody>
                {hits.map((hit) => (
                  <tr
                    key={hit.id}
                    className="border-b border-border hover:bg-muted/30"
                  >
                    <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                      {formatDate(hit.timestamp)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">
                        {hit.agent_label ?? 'Unknown'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-mono text-muted-foreground">
                      {hit.path}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                      {truncateIpHash(hit.ip_hash)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
