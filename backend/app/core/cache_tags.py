"""Revalidation tag names (conventions invariant 11).

One source for backend tag literals. TypeScript twin:
``frontend/lib/cacheTags.ts`` — the two files MUST stay in sync. A
mismatched tag means revalidation silently does nothing.
"""

CERTS = "certifications"
OVERVIEW = "overview"
PROJECTS = "projects"
RELEVANCE = "relevance"
SKILLS = "skills"
TIMELINE = "timeline"

ALL_TAGS: tuple[str, ...] = (CERTS, OVERVIEW, PROJECTS, RELEVANCE, SKILLS, TIMELINE)
