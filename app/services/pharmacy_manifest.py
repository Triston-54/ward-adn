"""Pharmacy Track architecture manifest and build status."""
from __future__ import annotations

from typing import Any, Optional

from app.services.content_loader import load_content
from app.services.pharmacy_calculations_service import get_module_summary as calc_summary

MANIFEST_FILE = "pharmacy_manifest.json"


def get_manifest() -> dict[str, Any]:
    return load_content(MANIFEST_FILE)


def get_all_module_specs() -> list[dict[str, Any]]:
    """Flatten stage modules into a single list with stage metadata."""
    manifest = get_manifest()
    modules: list[dict[str, Any]] = []
    for stage in manifest.get("stages", []):
        for mod in stage.get("modules", []):
            modules.append({
                **mod,
                "stage_id": stage["id"],
                "stage_title": stage["title"],
                "stage_order": stage.get("order", 0),
            })
    return modules


def get_module_spec(module_id: str) -> Optional[dict[str, Any]]:
    for mod in get_all_module_specs():
        if mod.get("id") == module_id:
            return mod
    return None


def _live_summary_for_module(module_id: str) -> dict[str, Any]:
    if module_id == "pharmacy_calculations":
        return calc_summary()
    return {}


def get_build_status() -> dict[str, Any]:
    manifest = get_manifest()
    inventory = manifest.get("content_inventory", {})

    sections: dict[str, dict[str, Any]] = {}
    for key, spec in inventory.items():
        live = _live_summary_for_module(key)
        live_key = spec.get("live_key", "")
        current = live.get(live_key, 0) if live_key else 0
        target = spec.get("target", 0)
        sections[key] = {
            "current": current,
            "target": target,
            "complete_pct": round((current / target) * 100) if target else 0,
        }

    stages = manifest.get("stages", [])
    total_modules = sum(len(s.get("modules", [])) for s in stages)
    scaffold_modules = sum(
        1
        for mod in get_all_module_specs()
        if mod.get("status") in ("scaffold", "in_progress", "implemented")
    )

    return {
        "track_id": manifest.get("track_id"),
        "version": manifest.get("version"),
        "status": manifest.get("status"),
        "stages_total": len(stages),
        "modules_total": total_modules,
        "modules_started": scaffold_modules,
        "sections": sections,
        "build_phases": manifest.get("build_phases", []),
    }