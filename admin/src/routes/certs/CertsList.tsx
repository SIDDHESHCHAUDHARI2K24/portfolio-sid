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

interface Certification {
  id: string
  title: string
  issuer: string
  kind: string
  issued_date: string
  expires_date: string | null
  credential_url: string | null
  file_key: string | null
  file_type: string | null
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

export default function CertsList() {
  const queryClient = useQueryClient()

  const { data: certs = [], isLoading } = useQuery<Certification[]>({
    queryKey: ['admin', 'certifications'],
    queryFn: () => apiFetch<Certification[]>('/admin/certifications'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/certifications/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'certifications'] })
    },
  })

  const technical = certs.filter((c) => c.kind === 'technical')
  const business = certs.filter((c) => c.kind === 'business')

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading certifications...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Certifications</h1>
        <Link to="/certs/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Certification
          </Button>
        </Link>
      </div>

      {certs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No certifications yet.{' '}
            <Link to="/certs/new" className="text-primary underline">
              Add one
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          {[
            { label: 'Technical', items: technical },
            { label: 'Business', items: business },
          ].map(({ label, items }) => {
            if (items.length === 0) return null
            return (
              <div key={label}>
                <h2 className="text-sm font-semibold uppercase text-muted-foreground mb-2">
                  {label}
                </h2>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border bg-muted/50">
                        <th className="px-4 py-3 text-left font-medium">Title</th>
                        <th className="px-4 py-3 text-left font-medium">Issuer</th>
                        <th className="px-4 py-3 text-left font-medium">Issued</th>
                        <th className="px-4 py-3 text-left font-medium">Status</th>
                        <th className="px-4 py-3 text-right font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((cert) => (
                        <tr key={cert.id} className="border-b border-border hover:bg-muted/30">
                          <td className="px-4 py-3 font-medium">{cert.title}</td>
                          <td className="px-4 py-3 text-muted-foreground">{cert.issuer}</td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {formatDate(cert.issued_date)}
                          </td>
                          <td className="px-4 py-3">
                            <Badge
                              variant={statusColors[cert.status] ?? 'secondary'}
                              className="capitalize"
                            >
                              {cert.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex justify-end gap-1">
                              <Link to={`/certs/${cert.id}/edit`}>
                                <Button variant="ghost" size="icon-sm" title="Edit">
                                  <PencilIcon className="size-4" />
                                </Button>
                              </Link>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                title="Delete"
                                onClick={() => {
                                  if (confirm(`Delete "${cert.title}"?`)) {
                                    deleteMutation.mutate(cert.id)
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
          })}
        </>
      )}
    </div>
  )
}
