import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { KeyRoundIcon, CheckIcon } from 'lucide-react'

export default function ChangePasswordPage() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')

  const mutation = useMutation({
    mutationFn: (body: { current_password: string; new_password: string }) =>
      apiFetch<{ status: string; detail: string }>('/admin/change-password', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      setCurrent('')
      setNext('')
      setConfirm('')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (next !== confirm) return
    if (!current.trim() || !next.trim() || !confirm.trim()) return
    mutation.mutate({ current_password: current, new_password: next })
  }

  const confirmMismatch = confirm.length > 0 && next !== confirm
  const shortNew = next.length > 0 && next.length < 12
  const sameAsCurrent = next.length > 0 && current.length > 0 && next === current

  const canSubmit =
    current.trim().length > 0 &&
    next.length >= 12 &&
    !confirmMismatch &&
    !sameAsCurrent &&
    !mutation.isPending

  return (
    <div className="mx-auto flex max-w-lg flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Rotate the admin password. No redeploy needed — future logins use the new password immediately.
        </p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <KeyRoundIcon className="size-5 text-primary" />
            <CardTitle className="text-base">Change Password</CardTitle>
          </div>
          <CardDescription>
            Requires your current password. New password must be 12–128 characters and differ from current.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="current">Current password</Label>
              <Input
                id="current"
                type="password"
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                placeholder="Enter current password"
                autoComplete="current-password"
                disabled={mutation.isPending}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="new">New password</Label>
              <Input
                id="new"
                type="password"
                value={next}
                onChange={(e) => setNext(e.target.value)}
                placeholder="At least 12 characters"
                autoComplete="new-password"
                disabled={mutation.isPending}
              />
              {shortNew && (
                <p className="text-sm text-destructive">New password must be at least 12 characters.</p>
              )}
              {sameAsCurrent && (
                <p className="text-sm text-destructive">New password must differ from current password.</p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="confirm">Confirm new password</Label>
              <Input
                id="confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Repeat new password"
                autoComplete="new-password"
                disabled={mutation.isPending}
              />
              {confirmMismatch && (
                <p className="text-sm text-destructive">Passwords do not match.</p>
              )}
            </div>

            {mutation.isError && (
              <p className="text-sm text-destructive">
                {mutation.error instanceof ApiError ? mutation.error.message : 'Failed to change password.'}
              </p>
            )}
            {mutation.isSuccess && (
              <p className="flex items-center gap-1 text-sm text-primary">
                <CheckIcon className="size-4" />
                Password updated. Use the new password for your next login.
              </p>
            )}

            <Button type="submit" className="w-full" disabled={!canSubmit}>
              {mutation.isPending ? 'Updating...' : 'Update Password'}
            </Button>
          </CardContent>
        </form>
      </Card>
    </div>
  )
}
