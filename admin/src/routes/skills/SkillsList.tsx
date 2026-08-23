import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { PlusIcon, PencilIcon, Trash2Icon } from 'lucide-react'
import { useMemo } from 'react'

interface Skill {
  id: string
  name: string
  section: string
  subsection: string | null
  icon_slug: string | null
  icon_key: string | null
  sort_order: number
  created_at: string
  updated_at: string
}

const SECTION_LABELS: Record<string, string> = {
  languages: 'Languages',
  tools: 'Tools & Platforms',
  frameworks: 'Frameworks & Libraries',
  ai: 'AI & Data',
  business: 'Business & Strategy',
}

function cdnPreviewUrl(slug: string): string {
  return `https://cdn.jsdelivr.net/npm/simple-icons@14/icons/${encodeURIComponent(slug)}.svg`
}

export default function SkillsList() {
  const queryClient = useQueryClient()

  const { data: skills = [], isLoading } = useQuery<Skill[]>({
    queryKey: ['admin', 'skills'],
    queryFn: () => apiFetch<Skill[]>('/admin/skills'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch(`/admin/skills/${id}`, { method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'skills'] })
    },
  })

  const grouped = useMemo(() => {
    const map: Record<string, Skill[]> = {}
    for (const s of skills) {
      if (!map[s.section]) map[s.section] = []
      map[s.section].push(s)
    }
    return map
  }, [skills])

  const sections = ['languages', 'tools', 'frameworks', 'ai', 'business']

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading skills...</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Skills</h1>
        <Link to="/skills/new">
          <Button size="sm" className="gap-1.5">
            <PlusIcon className="size-4" />
            New Skill
          </Button>
        </Link>
      </div>

      {skills.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            No skills yet.{' '}
            <Link to="/skills/new" className="text-primary underline">
              Add one
            </Link>
          </CardContent>
        </Card>
      ) : (
        sections.map((section) => {
          const items = grouped[section]
          if (!items || items.length === 0) return null
          return (
            <div key={section}>
              <h2 className="text-sm font-semibold uppercase text-muted-foreground mb-2">
                {SECTION_LABELS[section] ?? section}
              </h2>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50">
                      <th className="px-4 py-3 text-left font-medium">Name</th>
                      <th className="px-4 py-3 text-left font-medium">Subsection</th>
                      <th className="px-4 py-3 text-left font-medium">Icon</th>
                      <th className="px-4 py-3 text-left font-medium">Sort</th>
                      <th className="px-4 py-3 text-right font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((skill) => (
                      <tr key={skill.id} className="border-b border-border hover:bg-muted/30">
                        <td className="px-4 py-3 font-medium">{skill.name}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {skill.subsection ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          {skill.icon_slug ? (
                            <img
                              src={cdnPreviewUrl(skill.icon_slug)}
                              alt=""
                              className="h-5 w-5"
                              onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'
                              }}
                            />
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">{skill.sort_order}</td>
                        <td className="px-4 py-3">
                          <div className="flex justify-end gap-1">
                            <Link to={`/skills/${skill.id}/edit`}>
                              <Button variant="ghost" size="icon-sm" title="Edit">
                                <PencilIcon className="size-4" />
                              </Button>
                            </Link>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              title="Delete"
                              onClick={() => {
                                if (confirm(`Delete "${skill.name}"?`)) {
                                  deleteMutation.mutate(skill.id)
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
