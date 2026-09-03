"""Revalidation tag names (conventions invariant 11).

One source for backend tag literals. TypeScript twin:
``frontend/lib/cacheTags.ts`` — the two files MUST stay in sync. A
mismatched tag means revalidation silently does nothing.
"""

CERTS = "certifications"
COLLECTIONS = "collections"
CONTACT = "contact"
FORMS = "forms"
OVERVIEW = "overview"
PROJECTS = "projects"
PROSE = "prose"
RELEVANCE = "relevance"
RESUMES = "resumes"
SKILLS = "skills"
POSTS = "posts"
THESIS = "thesis"
TIMELINE = "timeline"

ALL_TAGS: tuple[str, ...] = (
    CERTS,
    COLLECTIONS,
    CONTACT,
    FORMS,
    OVERVIEW,
    POSTS,
    PROJECTS,
    PROSE,
    RELEVANCE,
    RESUMES,
    SKILLS,
    THESIS,
    TIMELINE,
)
