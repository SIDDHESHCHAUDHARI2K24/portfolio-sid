/**
 * Revalidation tag names (conventions invariant 11).
 *
 * One source for frontend tag literals. Python twin:
 * `backend/app/core/cache_tags.py` — the two files MUST stay in sync.
 * A mismatched tag means revalidation silently does nothing.
 */
export const CACHE_TAGS = {
  overview: "overview",
  timeline: "timeline",
  relevance: "relevance",
} as const;

export type CacheTag = (typeof CACHE_TAGS)[keyof typeof CACHE_TAGS];
