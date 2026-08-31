import { CACHE_TAGS, type CacheTag } from "./cacheTags";

// NEXT_PUBLIC_API_BASE_URL is the public origin (admin host via proxy) for
// client-side fetches. On the server (SSR/build) prefer BACKEND_URL — the
// Railway private network URL (http://backend.railway.internal:8000) so
// builds don't need a public backend. When NEXT_PUBLIC_API_BASE_URL is
// unset the client falls back to relative "/api/v1" which is proxied via
// Next.js rewrites to the same private backend (see next.config.ts).
const API_BASE =
  typeof window === "undefined"
    ? (process.env.BACKEND_URL
        ? `${process.env.BACKEND_URL}/api/v1`
        : process.env.NEXT_PUBLIC_API_BASE_URL
          ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
          : "http://backend.railway.internal:8000/api/v1")
    : process.env.NEXT_PUBLIC_API_BASE_URL
      ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
      : "/api/v1";

interface ApiFetchOptions extends Omit<RequestInit, "next"> {
  tags?: CacheTag[];
  revalidate?: number | false;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { tags = [CACHE_TAGS.timeline], revalidate = 3600, ...init } = options;

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    next: {
      tags,
      revalidate,
    },
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }

  return res.json() as Promise<T>;
}
