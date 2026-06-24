"""NURS 146 module architecture manifest and Phase 2 scaffold loader."""
from __future__ import annotations

from typing import Any, Optional

from app.services.assessment_service import get_module_summary
from app.services.content_loader import load_content

MANIFEST_FILE = "assessment_manifest.json"
SCAFFOLD_FILE = "assessment_scaffold.json"


def get_manifest() -> dict[str, Any]:
    """Module architecture: tabs, topic outline, build phases, API map."""
    return load_content(MANIFEST_FILE)


def get_scaffold() -> dict[str, Any]:
    """Phase 2 placeholder content — not served to students in production UI."""
    return load_content(SCAFFOLD_FILE)


def _count_scaffold_section(scaffold: dict, key: str) -> int:
    items = scaffold.get(key, [])
    return len(items) if isinstance(items, list) else 0


def get_build_status() -> dict[str, Any]:
    """
    Compare live content counts vs manifest targets and scaffold queue.
    Used by developers and /api/assessment/build-status — not student-facing.
    """
    manifest = get_manifest()
    scaffold = get_scaffold()
    live = get_module_summary()
    inventory = manifest.get("content_inventory", {})

    live_key_map = {
        "head_to_toe_sequence": "sequence_steps",
        "body_systems": "body_systems",
        "red_flags_master": "red_flags",
        "practice_questions": "practice_total",
        "assessment_checklists": "checklists",
        "soap_exercises": "soap_exercises",
        "assess_next_scenarios": "assess_next_scenarios",
        "special_populations": "special_populations",
        "skills": "skills",
        "interview_techniques": "interview_techniques",
        "flashcards": "flashcards",
        "sbar_exercises": "sbar_exercises",
    }

    sections: list[dict[str, Any]] = []
    for key, spec in inventory.items():
        if not isinstance(spec, dict):
            continue
        mapped = live_key_map.get(key)
        current = live.get(mapped, 0) if mapped else 0
        scaffold_count = _count_scaffold_section(scaffold, key)

        target = spec.get("target", current)
        gap = max(0, target - current)
        sections.append({
            "section": key,
            "current": current,
            "target": target,
            "gap": gap,
            "scaffold_queued": scaffold_count,
            "phase": spec.get("phase", 1),
            "status": spec.get("status", "unknown"),
        })

    phase1_tabs = [t for t in manifest.get("tabs", []) if t.get("phase") == 1]
    phase2_tabs = [t for t in manifest.get("tabs", []) if t.get("phase") == 2]
    implemented = [t for t in manifest.get("tabs", []) if t.get("status") == "implemented"]
    planned = [t for t in manifest.get("tabs", []) if t.get("status") == "planned"]

    return {
        "module_id": manifest.get("module_id", "assessment"),
        "version": manifest.get("version"),
        "module_status": manifest.get("status"),
        "sections": sections,
        "tabs": {
            "implemented": len(implemented),
            "planned": len(planned),
            "phase_1": len(phase1_tabs),
            "phase_2": len(phase2_tabs),
        },
        "build_phases": manifest.get("build_phases", []),
        "scaffold_meta": scaffold.get("_meta", {}),
        "totals": {
            "live_items": live.get("items_total", 0),
            "scaffold_entries": sum(
                _count_scaffold_section(scaffold, k)
                for k in (
                    "assessment_checklists", "soap_exercises", "assess_next_scenarios",
                    "special_populations", "skills", "red_flags_master",
                    "practice_questions", "flashcards", "sbar_exercises",
                )
            ),
        },
    }


def get_topic_outline() -> list[dict[str, Any]]:
    return get_manifest().get("topic_outline", [])


def get_planned_tabs() -> list[dict[str, Any]]:
    return [t for t in get_manifest().get("tabs", []) if t.get("status") == "planned"]


def get_interactive_roadmap() -> list[dict[str, Any]]:
    return get_manifest().get("interactive_elements", [])


def validate_scaffold_entry(entry: dict, schema_name: str, schemas: dict) -> list[str]:
    """Return list of validation errors for a scaffold entry."""
    errors: list[str] = []
    schema = schemas.get(schema_name, {})
    for field in schema.get("required", []):
        if field not in entry or entry[field] in (None, "", []):
            errors.append(f"Missing required field: {field}")
    if entry.get("status") == "scaffold" and not entry.get("source", {}).get("verified_date"):
        pass  # expected for scaffold
    return errors


def validate_scaffold() -> dict[str, Any]:
    """Validate scaffold file structure for CI / pre-merge checks."""
    scaffold = get_scaffold()
    schemas = scaffold.get("_schemas", {})
    results: dict[str, list[dict]] = {}

    checks = [
        ("assessment_checklists", "assessment_checklist"),
        ("soap_exercises", "soap_exercise"),
        ("assess_next_scenarios", "assess_next_scenario"),
        ("special_populations", "special_population"),
        ("skills", "skill"),
        ("red_flags_master", "red_flag"),
        ("practice_questions", "practice_question"),
        ("flashcards", "flashcard"),
        ("sbar_exercises", "sbar_exercise"),
    ]

    total_errors = 0
    for section_key, schema_name in checks:
        entries = scaffold.get(section_key, [])
        section_results = []
        for entry in entries:
            errs = validate_scaffold_entry(entry, schema_name, schemas)
            if errs:
                total_errors += len(errs)
                section_results.append({"id": entry.get("id", "?"), "errors": errs})
        if section_results:
            results[section_key] = section_results

    return {
        "valid": total_errors == 0,
        "error_count": total_errors,
        "sections_checked": len(checks),
        "entries_checked": sum(len(scaffold.get(k, [])) for k, _ in checks),
        "issues": results,
    }