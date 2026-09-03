import { CACHE_TAGS, type CacheTag } from "./cacheTags";

// NEXT_PUBLIC_API_BASE_URL is the public origin (admin host via proxy) for
// client-side fetches. On the server (SSR/build) prefer BACKEND_URL — the
// Railway private network URL (http://backend.railway.internal:8080) so
// runtime SSR stays on the private network. The Railway builder cannot resolve
// *.railway.internal at build time (prerender), so apiFetch retries with the
// public admin proxy (PUBLIC_API_PROXY env, e.g. https://<admin>.up.railway.app)
// when a private fetch fails with ENOTFOUND/ECONNREFUSED. Client falls back to
// relative "/api/v1" which is proxied via Next.js rewrites to the same private
// backend (see next.config.ts).
const PUBLIC_PROXY = process.env.PUBLIC_API_PROXY ?? "";

function getServerBase(): string {
  if (process.env.BACKEND_URL) return `${process.env.BACKEND_URL}/api/v1`;
  if (process.env.NEXT_PUBLIC_API_BASE_URL) return `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`;
  return "http://backend.railway.internal:8080/api/v1";
}

function getFallbackServerBase(primary: string): string | null {
  // Railway builder cannot resolve *.railway.internal; always retry via public proxy.
  // Ignore NEXT_PUBLIC_API_BASE_URL when it is localhost (local dev .env) to ensure
  // the builder uses the public proxy rather than a dead localhost.
  if (PUBLIC_PROXY) {
    const publicFallback = `${PUBLIC_PROXY}/api/v1`;
    if (publicFallback !== primary) return publicFallback;
  }
  const nextPublic = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (nextPublic) {
    const candidate = `${nextPublic}/api/v1`;
    if (candidate !== primary && !candidate.includes("localhost") && !candidate.includes("127.0.0.1")) {
      return candidate;
    }
  }
  return null;
}

function isPrivateNetworkError(err: unknown, primary: string): boolean {
  if (!primary.includes("railway.internal")) return false;
  if (err instanceof TypeError) {
    const msg = err.message.toLowerCase();
    if (msg.includes("fetch failed") || msg.includes("enotfound") || msg.includes("econnrefused") || msg.includes("getaddrinfo")) return true;
  }
  const cause = (err as { cause?: { code?: string; message?: string } })?.cause;
  if (cause?.code === "ENOTFOUND" || cause?.code === "ECONNREFUSED") return true;
  if (cause?.message && /enotfound|econnrefused|getaddrinfo/i.test(cause.message)) return true;
  return false;
}

const API_BASE =
  typeof window === "undefined"
    ? getServerBase()
    : process.env.NEXT_PUBLIC_API_BASE_URL
      ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1`
      : "/api/v1";

interface ApiFetchOptions extends Omit<RequestInit, "next"> {
  tags?: CacheTag[];
  revalidate?: number | false;
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { tags = [CACHE_TAGS.timeline], revalidate = 3600, ...init } = options;

  const doFetch = async (base: string) => {
    const res = await fetch(`${base}${path}`, {
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
  };

  try {
    return await doFetch(API_BASE);
  } catch (err) {
    // At build time the private backend is unreachable (ENOTFOUND); retry via public proxy.
    if (typeof window === "undefined" && isPrivateNetworkError(err, API_BASE)) {
      const fallback = getFallbackServerBase(API_BASE);
      if (fallback) {
        console.warn(`[apiFetch] ${API_BASE}${path} failed (${String(err)}), retrying via ${fallback}${path}`);
        return await doFetch(fallback);
      }
    }
    throw err;
  }
}
