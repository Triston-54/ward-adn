"""Shared helpers for content restoration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = ROOT / "data" / "content"


def load_sources() -> dict[str, Any]:
    return json.loads((CONTENT_DIR / "sources.json").read_text(encoding="utf-8"))


def src(module_key: str) -> dict[str, str]:
    """Source reference matching sources.json format."""
    s = load_sources().get(module_key, {})
    return {
        "title": s.get("title", module_key.replace("_", " ").title()),
        "citation": s.get("citation", "Open RN OER"),
        "verified_date": s.get("verified_date", "2026-06"),
    }


def mcq(
    qid: str,
    question: str,
    options: list[str],
    correct: int,
    explanation: str,
    *,
    clinical_why: str = "",
    nclex_category: str = "Physiological Integrity",
    topic: str | None = None,
    system: str | None = None,
    source_key: str = "assessment",
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "id": qid,
        "question": question,
        "options": options,
        "correct_index": correct,
        "explanation": explanation,
        "clinical_why": clinical_why or explanation,
        "nclex_category": nclex_category,
        "source": src(source_key),
    }
    if topic:
        item["topic"] = topic
    if system:
        item["system"] = system
    return item


def write_json(filename: str, data: dict[str, Any]) -> Path:
    path = CONTENT_DIR / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def count_sections(data: dict[str, Any], keys: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key in keys:
        val = data.get(key, [])
        if isinstance(val, dict):
            counts[key] = len(val)
        elif isinstance(val, list):
            counts[key] = len(val)
        else:
            counts[key] = 1 if val else 0
    return counts