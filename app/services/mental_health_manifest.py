"""Mental Health module architecture manifest and build status."""
from __future__ import annotations

from typing import Any

from app.services.content_loader import load_content
from app.services.mental_health_service import get_module_summary

MANIFEST_FILE = "mental_health_manifest.json"


def get_manifest() -> dict[str, Any]:
    return load_content(MANIFEST_FILE)


def get_build_status() -> dict[str, Any]:
    manifest = get_manifest()
    live = get_module_summary()
    inventory = manifest.get("content_inventory", {})

    sections: dict[str, dict[str, Any]] = {}
    for key, spec in inventory.items():
        live_key = spec.get("live_key", "")
        current = live.get(live_key, 0) if live_key else 0
        target = spec.get("target", 0)
        sections[key] = {
            "current": current,
            "target": target,
            "complete_pct": round((current / target) * 100) if target else 0,
        }

    tabs = manifest.get("tabs", [])
    implemented = sum(1 for t in tabs if t.get("status") == "implemented")

    return {
        "module_id": manifest.get("module_id"),
        "version": manifest.get("version"),
        "status": manifest.get("status"),
        "tabs_total": len(tabs),
        "tabs_implemented": implemented,
        "sections": sections,
        "live_summary": live,
        "build_phases": manifest.get("build_phases", []),
    }