import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface PublishStatusFieldProps {
  status: string
  publishAt: string
  onStatusChange: (status: string) => void
  onPublishAtChange: (value: string) => void
  error?: string
}

export function PublishStatusField({
  status,
  publishAt,
  onStatusChange,
  onPublishAtChange,
  error,
}: PublishStatusFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <div>
        <Label className="text-sm">Status</Label>
        <Select value={status} onValueChange={onStatusChange}>
          <Select.Trigger>
            <Select.Value />
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="draft">Draft</Select.Item>
            <Select.Item value="scheduled">Scheduled</Select.Item>
            <Select.Item value="published">Published</Select.Item>
          </Select.Content>
        </Select>
      </div>
      {status === 'scheduled' && (
        <div>
          <Label className="text-sm">Publish at</Label>
          <Input
            type="datetime-local"
            value={publishAt}
            onChange={(e) => onPublishAtChange(e.target.value)}
          />
        </div>
      )}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
