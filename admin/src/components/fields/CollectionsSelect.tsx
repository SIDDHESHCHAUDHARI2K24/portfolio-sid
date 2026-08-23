import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

const COLLECTIONS = [
  { value: 'tech_rabbithole', label: 'Tech Rabbithole' },
  { value: 'how_i_use_ai', label: 'How I Use AI' },
  { value: 'vc_for_founders', label: 'VC for Founders' },
]

interface CollectionsSelectProps {
  value: string[]
  onChange: (values: string[]) => void
}

export function CollectionsSelect({ value, onChange }: CollectionsSelectProps) {
  const toggle = (coll: string) => {
    if (value.includes(coll)) {
      onChange(value.filter((c) => c !== coll))
    } else {
      onChange([...value, coll])
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <Label className="text-xs text-muted-foreground">Collections</Label>
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {COLLECTIONS.map((c) => (
          <label key={c.value} className="flex items-center gap-1.5 text-sm">
            <Checkbox
              checked={value.includes(c.value)}
              onChange={() => toggle(c.value)}
            />
            {c.label}
          </label>
        ))}
      </div>
    </div>
  )
}
