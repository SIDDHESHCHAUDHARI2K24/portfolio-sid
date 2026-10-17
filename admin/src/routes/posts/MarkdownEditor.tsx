import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'

interface Props {
  value: string
  onChange: (value: string) => void
  error?: string
}

/** Markdown textarea with a live preview that mirrors the site renderer (no raw HTML). */
export function MarkdownEditor({ value, onChange, error }: Props) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div>
        <Label>Body (markdown)</Label>
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={20}
          className={cn('font-mono', error && 'border-destructive')}
          placeholder={'# Heading\n\nWrite your article in markdown...'}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
      <div>
        <Label>Preview</Label>
        <div
          data-testid="body-preview"
          className="article-body min-h-40 max-h-[32rem] overflow-y-auto rounded-md border border-input p-4"
        >
          {value.trim() ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
          ) : (
            <p className="text-muted-foreground">Nothing to preview yet.</p>
          )}
        </div>
      </div>
    </div>
  )
}
