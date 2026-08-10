import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select } from '@/components/ui/select'
import { DownloadIcon, ExternalLinkIcon, MailCheckIcon, EyeIcon } from 'lucide-react'
import { useState } from 'react'

interface Submission {
  id: string
  form_type: string
  payload: Record<string, unknown>
  consent_given: boolean
  consent_text: string
  submitter_email: string | null
  ip_address: string | null
  user_agent: string | null
  is_read: boolean
  created_at: string
}

const FORM_TYPE_LABELS: Record<string, string> = {
  contact: 'Contact',
  dealflow: 'Dealflow',
}

export default function FormsList() {
  const queryClient = useQueryClient()
  const [typeFilter, setTypeFilter] = useState('')
  const [readFilter, setReadFilter] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  const params = new URLSearchParams()
  if (typeFilter) params.set('form_type', typeFilter)
  if (readFilter) params.set('is_read', readFilter)
  const queryStr = params.toString() ? `?${params.toString()}` : ''

  const { data: items = [], isLoading } = useQuery<Submission[]>({
    queryKey: ['admin', 'forms', typeFilter, readFilter],
    queryFn: () => apiFetch<Submission[]>(`/admin/forms${queryStr}`),
  })

  const toggleRead = useMutation({
    mutationFn: ({ id, is_read }: { id: string; is_read: boolean }) =>
      apiFetch(`/admin/forms/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ is_read: !is_read }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'forms'] })
    },
  })

  const handleExport = () => {
    const exportParams = new URLSearchParams()
    if (typeFilter) exportParams.set('form_type', typeFilter)
    window.open(`/api/v1/admin/forms/export/csv${exportParams.toString() ? `?${exportParams.toString()}` : ''}`, '_blank')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading submissions...</p>
      </div>
    )
  }

  const unreadCount = items.filter((s) => !s.is_read).length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Form Submissions</h1>
          {unreadCount > 0 && (
            <p className="text-sm text-muted-foreground mt-1">
              {unreadCount} unread
            </p>
          )}
        </div>
        <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExport}>
          <DownloadIcon className="size-4" />
          Export CSV
        </Button>
      </div>

      <div className="flex gap-3">
        <Select
          value={typeFilter}
          onValueChange={(v) => setTypeFilter(v === 'all' ? '' : v)}
        >
          <Select.Trigger className="w-40">
            <Select.Value placeholder="All types" />
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="all">All Types</Select.Item>
            <Select.Item value="contact">Contact</Select.Item>
            <Select.Item value="dealflow">Dealflow</Select.Item>
          </Select.Content>
        </Select>

        <Select
          value={readFilter}
          onValueChange={(v) => setReadFilter(v === 'all' ? '' : v)}
        >
          <Select.Trigger className="w-40">
            <Select.Value placeholder="All status" />
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="all">All Status</Select.Item>
            <Select.Item value="true">Read</Select.Item>
            <Select.Item value="false">Unread</Select.Item>
          </Select.Content>
        </Select>
      </div>

      {items.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center text-muted-foreground">
          No submissions yet.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Type</th>
                <th className="px-4 py-3 text-left font-medium">From</th>
                <th className="px-4 py-3 text-left font-medium">Date</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <>
                  <tr
                    key={item.id}
                    className={`border-b border-border hover:bg-muted/30 cursor-pointer ${!item.is_read ? 'bg-primary/5' : ''}`}
                    onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                  >
                    <td className="px-4 py-3">
                      <Badge variant={item.form_type === 'dealflow' ? 'secondary' : 'default'}>
                        {FORM_TYPE_LABELS[item.form_type] ?? item.form_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-medium">
                      {item.submitter_email || (item.payload as any)?.email || '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(item.created_at).toLocaleDateString()}{' '}
                      {new Date(item.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3">
                      {item.is_read ? (
                        <Badge variant="outline">Read</Badge>
                      ) : (
                        <Badge variant="default" className="bg-primary text-primary-foreground">
                          Unread
                        </Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          title={item.is_read ? 'Mark unread' : 'Mark read'}
                          onClick={() => toggleRead.mutate({ id: item.id, is_read: item.is_read })}
                          disabled={toggleRead.isPending}
                        >
                          {item.is_read ? (
                            <EyeIcon className="size-4" />
                          ) : (
                            <MailCheckIcon className="size-4" />
                          )}
                        </Button>
                      </div>
                    </td>
                  </tr>
                  {expanded === item.id && (
                    <tr key={`${item.id}-detail`} className="border-b border-border bg-muted/20">
                      <td colSpan={5} className="px-6 py-4">
                        <DetailView item={item} />
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function DetailView({ item }: { item: Submission }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-2">
          Payload
        </h3>
        <table className="w-full max-w-lg text-sm">
          <tbody>
            {Object.entries(item.payload).map(([key, value]) => (
              <tr key={key} className="border-b border-border last:border-0">
                <td className="py-1.5 pr-4 font-medium text-muted-foreground capitalize whitespace-nowrap">
                  {key.replace(/_/g, ' ')}
                </td>
                <td className="py-1.5">{String(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-2">
          Consent
        </h3>
        <p className="text-sm">
          <span className={item.consent_given ? 'text-green-600' : 'text-destructive'}>
            {item.consent_given ? 'Given' : 'Not given'}
          </span>
        </p>
        <p className="text-sm text-muted-foreground mt-1 italic">
          &ldquo;{item.consent_text}&rdquo;
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 max-w-lg">
        <div>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
            IP Address
          </h3>
          <p className="text-sm font-mono">{item.ip_address || '—'}</p>
        </div>
        <div>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
            Submission ID
          </h3>
          <p className="text-sm font-mono">{item.id}</p>
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-1">
          User Agent
        </h3>
        <p className="text-sm font-mono break-all text-muted-foreground">
          {item.user_agent || '—'}
        </p>
      </div>
    </div>
  )
}
