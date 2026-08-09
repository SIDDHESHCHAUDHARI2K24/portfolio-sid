"""Revalidation tag names (conventions invariant 11).

One source for backend tag literals. TypeScript twin:
``frontend/lib/cacheTags.ts`` — the two files MUST stay in sync. A
mismatched tag means revalidation silently does nothing.
"""

OVERVIEW = "overview"
TIMELINE = "timeline"
RELEVANCE = "relevance"

ALL_TAGS: tuple[str, ...] = (OVERVIEW, TIMELINE, RELEVANCE)
