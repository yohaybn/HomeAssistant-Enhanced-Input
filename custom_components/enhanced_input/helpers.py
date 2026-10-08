"""Pure helpers for enhanced_input (no Home Assistant imports, easy to unit test)."""
from __future__ import annotations

import re
from typing import Any

_NON_SLUG = re.compile(r"[^a-z0-9]+")
_DUP_SUFFIX = re.compile(r"^(?P<base>.*?)(?:_2){2,}$")


def slugify_name(name: Any) -> str:
    """Return a stable, valid entity object_id for a user supplied name.

    "AI-Answer", "ai answer" and "Ai Answer" all map to "ai_answer", so one name
    always resolves to one entity_id and one unique_id.
    """
    slug = _NON_SLUG.sub("_", str(name).strip().lower()).strip("_")
    return slug or "enhanced_input"


def to_text(value: Any) -> str:
    """Coerce a service/storage value to str (numbers used to crash len())."""
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def migrate_storage(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Clean up entries created by the old "_2_2_2" duplicate bug.

    Entries whose object_id ends in two or more "_2" are artifacts. They are
    dropped when the base entity (or its first "_2" copy) already exists,
    otherwise renamed back to the base object_id.

    Returns (new_data, removed_entity_ids). Renamed entries also appear in
    removed_entity_ids so the caller can drop their old registry entry.
    """
    result: dict[str, Any] = {}
    removed: list[str] = []
    tails = {key.split(".")[-1] for key in data}
    for key, value in data.items():
        domain, _, tail = key.rpartition(".")
        match = _DUP_SUFFIX.match(tail)
        if not match or not match.group("base"):
            result.setdefault(key, value)
            continue
        base = match.group("base")
        removed.append(key)
        if base in tails or f"{base}_2" in tails:
            continue
        new_key = f"{domain}.{base}" if domain else base
        result.setdefault(new_key, value)
        tails.add(base)
    return result, removed
