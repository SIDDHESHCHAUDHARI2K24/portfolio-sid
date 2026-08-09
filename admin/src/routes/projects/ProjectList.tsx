import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'
import type { Project } from './types'

const statusColors: Record<string, 'default' | 'secondary' | 'outline'> = {
  draft: 'secondary',
  scheduled: 'outline',
  published: 'default',
}

export default function ProjectList() {
  const queryClient = useQueryClient()

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ['admin', 'projects'],
    queryFn: () => apiFetch<Project[]>('/admin/projects'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/projects/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'projects'] })
    },
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading projects...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Projects</h1>
        <Link to="/projects/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Project
          </Button>
        </Link>
      </div>

      {projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No projects found.{' '}
            <Link to="/projects/new" className="text-primary underline">
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
                <th className="px-4 py-3 text-left font-medium">Slug</th>
                <th className="px-4 py-3 text-left font-medium">Tags</th>
                <th className="px-4 py-3 text-left font-medium">Attachments</th>
                <th className="px-4 py-3 text-left font-medium">Status</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id} className="border-b border-border hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{project.title}</td>
                  <td className="px-4 py-3 text-muted-foreground">{project.slug}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-0.5">
                      {project.topic_tags.map((t) => (
                        <Badge key={t.slug} variant="outline" className="text-xs">
                          {t.label}
                        </Badge>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {project.attachments.length}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={statusColors[project.status] ?? 'secondary'} className="capitalize">
                      {project.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Link to={`/projects/${project.id}/edit`}>
                        <Button variant="ghost" size="icon-sm" title="Edit">
                          <PencilIcon className="size-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete "${project.title}"?`)) {
                            deleteMutation.mutate(project.id)
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
