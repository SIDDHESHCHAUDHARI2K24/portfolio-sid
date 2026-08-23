import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch, ApiError } from '@/lib/api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card'
import { LockIcon } from 'lucide-react'

export default function LoginPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [password, setPassword] = useState('')

  const mutation = useMutation({
    mutationFn: (pw: string) =>
      apiFetch<{ detail: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password: pw }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
      navigate('/login/verify')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (password.trim()) {
      mutation.mutate(password)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-primary/10">
            <LockIcon className="size-5 text-primary" />
          </div>
          <CardTitle>Admin Login</CardTitle>
          <CardDescription>Enter your password to receive a one-time code.</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                autoFocus
                disabled={mutation.isPending}
              />
              {mutation.isError && (
                <p className="text-sm text-destructive">
                  {mutation.error instanceof ApiError
                    ? mutation.error.message
                    : 'Something went wrong. Please try again.'}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={mutation.isPending || !password.trim()}>
              {mutation.isPending ? 'Sending...' : 'Send Code'}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
