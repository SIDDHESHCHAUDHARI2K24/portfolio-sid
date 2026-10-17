"""Contact service: dicts in, dicts out (never ORM across the router)."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.contact import repository
from app.features.contact.models import ContactItem, ContactItemKind
from app.features.contact.schemas import ContactItemUpdate, ContactUpdate


def _item_to_dict(item: ContactItem) -> dict[str, object]:
    return {
        "id": item.id,
        "kind": item.kind,
        "label": item.label,
        "url": item.url,
        "sort_order": item.sort_order,
    }


async def get_dict(session: AsyncSession) -> dict[str, object] | None:
    profile = await repository.get_profile(session)
    if profile is None:
        return None
    items = await repository.list_items(session)
    return {
        "consent_text": profile.consent_text,
        "items": [_item_to_dict(i) for i in items],
    }


async def update_dict(session: AsyncSession, data: ContactUpdate) -> dict[str, object]:
    profile = await repository.get_profile(session)
    if profile is None:
        raise ValueError("contact profile not found")

    if data.consent_text is not None:
        profile.consent_text = data.consent_text
        profile.updated_at = datetime.now(UTC)
        await repository.update_profile(session, profile)

    if data.items is not None:
        await _replace_items(session, data.items)

    await session.commit()
    return await get_dict(session)  # type: ignore[return-value]


async def _replace_items(session: AsyncSession, updates: list[ContactItemUpdate]) -> None:
    """Full replace: array order becomes sort_order; rows are recreated.

    Delete-and-insert keeps the semantics dead simple for a single-admin
    editor (ids in the payload are advisory only — nothing is upserted).
    """
    await repository.delete_all_items(session)
    for index, entry in enumerate(updates):
        session.add(
            ContactItem(
                kind=ContactItemKind(entry.kind),
                label=entry.label,
                url=entry.url,
                sort_order=index,
            )
        )
    await session.flush()
