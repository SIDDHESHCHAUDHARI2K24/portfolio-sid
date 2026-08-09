import { useQuery } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { Badge } from '@/components/ui/badge'

interface Tag {
  id: string
  slug: string
  label: string
}

interface TagSelectProps {
  value: string[]
  onChange: (slugs: string[]) => void
  error?: string
}

export function TagSelect({ value, onChange, error }: TagSelectProps) {
  const { data: allTags = [], isLoading } = useQuery<Tag[]>({
    queryKey: ['tags'],
    queryFn: () => apiFetch<Tag[]>('/admin/tags'),
  })

  const selectedTags = allTags.filter((t) => value.includes(t.slug))
  const availableTags = allTags.filter((t) => !value.includes(t.slug))

  return (
    <div className="flex flex-col gap-2">
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading tags...</p>
      ) : (
        <>
          <div className="flex flex-wrap gap-1">
            {selectedTags.map((tag) => (
              <Badge key={tag.id} variant="secondary" className="flex items-center gap-1">
                {tag.label}
                <button
                  type="button"
                  onClick={() => onChange(value.filter((s) => s !== tag.slug))}
                  className="ml-0.5 rounded-full p-0.5 hover:bg-muted"
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
          </div>
          {availableTags.length > 0 && (
            <select
              value=""
              onChange={(e) => {
                if (e.target.value) {
                  onChange([...value, e.target.value])
                }
              }}
              className="h-8 w-full rounded-md border border-input bg-background px-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <option value="">Add tag...</option>
              {availableTags.map((tag) => (
                <option key={tag.id} value={tag.slug}>
                  {tag.label}
                </option>
              ))}
            </select>
          )}
        </>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
