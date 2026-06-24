"""Pharmacy Calculations & Advanced Problem Solving — module service."""
from __future__ import annotations

from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content

MODULE_ID = "pharmacy_calculations"
ITEMS_TOTAL = 48
CONTENT_FILE = "pharmacy_calculations.json"


def _data() -> dict[str, Any]:
    return load_content(CONTENT_FILE)


def default_source() -> SourceRef:
    data = _data()
    src = data.get("primary_source", {})
    return SourceRef(
        title=src.get("title", "Remington · NAPLEX Calculation Competencies"),
        url=src.get("url"),
        citation=src.get("citation", "Remington; NABP NAPLEX"),
        verified_date=data.get("updated", "2026-06"),
    )


def get_module_summary() -> dict[str, int]:
    data = _data()
    return {
        "calc_type_count": len(data.get("calc_types", [])),
        "calc_topic_count": len(data.get("topic_outline", [])),
        "practice_count": len(data.get("practice_problems", [])),
        "error_trap_count": len(data.get("error_traps", [])),
        "clinical_scenario_count": len(data.get("clinical_scenarios", [])),
        "items_total": ITEMS_TOTAL,
        "items_live": (
            len(data.get("calc_types", []))
            + len(data.get("topic_outline", []))
            + len(data.get("practice_problems", []))
            + len(data.get("error_traps", []))
        ),
    }


def get_topic_outline() -> list[dict[str, Any]]:
    return _data().get("topic_outline", [])


def get_calc_types() -> list[dict[str, Any]]:
    return _data().get("calc_types", [])


def get_calc_type(calc_id: str) -> Optional[dict[str, Any]]:
    return next((c for c in get_calc_types() if c.get("id") == calc_id), None)


def get_practice_problems() -> list[dict[str, Any]]:
    return _data().get("practice_problems", [])


def get_practice_problem(problem_id: str) -> Optional[dict[str, Any]]:
    return next((p for p in get_practice_problems() if p.get("id") == problem_id), None)


def get_error_traps() -> list[dict[str, Any]]:
    return _data().get("error_traps", [])


def get_clinical_scenarios() -> list[dict[str, Any]]:
    return _data().get("clinical_scenarios", [])


def check_practice_answer(problem_id: str, selected_index: int) -> dict[str, Any]:
    problem = get_practice_problem(problem_id)
    if not problem:
        return {"correct": False, "message": "Problem not found."}

    correct = selected_index == problem.get("correct_index", -1)
    return {
        "correct": correct,
        "correct_index": problem.get("correct_index"),
        "explanation": problem.get("explanation", ""),
        "answer": problem.get("answer", ""),
        "trap": problem.get("trap", ""),
        "pharmacist_note": problem.get("pharmacist_note", ""),
        "clinical_context": problem.get("clinical_context", ""),
        "work_steps": problem.get("work_steps", []),
    }


def get_module_content() -> dict[str, Any]:
    data = _data()
    return {
        "module_id": data.get("module_id", MODULE_ID),
        "title": data.get("title", ""),
        "subtitle": data.get("subtitle", ""),
        "status": data.get("status", "scaffold"),
        "differentiator": data.get("differentiator", ""),
        "topic_outline": get_topic_outline(),
        "calc_types": get_calc_types(),
        "practice_problems": get_practice_problems(),
        "error_traps": get_error_traps(),
        "clinical_scenarios": get_clinical_scenarios(),
        "tabs": data.get("tabs", []),
        "summary": get_module_summary(),
    }