export const apiBase = '/api/v1'

class AuthRedirect extends Error {
  constructor() {
    super('Session expired')
    this.name = 'AuthRedirect'
  }
}

let navigateFn: ((path: string) => void) | null = null

export function setNavigate(fn: (path: string) => void) {
  navigateFn = fn
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = path.startsWith('http') ? path : `${apiBase}${path}`

  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (res.status === 401) {
    if (navigateFn) {
      navigateFn('/login')
    }
    throw new AuthRedirect()
  }

  if (res.status === 204) {
    return undefined as T
  }

  const data = await res.json()

  if (!res.ok) {
    const message = data?.detail ?? `Request failed (${res.status})`
    throw new ApiError(message, res.status, data)
  }

  return data as T
}

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(message: string, status: number, data: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}
