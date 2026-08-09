import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

const AUDIENCES = [
  { value: 'recruiters', label: 'Recruiters' },
  { value: 'techies', label: 'Techies' },
  { value: 'investors', label: 'Investors' },
  { value: 'founders', label: 'Founders' },
  { value: 'personal', label: 'Personal' },
]

interface AudienceOverrideSelectProps {
  value: string[] | null
  onChange: (values: string[] | null) => void
}

export function AudienceOverrideSelect({ value, onChange }: AudienceOverrideSelectProps) {
  const selected = value ?? []

  const toggle = (aud: string) => {
    if (selected.includes(aud)) {
      const next = selected.filter((a) => a !== aud)
      onChange(next.length > 0 ? next : null)
    } else {
      onChange([...selected, aud])
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">
        Override audiences (leave empty for tag-based relevance)
      </Label>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {AUDIENCES.map((a) => (
          <label key={a.value} className="flex items-center gap-1.5 text-sm">
            <Checkbox
              checked={selected.includes(a.value)}
              onChange={() => toggle(a.value)}
            />
            {a.label}
          </label>
        ))}
      </div>
    </div>
  )
}
