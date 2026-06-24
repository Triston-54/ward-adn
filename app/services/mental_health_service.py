"""NURS 147 — Mental Health Nursing module service."""
from __future__ import annotations

from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "mental_health"


def _data() -> dict[str, Any]:
    return load_content("mental_health.json")


def _content_counts(data: dict[str, Any] | None = None) -> dict[str, int]:
    payload = data if data is not None else _data()
    return {
        "communication_count": len(payload.get("therapeutic_communication", [])),
        "barrier_count": len(payload.get("communication_barriers", [])),
        "communication_scenario_count": len(payload.get("communication_scenarios", [])),
        "safety_flag_count": len(payload.get("safety_risk_flags", [])),
        "screening_tool_count": len(payload.get("screening_tools", [])),
        "safety_drill_count": len(payload.get("safety_drill", [])),
        "disorder_count": len(payload.get("disorders", [])),
        "de_escalation_count": len(payload.get("de_escalation", [])),
        "practice_count": len(payload.get("practice_questions", [])),
    }


ITEMS_TOTAL = sum(_content_counts().values())


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("mental_health", {})
    return SourceRef(
        title=s.get("title", "Open RN — Mental Health Nursing"),
        url=s.get("url"),
        citation=s.get("citation", "Open RN OER; NCSBN Psychosocial Integrity"),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_module_summary() -> dict[str, int]:
    counts = _content_counts()
    counts["items_total"] = sum(counts.values())
    return counts


def get_therapeutic_communication() -> list[dict[str, Any]]:
    return _data().get("therapeutic_communication", [])


def get_communication_barriers() -> list[dict[str, Any]]:
    return _data().get("communication_barriers", [])


def get_communication_scenarios() -> list[dict[str, Any]]:
    return _data().get("communication_scenarios", [])


def get_safety_risk_flags() -> list[dict[str, Any]]:
    return _data().get("safety_risk_flags", [])


def get_screening_tools() -> list[dict[str, Any]]:
    return _data().get("screening_tools", [])


def get_disorders() -> list[dict[str, Any]]:
    return _data().get("disorders", [])


def get_de_escalation() -> list[dict[str, Any]]:
    return _data().get("de_escalation", [])


def get_de_escalation_techniques() -> list[dict[str, Any]]:
    return [item for item in get_de_escalation() if item.get("type") == "technique"]


def get_de_escalation_scenarios() -> list[dict[str, Any]]:
    return [item for item in get_de_escalation() if item.get("type") == "scenario"]


def get_safety_drill_pool() -> list[dict[str, Any]]:
    return _data().get("safety_drill", [])


def get_safety_drill_questions(count: int = 5) -> list[dict[str, Any]]:
    """Return shuffled safety drill questions without answers."""
    pool = get_safety_drill_pool()
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
            "topic": q.get("topic"),
            "source": q.get("source"),
        }
        for q in selected
    ]


def _check_scenario_answer(
    pool: list[dict[str, Any]],
    question_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
    *,
    correct_feedback: str,
    incorrect_feedback: str,
) -> dict[str, Any]:
    question = next((q for q in pool if q.get("id") == question_id), None)
    if not question:
        return {
            "correct": False,
            "feedback": "Scenario not found.",
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
        "feedback": correct_feedback if correct else incorrect_feedback,
    }


def check_safety_drill_answer(
    question_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    return _check_scenario_answer(
        get_safety_drill_pool(),
        question_id,
        selected_index,
        selected_option,
        correct_feedback="Correct — priority action identified.",
        incorrect_feedback="Review the priority nursing action for this finding.",
    )


def check_communication_scenario_answer(
    scenario_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    return _check_scenario_answer(
        get_communication_scenarios(),
        scenario_id,
        selected_index,
        selected_option,
        correct_feedback="Correct — therapeutic response identified.",
        incorrect_feedback="Review therapeutic communication techniques for this patient statement.",
    )


def check_de_escalation_scenario_answer(
    scenario_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict[str, Any]:
    return _check_scenario_answer(
        get_de_escalation_scenarios(),
        scenario_id,
        selected_index,
        selected_option,
        correct_feedback="Correct — de-escalation priority identified.",
        incorrect_feedback="Review least-restrictive de-escalation steps for this situation.",
    )