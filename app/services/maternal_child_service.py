"""NURS 148 — Maternal-Child Nursing (OB/Peds) module service."""
from __future__ import annotations

import random
from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "maternal_child"


def _data() -> dict[str, Any]:
    return load_content("maternal_child.json")


def _content_counts(data: dict[str, Any] | None = None) -> dict[str, int]:
    payload = data if data is not None else _data()
    return {
        "pregnancy_count": len(payload.get("pregnancy_stages", [])),
        "labor_count": len(payload.get("labor_delivery", [])),
        "postpartum_count": len(payload.get("postpartum_newborn", [])),
        "pediatric_count": len(payload.get("pediatric_essentials", [])),
        "safety_flag_count": len(payload.get("safety_red_flags", [])),
        "drill_count": len(payload.get("complications_drill", [])),
        "flashcard_count": len(payload.get("flashcards", [])),
        "practice_count": len(payload.get("practice_questions", [])),
    }


ITEMS_TOTAL = sum(_content_counts().values())


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("maternal_child", {})
    return SourceRef(
        title=s.get("title", "Open RN — Nursing Care of the Newborn Family"),
        url=s.get("url"),
        citation=s.get(
            "citation",
            "Open RN OER — Maternal-Newborn Nursing; NCSBN Health Promotion & Physiological Integrity",
        ),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_module_summary() -> dict[str, int]:
    counts = _content_counts()
    counts["items_total"] = sum(counts.values())
    return counts


def get_pregnancy_stages() -> list[dict[str, Any]]:
    return _data().get("pregnancy_stages", [])


def get_labor_delivery() -> list[dict[str, Any]]:
    return _data().get("labor_delivery", [])


def get_postpartum_newborn() -> list[dict[str, Any]]:
    return _data().get("postpartum_newborn", [])


def get_pediatric_essentials() -> list[dict[str, Any]]:
    return _data().get("pediatric_essentials", [])


def get_safety_red_flags() -> list[dict[str, Any]]:
    return _data().get("safety_red_flags", [])


def get_complications_drill_pool() -> list[dict[str, Any]]:
    return _data().get("complications_drill", [])


def get_complications_drill_questions(count: int = 5) -> list[dict[str, Any]]:
    """Return shuffled complications drill questions without answers."""
    pool = get_complications_drill_pool()
    selected = safe_sample(pool, count)
    return [
        {
            "id": q["id"],
            "finding": q["finding"],
            "category": q.get("category"),
            "options": q["options"],
        }
        for q in selected
    ]


def check_complications_drill_answer(
    question_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    question = next(
        (q for q in get_complications_drill_pool() if q.get("id") == question_id),
        None,
    )
    if not question:
        return {
            "correct": False,
            "feedback": "Question not found.",
            "explanation": "",
            "clinical_why": "",
        }

    correct_index = question.get("correct_index", -1)
    correct = selected_index == correct_index
    if selected_option is not None and not correct:
        correct = selected_option.strip() == question["options"][correct_index].strip()

    return {
        "correct": correct,
        "correct_index": correct_index,
        "correct_answer": question["options"][correct_index],
        "explanation": question.get("explanation", ""),
        "clinical_why": question.get("clinical_why", ""),
        "feedback": (
            "Correct — priority action identified."
            if correct
            else "Review the priority nursing action for this complication."
        ),
    }


def get_flashcards(count: Optional[int] = None) -> list[dict[str, Any]]:
    cards = list(_data().get("flashcards", []))
    random.shuffle(cards)
    if count is not None:
        return cards[:count]
    return cards


def get_practice_questions(count: int = 10) -> list[dict[str, Any]]:
    pool = list(_data().get("practice_questions", []))
    selected = safe_sample(pool, count)
    return [
        {
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "correct_index": q["correct_index"],
            "explanation": q.get("explanation", ""),
            "nclex_category": q.get("nclex_category"),
            "source_ref": q.get("source_ref", "maternal_child"),
        }
        for q in selected
    ]


def build_flashcards_markdown() -> str:
    """Markdown flashcard export for maternal-child deck."""
    lines = ["# The Ward — Maternal-Child Flashcards\n"]
    for i, card in enumerate(_data().get("flashcards", []), 1):
        lines += [
            f"## Card {i}",
            f"**Front:** {card.get('front', '')}",
            f"**Back:** {card.get('back', '')}",
            f"**Category:** {card.get('category', 'OB/Peds')}",
            "",
        ]
    return "\n".join(lines)