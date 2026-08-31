"""Superset canon seeder: TopicTags, Resumes (PDFs), Timeline, Projects, Skills, Overview.

Idempotent: every entity is upserted by its natural key (variant, slug,
title+organisation+start_date+canon-key, name+section, audience).  Can be
run locally via ``STORAGE_KIND=local`` (writes to ``.storage``) or on
Railway via ``railway run`` with the same args.

Storage + DB are source of truth (D8); PDFs are gitignored but present
locally in ``resumes/``.

Usage::

    uv run python scripts/seed_resumes.py --dir resumes \\
        --canon backend/scripts/resume_canon.json --dry-run   # preview
    uv run python scripts/seed_resumes.py --dir resumes \\
        --canon backend/scripts/resume_canon.json              # real run

    # Railway (same script):
    # railway run python scripts/seed_resumes.py --dir resumes --canon backend/scripts/resume_canon.json

CLI flags:
    --dir DIR        resumes PDF directory (default: resumes)
    --canon PATH     canon JSON path (default: resume_canon.json next to script)
    --pdfs-only      only handle PDFs + Resume rows
    --canon-only     only handle DB canon (skip PDFs)
    --dry-run        log actions without writing DB or storage

Requirements from task:
* TopicTags upsert by slug
* PDF key: ``resumes/{variant}-{sha256[:12]}.pdf``, uploaded via
  ``app.core.storage.get_storage().put(key, data, "application/pdf")``
* Resume upsert by variant (label, file_key, is_active)
* Timeline upsert by canon ``key`` dedupe mapped to (title, organisation,
  start_date) — update highlights/summary/tags, else create; set
  published_at when status published; attach topic_tags via tag_slugs;
  uses service/repository layer lookups
* Projects upsert by slug, resolve timeline_entry_id_key → UUID after
  timeline seeding, set topic_tags + FK
* Skills upsert by name+section
* OverviewIntros upsert by audience
* Revalidate after commits: timeline, projects, skills, resumes, overview, relevance
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

# Make ``backend`` importable when invoked as ``python scripts/seed_resumes.py``
# from either repo root or backend cwd (mirrors seed_e2e.py pattern).
_backend_root = Path(__file__).resolve().parents[1]
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.orm import selectinload  # noqa: E402

from app.core.cache_tags import OVERVIEW, PROJECTS, RELEVANCE, RESUMES, SKILLS, TIMELINE  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.database import async_session_factory  # noqa: E402
from app.core.enums import Audience, PublishStatus  # noqa: E402
from app.core.models import TopicTag  # noqa: E402
from app.core.revalidation import revalidate  # noqa: E402
from app.core.storage import get_storage  # noqa: E402
from app.features.overview.models import OverviewIntro, VALID_AUDIENCES  # noqa: E402
from app.features.projects.models import Project  # noqa: E402
from app.features.resumes.models import ALLOWED_VARIANTS, Resume  # noqa: E402
from app.features.skills.models import Skill, SkillSection  # noqa: E402
from app.features.timeline.models import TimelineEntry, TimelineKind  # noqa: E402

# ---------------------------------------------------------------------------
# helpers: hashing and key generation (exposed for tests)
# ---------------------------------------------------------------------------


def content_hash(data: bytes) -> str:
    """First 12 hex chars of sha256(data) — matches storage.content_hashed_key logic."""
    return hashlib.sha256(data).hexdigest()[:12]


def resume_file_key(variant: str, data: bytes) -> str:
    """Return ``resumes/{variant}-{hash[:12]}.pdf``.

    Mirrors task spec and ``app.core.storage.content_hashed_key`` convention
    but with fixed ``resumes/`` prefix and ``.pdf`` extension.
    """
    if variant not in ALLOWED_VARIANTS:
        allowed = ", ".join(sorted(ALLOWED_VARIANTS))
        raise ValueError(f"variant must be one of: {allowed} (got {variant!r})")
    digest = content_hash(data)
    return f"resumes/{variant}-{digest}.pdf"


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    return date.fromisoformat(s)


def _resolve_canon_path(raw: str | Path) -> Path:
    """Resolve ``--canon`` robustly whether cwd is repo root or backend."""
    p = Path(raw)
    if p.is_file():
        return p.resolve()
    # Try relative to script dir
    alt = (Path(__file__).parent / p.name).resolve()
    if alt.is_file():
        return alt
    # Try relative to backend root
    alt2 = (_backend_root / raw).resolve()
    if alt2.is_file():
        return alt2
    # Try repo root (one up from backend)
    alt3 = (_backend_root.parent / raw).resolve()
    if alt3.is_file():
        return alt3
    # Fallback: return original (caller will raise file-not-found)
    return p


def _resolve_pdf_dir(raw: str | Path) -> Path:
    """Resolve ``--dir`` robustly (cwd may be backend or repo root)."""
    p = Path(raw)
    if p.is_dir():
        return p.resolve()
    # Try sibling of backend root (repo root)
    alt = (_backend_root.parent / raw).resolve()
    if alt.is_dir():
        return alt
    # Try backend-relative
    alt2 = (_backend_root / raw).resolve()
    if alt2.is_dir():
        return alt2
    return p


# ---------------------------------------------------------------------------
# seeding steps
# ---------------------------------------------------------------------------


async def ensure_topic_tags(session, canon_tags: list[dict[str, Any]], dry_run: bool = False) -> dict[str, TopicTag]:
    """Upsert TopicTags by slug. Returns slug -> TopicTag mapping."""
    tag_map: dict[str, TopicTag] = {}
    for t in canon_tags:
        slug = t["slug"]
        label = t["label"]
        desc = t.get("description")
        # Repository-layer lookup (queries only, no FastAPI)
        existing = (await session.scalars(select(TopicTag).where(TopicTag.slug == slug))).first()
        if existing:
            changed = False
            if existing.label != label:
                if dry_run:
                    print(f"  [dry-run] would update TopicTag slug={slug!r} label {existing.label!r} -> {label!r}")
                else:
                    existing.label = label
                    changed = True
            if (existing.description or None) != (desc or None):
                if dry_run:
                    print(f"  [dry-run] would update TopicTag slug={slug!r} description")
                else:
                    existing.description = desc
                    changed = True
            if changed and not dry_run:
                await session.flush()
            tag_map[slug] = existing
        else:
            if dry_run:
                print(f"  [dry-run] would create TopicTag slug={slug!r} label={label!r}")
                # Create an in-memory placeholder so later tag resolutions don't fail
                # during dry-run; we won't commit it.
                placeholder = TopicTag(slug=slug, label=label, description=desc)
                tag_map[slug] = placeholder
            else:
                tag = TopicTag(slug=slug, label=label, description=desc)
                session.add(tag)
                await session.flush()
                print(f"  upsert TopicTag slug={slug!r} label={label!r}")
                tag_map[slug] = tag
    if not dry_run and canon_tags:
        await session.flush()
    # For dry-run we need a real map for later steps — reload real tags from DB
    if dry_run:
        rows = list((await session.scalars(select(TopicTag))).all())
        tag_map_real = {r.slug: r for r in rows}
        # Merge canon slugs that don't yet exist so downstream resolvers can still find them
        for slug, placeholder in list(tag_map.items()):
            if slug not in tag_map_real:
                tag_map_real[slug] = placeholder  # type: ignore[assignment]
        return tag_map_real
    return tag_map


async def seed_resume_pdfs(
    session,
    canon_resumes: list[dict[str, Any]],
    pdf_dir: Path,
    dry_run: bool = False,
) -> None:
    """Upload PDFs via get_storage().put and upsert Resume rows by variant."""
    storage = get_storage()
    for r in canon_resumes:
        variant = r["variant"]
        label = r.get("label") or variant
        source_pdf = r.get("source_pdf")
        is_active = r.get("is_active", True)
        if variant not in ALLOWED_VARIANTS:
            allowed = ", ".join(sorted(ALLOWED_VARIANTS))
            raise ValueError(f"variant must be one of: {allowed} (got {variant!r})")

        pdf_path = pdf_dir / source_pdf if source_pdf else None
        if pdf_path is None or not pdf_path.is_file():
            # Fallback: try alternative capitalisation / exact name search
            candidates = list(pdf_dir.glob("*.pdf"))
            match = None
            if source_pdf:
                for c in candidates:
                    if c.name == source_pdf:
                        match = c
                        break
            if match is None:
                print(f"  WARN: PDF for variant {variant!r} not found: {pdf_path} — skipping storage upload, using existing file_key if any")
                # Still upsert DB with placeholder key so site doesn't break
                # Attempt to keep existing file_key if row exists
                existing = (await session.scalars(select(Resume).where(Resume.variant == variant))).first()
                if existing is None:
                    raise FileNotFoundError(f"PDF missing for variant {variant!r}: {pdf_path} and no existing DB row to preserve file_key")
                else:
                    if dry_run:
                        print(f"  [dry-run] would preserve Resume variant={variant!r} file_key={existing.file_key!r}")
                    else:
                        existing.label = label
                        existing.is_active = bool(is_active)
                        await session.flush()
                        print(f"  preserve Resume variant={variant!r} file_key={existing.file_key!r} (PDF missing)")
                    continue
            else:
                pdf_path = match

        assert pdf_path is not None and pdf_path.is_file()
        data = pdf_path.read_bytes()
        file_key = resume_file_key(variant, data)

        if dry_run:
            print(f"  [dry-run] would put PDF variant={variant!r} key={file_key!r} bytes={len(data)} source={pdf_path.name}")
        else:
            # Content-hashed: re-putting same bytes is idempotent
            storage.put(file_key, data, "application/pdf")
            print(f"  put PDF variant={variant!r} key={file_key!r} bytes={len(data)}")

        # Upsert Resume row by variant (natural key)
        existing = (await session.scalars(select(Resume).where(Resume.variant == variant))).first()
        if existing:
            if dry_run:
                print(f"  [dry-run] would update Resume variant={variant!r} label={label!r} file_key={file_key!r}")
            else:
                existing.label = label
                existing.file_key = file_key
                existing.is_active = bool(is_active)
                await session.flush()
                print(f"  upsert Resume variant={variant!r} label={label!r}")
        else:
            if dry_run:
                print(f"  [dry-run] would create Resume variant={variant!r} label={label!r} file_key={file_key!r}")
            else:
                row = Resume(variant=variant, label=label, file_key=file_key, is_active=bool(is_active))
                session.add(row)
                await session.flush()
                print(f"  create Resume variant={variant!r} label={label!r}")


async def seed_timeline(
    session,
    canon_entries: list[dict[str, Any]],
    tag_map: dict[str, TopicTag],
    dry_run: bool = False,
) -> dict[str, object]:
    """Idempotent timeline seeding.

    Dedupes on canon ``key`` mapped to natural tuple (title, organisation, start_date)
    as the DB has no ``key`` column.  Uses repository-layer lookups
    (select with selectinload) and updates highlights/summary/tags if exists.
    Returns canon_key -> UUID mapping for project FK resolution.
    """
    key_to_id: dict[str, object] = {}
    for e in canon_entries:
        canon_key: str = e["key"]
        kind_raw = e["kind"]
        title = e["title"]
        organisation = e["organisation"]
        location = e.get("location")
        start_date = _parse_date(e["start_date"])
        end_date = _parse_date(e.get("end_date"))
        summary = e.get("summary")
        highlights = e.get("highlights")
        external_url = e.get("external_url")
        sort_order = int(e.get("sort_order", 0))
        status_raw = e.get("status", "published")
        is_pinned = bool(e.get("is_pinned", False))
        tag_slugs: list[str] = list(e.get("tag_slugs", []))
        audience_override_raw: list[str] | None = e.get("audience_override")

        assert start_date is not None, f"timeline entry {canon_key!r} missing start_date"

        # Validate enums
        try:
            kind = TimelineKind(kind_raw)
        except ValueError as exc:
            raise ValueError(f"invalid timeline kind {kind_raw!r} for key {canon_key!r}") from exc
        try:
            status = PublishStatus(status_raw)
        except ValueError as exc:
            raise ValueError(f"invalid status {status_raw!r} for key {canon_key!r}") from exc

        # Resolve tags via tag_map (repository layer)
        missing_slugs = [s for s in tag_slugs if s not in tag_map]
        if missing_slugs:
            raise ValueError(f"timeline entry {canon_key!r} references unknown tag slugs: {', '.join(missing_slugs)}")
        tags = [tag_map[s] for s in tag_slugs]

        # audience_override conversion
        audience_override = None
        if audience_override_raw:
            # Filter empty list -> None
            if len(audience_override_raw) > 0:
                audience_override = [Audience(a) for a in audience_override_raw]

        # Dedupe lookup: natural tuple (title, organisation, start_date)
        # Include canon key in comment: the key determines which natural tuple
        # to expect; two rows with same natural tuple would be considered same
        # logical entry by canon design (superset merge D5).
        existing = (
            await session.scalars(
                select(TimelineEntry)
                .where(
                    TimelineEntry.title == title,
                    TimelineEntry.organisation == organisation,
                    TimelineEntry.start_date == start_date,
                )
                .options(selectinload(TimelineEntry.topic_tags))
            )
        ).first()

        if existing:
            if dry_run:
                print(f"  [dry-run] would update TimelineEntry key={canon_key!r} title={title!r} org={organisation!r} start={start_date}")
                key_to_id[canon_key] = existing.id
                continue
            # Update mutable fields (service-layer style)
            existing.kind = kind
            existing.location = location
            existing.end_date = end_date
            existing.summary = summary
            existing.highlights = highlights
            existing.external_url = external_url
            existing.sort_order = sort_order
            existing.status = status
            existing.is_pinned = is_pinned
            existing.audience_override = audience_override  # type: ignore[assignment]
            # Set published_at when status published and not already set
            if status == PublishStatus.PUBLISHED and existing.published_at is None:
                existing.published_at = datetime.now(UTC)
            # Tags
            existing.topic_tags = tags  # type: ignore[assignment]
            existing.updated_at = datetime.now(UTC)
            await session.flush()
            print(f"  upsert TimelineEntry key={canon_key!r} title={title!r}")
            key_to_id[canon_key] = existing.id
        else:
            if dry_run:
                print(f"  [dry-run] would create TimelineEntry key={canon_key!r} title={title!r} org={organisation!r} start={start_date}")
                # Create a temporary UUID for downstream project FK dry-run resolution
                import uuid as _uuid

                key_to_id[canon_key] = _uuid.uuid4()
                continue
            published_at = datetime.now(UTC) if status == PublishStatus.PUBLISHED else None
            row = TimelineEntry(
                kind=kind,
                title=title,
                organisation=organisation,
                location=location,
                start_date=start_date,
                end_date=end_date,
                summary=summary,
                highlights=highlights,
                external_url=external_url,
                sort_order=sort_order,
                status=status,
                published_at=published_at,
                audience_override=audience_override,  # type: ignore[arg-type]
                is_pinned=is_pinned,
            )
            # Attach tags after construction (relationship needs session add + flush semantics)
            row.topic_tags = tags  # type: ignore[assignment]
            session.add(row)
            await session.flush()
            print(f"  create TimelineEntry key={canon_key!r} title={title!r}")
            key_to_id[canon_key] = row.id

    return key_to_id


async def seed_projects(
    session,
    canon_projects: list[dict[str, Any]],
    key_to_id: dict[str, object],
    tag_map: dict[str, TopicTag],
    dry_run: bool = False,
) -> None:
    """Upsert Projects by slug, resolve timeline_entry_id_key → UUID."""
    for p in canon_projects:
        title = p["title"]
        slug = p["slug"]
        summary = p.get("summary")
        description = p.get("description")
        video_url = p.get("video_url")
        sort_order = int(p.get("sort_order", 0))
        is_pinned = bool(p.get("is_pinned", False))
        status_raw = p.get("status", "published")
        tag_slugs: list[str] = list(p.get("tag_slugs", []))
        audience_override_raw = p.get("audience_override")
        timeline_key = p.get("timeline_entry_id_key")

        try:
            status = PublishStatus(status_raw)
        except ValueError as exc:
            raise ValueError(f"invalid project status {status_raw!r} for slug {slug!r}") from exc

        missing_slugs = [s for s in tag_slugs if s not in tag_map]
        if missing_slugs:
            raise ValueError(f"project {slug!r} references unknown tag slugs: {', '.join(missing_slugs)}")
        tags = [tag_map[s] for s in tag_slugs]

        audience_override = None
        if audience_override_raw:
            if len(audience_override_raw) > 0:
                audience_override = [Audience(a) for a in audience_override_raw]

        timeline_entry_id = None
        if timeline_key:
            if timeline_key not in key_to_id:
                # Fallback: try to look up by natural tuple in DB for robustness
                print(f"  WARN: project {slug!r} timeline_entry_id_key {timeline_key!r} not in key_to_id map — looking up in DB")
                # We could attempt to find by canon key's title etc, but unknown;
                # treat as error unless dry_run
                if dry_run:
                    import uuid as _uuid

                    timeline_entry_id = _uuid.uuid4()
                else:
                    raise ValueError(f"project {slug!r} references unknown timeline_entry_id_key {timeline_key!r}")
            else:
                timeline_entry_id = key_to_id[timeline_key]

        existing = (
            await session.scalars(
                select(Project)
                .where(Project.slug == slug)
                .options(selectinload(Project.topic_tags))
            )
        ).first()

        if existing:
            if dry_run:
                print(f"  [dry-run] would update Project slug={slug!r} title={title!r}")
                continue
            existing.title = title
            existing.summary = summary
            existing.description = description
            existing.video_url = video_url
            existing.sort_order = sort_order
            existing.is_pinned = is_pinned
            existing.status = status
            if status == PublishStatus.PUBLISHED and existing.published_at is None:
                existing.published_at = datetime.now(UTC)
            existing.audience_override = audience_override  # type: ignore[assignment]
            if timeline_entry_id is not None:
                existing.timeline_entry_id = timeline_entry_id  # type: ignore[assignment]
            existing.topic_tags = tags  # type: ignore[assignment]
            existing.updated_at = datetime.now(UTC)
            await session.flush()
            print(f"  upsert Project slug={slug!r}")
        else:
            if dry_run:
                print(f"  [dry-run] would create Project slug={slug!r} title={title!r}")
                continue
            published_at = datetime.now(UTC) if status == PublishStatus.PUBLISHED else None
            row = Project(
                title=title,
                slug=slug,
                summary=summary,
                description=description,
                video_url=video_url,
                sort_order=sort_order,
                status=status,
                published_at=published_at,
                is_pinned=is_pinned,
                audience_override=audience_override,  # type: ignore[arg-type]
                timeline_entry_id=timeline_entry_id,  # type: ignore[arg-type]
            )
            row.topic_tags = tags  # type: ignore[assignment]
            # attachments default empty per repository pattern
            row.attachments = []  # type: ignore[assignment]
            session.add(row)
            await session.flush()
            print(f"  create Project slug={slug!r}")


async def seed_skills(
    session,
    canon_skills: list[dict[str, Any]],
    dry_run: bool = False,
) -> None:
    """Upsert Skills by name+section (logical unique)."""
    for s in canon_skills:
        name = s["name"]
        section_raw = s["section"]
        subsection = s.get("subsection")
        icon_slug = s.get("icon_slug")
        icon_key = s.get("icon_key")
        sort_order = int(s.get("sort_order", 0))

        try:
            section = SkillSection(section_raw)
        except ValueError as exc:
            raise ValueError(f"invalid skill section {section_raw!r} for skill {name!r}") from exc

        existing = (
            await session.scalars(
                select(Skill).where(Skill.name == name, Skill.section == section)
            )
        ).first()

        if existing:
            if dry_run:
                print(f"  [dry-run] would update Skill name={name!r} section={section_raw!r}")
                continue
            changed = False
            if existing.subsection != subsection:
                existing.subsection = subsection
                changed = True
            if existing.icon_slug != icon_slug:
                existing.icon_slug = icon_slug
                changed = True
            if existing.icon_key != icon_key:
                existing.icon_key = icon_key
                changed = True
            if existing.sort_order != sort_order:
                existing.sort_order = sort_order
                changed = True
            if changed:
                existing.updated_at = datetime.now(UTC)
                await session.flush()
            print(f"  upsert Skill name={name!r} section={section_raw!r}")
        else:
            if dry_run:
                print(f"  [dry-run] would create Skill name={name!r} section={section_raw!r}")
                continue
            row = Skill(
                name=name,
                section=section,
                subsection=subsection,
                icon_slug=icon_slug,
                icon_key=icon_key,
                sort_order=sort_order,
            )
            session.add(row)
            await session.flush()
            print(f"  create Skill name={name!r} section={section_raw!r}")


async def seed_overview_intros(
    session,
    canon_intros: list[dict[str, Any]],
    dry_run: bool = False,
) -> None:
    """Upsert OverviewIntros by audience (update headline/body)."""
    for intro in canon_intros:
        audience = intro["audience"]
        headline = intro.get("headline", "")
        body = intro.get("body", "")
        hero_image_key = intro.get("hero_image_key")
        cta_label = intro.get("cta_label")
        cta_url = intro.get("cta_url")
        status_raw = intro.get("status", "published")
        is_pinned = bool(intro.get("is_pinned", False))

        if audience not in VALID_AUDIENCES:
            raise ValueError(f"invalid overview audience {audience!r}")

        try:
            status = PublishStatus(status_raw)
        except ValueError as exc:
            raise ValueError(f"invalid overview status {status_raw!r} for audience {audience!r}") from exc

        existing = (
            await session.scalars(select(OverviewIntro).where(OverviewIntro.audience == audience))
        ).first()

        if existing:
            if dry_run:
                print(f"  [dry-run] would update OverviewIntro audience={audience!r}")
                continue
            existing.headline = headline
            existing.body = body
            if hero_image_key is not None:
                existing.hero_image_key = hero_image_key
            if cta_label is not None:
                existing.cta_label = cta_label
            if cta_url is not None:
                existing.cta_url = cta_url
            existing.is_pinned = is_pinned
            # Ensure published if canon says published
            if status == PublishStatus.PUBLISHED and existing.status != PublishStatus.PUBLISHED:
                existing.status = PublishStatus.PUBLISHED
                if existing.published_at is None:
                    existing.published_at = datetime.now(UTC)
            elif existing.status != status:
                existing.status = status
                if status == PublishStatus.PUBLISHED and existing.published_at is None:
                    existing.published_at = datetime.now(UTC)
            existing.updated_at = datetime.now(UTC)
            await session.flush()
            print(f"  upsert OverviewIntro audience={audience!r}")
        else:
            if dry_run:
                print(f"  [dry-run] would create OverviewIntro audience={audience!r}")
                continue
            published_at = datetime.now(UTC) if status == PublishStatus.PUBLISHED else None
            row = OverviewIntro(
                audience=audience,
                headline=headline,
                body=body,
                hero_image_key=hero_image_key,
                cta_label=cta_label,
                cta_url=cta_url,
                status=status,
                published_at=published_at,
                is_pinned=is_pinned,
            )
            session.add(row)
            await session.flush()
            print(f"  create OverviewIntro audience={audience!r}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


async def run_seed(
    pdf_dir: Path,
    canon_path: Path,
    pdfs_only: bool = False,
    canon_only: bool = False,
    dry_run: bool = False,
) -> None:
    if pdfs_only and canon_only:
        raise ValueError("--pdfs-only and --canon-only are mutually exclusive")

    # Load canon
    with canon_path.open(encoding="utf-8") as f:
        canon = json.load(f)

    topic_tags = canon.get("topic_tags", [])
    timeline_entries = canon.get("timeline_entries", [])
    projects = canon.get("projects", [])
    skills = canon.get("skills", [])
    resumes = canon.get("resumes", [])
    overview_intros = canon.get("overview_intros", [])

    print(f"Canon loaded: {canon_path}")
    print(f"  topic_tags={len(topic_tags)} timeline={len(timeline_entries)} projects={len(projects)} skills={len(skills)} resumes={len(resumes)} intros={len(overview_intros)}")
    if dry_run:
        print("DRY RUN — no DB or storage writes will be performed")

    # Validate variant allowlist early
    for r in resumes:
        if r["variant"] not in ALLOWED_VARIANTS:
            allowed = ", ".join(sorted(ALLOWED_VARIANTS))
            raise ValueError(f"variant must be one of: {allowed} (got {r['variant']!r})")

    # Shared session for all DB work (one transaction per logical group, commits after each)
    # Use async_session_factory (conventions: real Postgres, no DB mocks)
    async with async_session_factory() as session:
        tag_map: dict[str, TopicTag] = {}
        key_to_id: dict[str, object] = {}

        if not pdfs_only:
            # 1) TopicTags
            print("Ensuring TopicTags...")
            tag_map = await ensure_topic_tags(session, topic_tags, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print(f"  committed {len(tag_map)} TopicTags")
            else:
                # Still need tag_map for downstream dry-run planning; we built it above
                print(f"  [dry-run] TopicTags would be {len(tag_map)}")
            # If tag_map was built via dry-run placeholder, reload real ones for downstream
            if not tag_map and topic_tags:
                tag_map = {t.slug: t for t in (await session.scalars(select(TopicTag))).all()}

            # 2) Timeline
            print("Seeding TimelineEntries...")
            key_to_id = await seed_timeline(session, timeline_entries, tag_map, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print(f"  committed timeline key_to_id={len(key_to_id)}")
            else:
                print(f"  [dry-run] timeline keys would be {len(key_to_id)}")

            # 3) Projects
            print("Seeding Projects...")
            await seed_projects(session, projects, key_to_id, tag_map, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print("  committed projects")

            # 4) Skills
            print("Seeding Skills...")
            await seed_skills(session, skills, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print("  committed skills")

            # 5) OverviewIntros
            print("Seeding OverviewIntros...")
            await seed_overview_intros(session, overview_intros, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print("  committed overview_intros")

        if not canon_only:
            # 6) Resume PDFs + rows
            # Ensure tag_map populated even if pdfs_only (not needed for resumes but for completeness)
            if not tag_map:
                rows = list((await session.scalars(select(TopicTag))).all())
                tag_map = {r.slug: r for r in rows}
            print(f"Seeding Resumes from dir={pdf_dir} ...")
            if not pdf_dir.is_dir():
                raise FileNotFoundError(f"PDF dir not found: {pdf_dir}")
            await seed_resume_pdfs(session, resumes, pdf_dir, dry_run=dry_run)
            if not dry_run:
                await session.commit()
                print("  committed resumes")

    if not dry_run:
        # Revalidation after commits (conventions invariant 8: after commit, never inside tx)
        # Tags per task: timeline, projects, skills, resumes, overview, relevance
        tags = [TIMELINE, PROJECTS, SKILLS, RESUMES, OVERVIEW, RELEVANCE]
        print(f"Triggering revalidation for tags={tags} ...")
        try:
            await revalidate(tags)
            print("  revalidation triggered")
        except Exception as exc:  # revalidate never raises, but be defensive
            print(f"  revalidation error (non-fatal): {exc}")
    else:
        print("DRY RUN — skipping revalidation")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed superset canon (resumes, timeline, projects, skills, overview)")
    parser.add_argument(
        "--dir",
        dest="pdf_dir",
        default="resumes",
        help="PDF source directory (default: resumes; resolved relative to CWD or repo root)",
    )
    parser.add_argument(
        "--canon",
        dest="canon_path",
        default=str(Path(__file__).parent / "resume_canon.json"),
        help="Canon JSON path (default: backend/scripts/resume_canon.json)",
    )
    parser.add_argument("--pdfs-only", action="store_true", help="Only handle PDFs + Resume rows")
    parser.add_argument("--canon-only", action="store_true", help="Only handle DB canon (skip PDFs)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing DB or storage")
    # Alias: --dry_run or dry-run flag without dashes handling
    parser.add_argument("--dry_run", action="store_true", help=argparse.SUPPRESS, dest="dry_run_alias")
    return parser.parse_args(argv)


async def main_async(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    dry_run = bool(args.dry_run or getattr(args, "dry_run_alias", False))
    pdf_dir = _resolve_pdf_dir(args.pdf_dir)
    canon_path = _resolve_canon_path(args.canon_path)

    if not canon_path.is_file():
        # Try alternative: if canon_path was backend/scripts/resume_canon.json but cwd is backend, try repo root
        alt = _resolve_canon_path(Path(__file__).parent / "resume_canon.json")
        if alt.is_file():
            canon_path = alt
        else:
            raise FileNotFoundError(f"canon JSON not found: {canon_path} (also tried {alt})")

    print(f"PDF dir: {pdf_dir}")
    print(f"Canon: {canon_path}")
    print(f"STORAGE_KIND={get_settings().storage_kind} LOCAL_STORAGE_DIR={get_settings().local_storage_dir}")
    if args.pdfs_only:
        print("Mode: pdfs-only")
    if args.canon_only:
        print("Mode: canon-only")
    if dry_run:
        print("Mode: dry-run")

    await run_seed(
        pdf_dir=pdf_dir,
        canon_path=canon_path,
        pdfs_only=args.pdfs_only,
        canon_only=args.canon_only,
        dry_run=dry_run,
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
