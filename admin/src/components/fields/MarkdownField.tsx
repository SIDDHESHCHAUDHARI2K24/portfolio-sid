import { useState } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface MarkdownFieldProps {
  value: string
  onChange: (value: string) => void
  label?: string
  error?: string
  rows?: number
}

function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="bg-muted px-1 rounded text-sm">$1</code>')
    .replace(/^### (.+)$/gm, '<h3 class="text-lg font-semibold mt-2 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="text-xl font-semibold mt-3 mb-1">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>')
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n\n/g, '</p><p class="mb-2">')
    .replace(/\n/g, '<br/>')
}

export function MarkdownField({ value, onChange, label, error, rows = 6 }: MarkdownFieldProps) {
  const [showPreview, setShowPreview] = useState(false)

  return (
    <div className="flex flex-col gap-1.5">
      {label && <Label className="text-sm">{label}</Label>}
      <div className="flex gap-2 mb-1">
        <button
          type="button"
          className={cn(
            'text-xs px-2 py-0.5 rounded-sm border border-border',
            !showPreview && 'bg-accent text-accent-foreground',
          )}
          onClick={() => setShowPreview(false)}
        >
          Edit
        </button>
        <button
          type="button"
          className={cn(
            'text-xs px-2 py-0.5 rounded-sm border border-border',
            showPreview && 'bg-accent text-accent-foreground',
          )}
          onClick={() => setShowPreview(true)}
        >
          Preview
        </button>
      </div>
      {showPreview ? (
        <div
          className="min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm"
          dangerouslySetInnerHTML={{
            __html: value ? `<p class="mb-2">${renderMarkdown(value)}</p>` : '<span class="text-muted-foreground">Nothing to preview</span>',
          }}
        />
      ) : (
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          placeholder="Markdown supported: **bold**, *italic*, `code`, # headings, - lists"
        />
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
