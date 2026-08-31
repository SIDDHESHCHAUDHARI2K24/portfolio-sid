import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'

interface ResumeEntry {
  id: string
  variant: string
  label: string
  file_key: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const VARIANT_LABELS: Record<string, string> = {
  business: 'Business / TPM',
  generic: 'Product Builder',
  vc: 'Venture Capital',
  ai_consultant: 'AI Consultant',
  ai_workflow: 'AI Workflow Engineer',
  product_engineer: 'Product Engineer',
  // legacy fallback
  tech: 'Tech (legacy)',
}

function formatDate(d: string | null) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function variantLabel(variant: string): string {
  return VARIANT_LABELS[variant] ?? variant
}

export default function ResumeList() {
  const queryClient = useQueryClient()

  const { data: entries = [], isLoading } = useQuery<ResumeEntry[]>({
    queryKey: ['admin', 'resumes'],
    queryFn: () => apiFetch<ResumeEntry[]>('/admin/resumes'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/resumes/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'resumes'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading resumes...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Resumes</h1>
        <Link to="/resumes/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Resume
          </Button>
        </Link>
      </div>

      {entries.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No resumes found.{' '}
            <Link to="/resumes/new" className="text-primary underline">
              Create one
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Label</th>
                <th className="px-4 py-3 text-left font-medium">Variant</th>
                <th className="px-4 py-3 text-left font-medium">Active</th>
                <th className="px-4 py-3 text-left font-medium">Updated At</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{entry.label}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" title={entry.variant}>
                      {variantLabel(entry.variant)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={entry.is_active ? 'default' : 'secondary'}>
                      {entry.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDate(entry.updated_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/resumes/${entry.id}/edit`}>
                        <Button variant="ghost" size="icon-sm" title="Edit">
                          <PencilIcon className="size-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete "${entry.label}"?`)) {
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
