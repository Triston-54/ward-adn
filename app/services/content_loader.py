"""Load verified JSON content from data/content/."""
import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence, TypeVar

from app.config import settings

T = TypeVar("T")


@lru_cache(maxsize=32)
def load_content(filename: str) -> dict[str, Any]:
    """Load and cache a JSON content file."""
    path = settings.content_dir / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def reload_content(filename: str) -> dict[str, Any]:
    """Force reload of a content file (clears cache for that file)."""
    load_content.cache_clear()
    return load_content(filename)


def safe_sample(pool: Sequence[T], count: int) -> list[T]:
    """Sample up to count items without replacement; return [] if pool is empty."""
    if not pool or count <= 0:
        return []
    return random.sample(list(pool), min(count, len(pool)))