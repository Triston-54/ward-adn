"""Pathophysiology module — core concepts, disease processes, scenarios, practice."""
from __future__ import annotations

import random
from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "pathophysiology"
ITEMS_TOTAL = 76


def _data() -> dict[str, Any]:
    return load_content("pathophysiology.json")


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("pathophysiology", {})
    return SourceRef(
        title=s.get("title", "Open RN — Pathophysiology"),
        url=s.get("url"),
        citation=s.get("citation", "Open RN OER; NCSBN Physiological Integrity"),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_core_concepts() -> list[dict[str, Any]]:
    return _data().get("core_concepts", [])


def get_disease_processes() -> list[dict[str, Any]]:
    return _data().get("disease_processes", [])


def get_compare_contrast_pairs() -> list[dict[str, Any]]:
    return _data().get("compare_contrast_pairs", [])


def get_breakdown_scenarios_pool() -> list[dict[str, Any]]:
    return _data().get("what_breaks_down_scenarios", [])


def get_breakdown_scenarios(count: int = 5) -> list[dict[str, Any]]:
    """Return shuffled teaching scenarios without answers for client drill."""
    pool = get_breakdown_scenarios_pool()
    selected = safe_sample(pool, count)
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "trigger": s.get("trigger"),
            "normal_function": s.get("normal_function"),
            "breakdown": s.get("breakdown"),
            "cascade": s.get("cascade", []),
            "clinical_signs": s.get("clinical_signs", []),
            "nursing_response": s.get("nursing_response"),
            "question": s["question"],
            "options": s["options"],
            "source_ref": s.get("source_ref"),
        }
        for s in selected
    ]


def check_breakdown_answer(
    scenario_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    scenario = next(
        (s for s in get_breakdown_scenarios_pool() if s.get("id") == scenario_id),
        None,
    )
    if not scenario:
        return {
            "correct": False,
            "feedback": "Scenario not found.",
            "explanation": "",
            "clinical_why": "",
        }

    correct_index = scenario.get("correct_index", -1)
    correct = selected_index == correct_index
    if selected_option is not None and not correct:
        correct = selected_option.strip() == scenario["options"][correct_index].strip()

    return {
        "correct": correct,
        "correct_index": correct_index,
        "correct_answer": scenario["options"][correct_index],
        "explanation": scenario.get("explanation", ""),
        "clinical_why": scenario.get("nursing_response", ""),
        "feedback": "Correct — mechanism identified." if correct else "Review the pathophysiologic cascade for this scenario.",
    }


def get_flashcards(count: Optional[int] = None) -> list[dict[str, Any]]:
    cards = list(_data().get("flashcards", []))
    random.shuffle(cards)
    if count is not None:
        cards = cards[: min(count, len(cards))]
    return cards


def get_practice_questions(count: int = 10) -> list[dict[str, Any]]:
    pool = list(_data().get("practice_questions", []))
    selected = safe_sample(pool, count)
    output = []
    for q in selected:
        item = dict(q)
        if "options" in item and "correct_index" in item:
            indexed = list(enumerate(item["options"]))
            random.shuffle(indexed)
            item["options"] = [opt for _, opt in indexed]
            item["correct_index"] = next(
                i for i, (orig, _) in enumerate(indexed) if orig == q["correct_index"]
            )
        output.append(item)
    return output


def build_flashcards_markdown() -> str:
    """Markdown flashcard export for pathophysiology deck."""
    lines = ["# The Ward — Pathophysiology Flashcards\n"]
    for i, card in enumerate(_data().get("flashcards", []), 1):
        lines += [
            f"## Card {i}",
            f"**Front:** {card.get('front', '')}",
            f"**Back:** {card.get('back', '')}",
            f"**Category:** {card.get('category', '')}",
            f"**Clinical:** {card.get('clinical_why', '')}",
            "",
        ]
    return "\n".join(lines)


def get_module_summary() -> dict[str, Any]:
    data = _data()
    return {
        "concepts_count": len(data.get("core_concepts", [])),
        "disease_count": len(data.get("disease_processes", [])),
        "compare_count": len(data.get("compare_contrast_pairs", [])),
        "scenario_count": len(data.get("what_breaks_down_scenarios", [])),
        "flashcard_count": len(data.get("flashcards", [])),
        "practice_count": len(data.get("practice_questions", [])),
        "items_total": ITEMS_TOTAL,
    }