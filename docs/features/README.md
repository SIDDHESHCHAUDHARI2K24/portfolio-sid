# Backend Feature Documentation Index

One markdown doc per backend feature: purpose, API surface, data flow (mermaid), functionality (mermaid), files to reference, and feature-specific invariants. Facts are sourced from code; when behaviour looks asymmetric it is documented as-is rather than smoothed over.

| Feature | Doc | One-liner |
|---|---|---|
| auth | [auth.md](auth.md) | Password + OTP admin login, sessions, lockout |
| certifications | [certifications.md](certifications.md) | Technical/business credentials with file evidence |
| collections | [collections.md](collections.md) | Books/anime/manhwa + download-once R2 cover pipeline |
| crawlers | [crawlers.md](crawlers.md) | AI-crawler hit logging with hashed IPs, admin panel |
| forms | [forms.md](forms.md) | Contact/dealflow submissions behind anti-abuse chain |
| overview | [overview.md](overview.md) | Per-audience intro/hero rows |
| posts | [posts.md](posts.md) | External posts routed into three themed collections |
| projects | [projects.md](projects.md) | Projects with attachments and timeline cross-links |
| prose | [prose.md](prose.md) | Sanitized markdown pages grouped by editorial intent |
| relevance | [relevance.md](relevance.md) | Audience-tag map + pure client-side resolver |
| resumes | [resumes.md](resumes.md) | Tech/business resume PDF variants per audience |
| skills | [skills.md](skills.md) | Sectioned skill lists — deliberately unfiltered |
| thesis | [thesis.md](thesis.md) | Investment-thesis links out to Drive docs |
| timeline | [timeline.md](timeline.md) | Education/experience chronology with publish lifecycle |

Cross-cutting core (`backend/app/core/`): storage adapter, revalidation, cache tags, turnstile, glitchtip — documented within the feature docs that consume them; see `docs/post-development/session-1/post-development-report.md` §Key Invariants for the global rules.

Docstring policy (S2_T07): module-level docstrings are present on 100% of non-`__init__` modules; function-level docstrings are added where logic is non-obvious — self-describing CRUD names stay bare to keep signal-to-noise high.
