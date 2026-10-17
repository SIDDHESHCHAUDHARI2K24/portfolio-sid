import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import type { FormState } from './postFormUtils'

interface Props {
  form: FormState
  errors: Record<string, string>
  onUrlChange: (value: string) => void
  onSlugChange: (value: string) => void
}

/** Internal posts have a slug (served at /writing/<slug>); every other platform has a url. */
export function LinkFields({ form, errors, onUrlChange, onSlugChange }: Props) {
  if (form.platform === 'internal') {
    return (
      <div className="sm:col-span-2">
        <Label>Slug</Label>
        <Input
          value={form.slug}
          onChange={(e) => onSlugChange(e.target.value)}
          className={cn(errors.slug && 'border-destructive')}
          placeholder="my-first-article"
        />
        <p className="text-xs text-muted-foreground">
          Published at /writing/{form.slug.trim().toLowerCase() || '<slug>'}
        </p>
        {errors.slug && <p className="text-sm text-destructive">{errors.slug}</p>}
      </div>
    )
  }
  return (
    <div className="sm:col-span-2">
      <Label>URL</Label>
      <Input
        value={form.url}
        onChange={(e) => onUrlChange(e.target.value)}
        className={cn(errors.url && 'border-destructive')}
        placeholder="https://example.com/my-post"
      />
      {errors.url && <p className="text-sm text-destructive">{errors.url}</p>}
    </div>
  )
}
