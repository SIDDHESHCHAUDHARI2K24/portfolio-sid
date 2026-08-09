import { Navigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/api'
import { Loader2Icon } from 'lucide-react'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  const { isLoading, isError } = useQuery({
    queryKey: ['session'],
    queryFn: () => apiFetch<{ status: string }>('/admin/me'),
    retry: false,
    staleTime: 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2Icon className="size-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (isError) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}
