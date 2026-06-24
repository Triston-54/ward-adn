"""Pharmacy Track progress aggregation and next-step recommendations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModuleCompletion
from app.services.pharmacy_manifest import get_all_module_specs, get_manifest
from app.services.progress_service import (
    MODULES,
    PHARMACY_MODULE_IDS,
    ensure_modules,
    get_all_progress,
)


def _progress_for_module(
    module_id: str, completions: dict[str, ModuleCompletion]
) -> Optional[ModuleCompletion]:
    return completions.get(module_id)


def _stage_progress(
    stage: dict[str, Any], completions: dict[str, ModuleCompletion]
) -> dict[str, Any]:
    modules_out: list[dict[str, Any]] = []
    total_pct = 0.0
    active_count = 0

    for mod_spec in stage.get("modules", []):
        mod_id = mod_spec.get("id", "")
        completion = _progress_for_module(mod_id, completions)
        pct = completion.percentage if completion else 0.0
        items_completed = completion.items_completed if completion else 0
        items_total = (
            completion.items_total
            if completion
            else mod_spec.get("items_total", 0)
        )
        last_practiced = completion.last_practiced if completion else None

        if mod_spec.get("status") not in ("planned",):
            active_count += 1
            total_pct += pct

        modules_out.append({
            **mod_spec,
            "percentage": pct,
            "items_completed": items_completed,
            "items_total": items_total,
            "last_practiced": last_practiced,
            "has_progress_record": completion is not None,
        })

    stage_pct = round(total_pct / active_count, 1) if active_count else 0.0
    return {
        "id": stage["id"],
        "order": stage.get("order", 0),
        "title": stage["title"],
        "subtitle": stage.get("subtitle", ""),
        "description": stage.get("description", ""),
        "status": stage.get("status", "planned"),
        "optional": stage.get("optional", False),
        "estimated_weeks": stage.get("estimated_weeks"),
        "percentage": stage_pct,
        "modules": modules_out,
    }


def _recommend_next_steps(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return ordered recommendations based on stage order and module completion."""
    recommendations: list[dict[str, Any]] = []

    for stage in stages:
        for mod in stage.get("modules", []):
            if mod.get("status") == "planned" and not mod.get("url"):
                continue
            if mod.get("percentage", 0) < 100:
                recommendations.append({
                    "type": "continue" if mod.get("items_completed", 0) > 0 else "start",
                    "stage_id": stage["id"],
                    "stage_title": stage["title"],
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "url": mod.get("url"),
                    "percentage": mod.get("percentage", 0),
                    "priority": mod.get("priority", "P2"),
                })
                if len(recommendations) >= 3:
                    return recommendations

    for stage in stages:
        for mod in stage.get("modules", []):
            if mod.get("status") == "planned" and not mod.get("url"):
                recommendations.append({
                    "type": "upcoming",
                    "stage_id": stage["id"],
                    "stage_title": stage["title"],
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "url": None,
                    "percentage": 0,
                    "priority": mod.get("priority", "P2"),
                })
                return recommendations[:3]

    return recommendations


def _recent_modules(
    stages: list[dict[str, Any]], limit: int = 3
) -> list[dict[str, Any]]:
    recent: list[dict[str, Any]] = []
    for stage in stages:
        for mod in stage.get("modules", []):
            lp = mod.get("last_practiced")
            if lp and mod.get("url"):
                recent.append({**mod, "stage_title": stage["title"], "last_practiced": lp})
    recent.sort(key=lambda m: m["last_practiced"], reverse=True)
    return recent[:limit]


async def get_pharmacy_dashboard_stats(session: AsyncSession) -> dict[str, Any]:
    """Aggregate Pharmacy Track stats for the dedicated dashboard."""
    await ensure_modules(session)
    manifest = get_manifest()
    all_completions = await get_all_progress(session)
    completion_map = {m.module_id: m for m in all_completions}

    stages = [
        _stage_progress(stage, completion_map)
        for stage in manifest.get("stages", [])
    ]

    pharmacy_modules = [
        m for m in all_completions if m.module_id in PHARMACY_MODULE_IDS
    ]
    total_pct = (
        sum(m.percentage for m in pharmacy_modules) / len(pharmacy_modules)
        if pharmacy_modules
        else 0.0
    )
    total_completed = sum(m.items_completed for m in pharmacy_modules)
    total_items = sum(m.items_total for m in pharmacy_modules)
    max_streak = max((m.streak_days for m in pharmacy_modules), default=0)

    current_stage = next(
        (s for s in stages if s["percentage"] < 100 and s["status"] != "planned"),
        stages[0] if stages else None,
    )

    return {
        "track": manifest,
        "stages": stages,
        "overall_percentage": round(total_pct, 1),
        "total_completed": total_completed,
        "total_items": total_items,
        "max_streak": max_streak,
        "current_stage": current_stage,
        "recommendations": _recommend_next_steps(stages),
        "recent_modules": _recent_modules(stages),
        "module_catalog": {
            k: v for k, v in MODULES.items() if v.get("track") == "pharmacy"
        },
        "build_status": {
            "version": manifest.get("version"),
            "status": manifest.get("status"),
            "phases": manifest.get("build_phases", []),
        },
    }