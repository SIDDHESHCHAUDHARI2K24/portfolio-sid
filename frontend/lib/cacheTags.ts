/**
 * Revalidation tag names (conventions invariant 11).
 *
 * One source for frontend tag literals. Python twin:
 * `backend/app/core/cache_tags.py` — the two files MUST stay in sync.
 * A mismatched tag means revalidation silently does nothing.
 */
// === APPEND-ZONE-START: cache tag constants ===
// Add new cache tags below, alphabetical, never reorder
export const CACHE_TAGS = {
  overview: "overview",
  timeline: "timeline",
  relevance: "relevance",
} as const;
// === APPEND-ZONE-END: cache tag constants ===

export type CacheTag = (typeof CACHE_TAGS)[keyof typeof CACHE_TAGS];
