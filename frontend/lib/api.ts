import { CACHE_TAGS, type CacheTag } from "./cacheTags";

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
    : "/api/v1"
);

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
