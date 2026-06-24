"""Pathophysiology module — disease processes, compare/contrast, scenarios, practice."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ModuleProgressReport
from app.services.pathophysiology_manifest import get_build_status, get_manifest
from app.services.pathophysiology_service import (
    MODULE_ID,
    check_breakdown_answer,
    default_source,
    get_breakdown_scenarios,
    get_compare_contrast_pairs,
    get_core_concepts,
    get_disease_processes,
    build_flashcards_markdown,
    get_flashcards,
    get_module_summary,
    get_practice_questions,
)
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["pathophysiology"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


class BreakdownCheckRequest(BaseModel):
    scenario_id: str
    selected_index: int
    selected_option: Optional[str] = None


async def _module_context(db: AsyncSession) -> dict:
    stats = await get_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    summary = get_module_summary()
    manifest = get_manifest()
    return {
        "stats": stats,
        "module_progress": mod,
        "summary": summary,
        "manifest": manifest,
        "tabs": [t for t in manifest.get("tabs", []) if t.get("status") == "implemented"],
    }


@router.get("/pathophysiology")
async def pathophysiology_redirect():
    return RedirectResponse(url="/modules/pathophysiology", status_code=301)


@router.get("/modules/pathophysiology", response_class=HTMLResponse)
async def pathophysiology_page(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/pathophysiology.html", ctx)


@router.get("/api/pathophysiology/stats")
async def pathophysiology_stats(db: AsyncSession = Depends(get_db)):
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    return {
        "module_id": MODULE_ID,
        "percentage": mod.percentage if mod else 0,
        "items_completed": mod.items_completed if mod else 0,
        "items_total": mod.items_total if mod else MODULES[MODULE_ID]["total"],
        "streak_days": mod.streak_days if mod else 0,
        "summary": get_module_summary(),
    }


@router.get("/api/pathophysiology/manifest")
async def pathophysiology_manifest():
    return {"manifest": get_manifest(), "build_status": get_build_status()}


@router.post("/api/pathophysiology/progress")
async def report_progress(data: ModuleProgressReport, db: AsyncSession = Depends(get_db)):
    mod = await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}


@router.get("/api/pathophysiology/concepts")
async def concepts_api():
    return {
        "concepts": get_core_concepts(),
        "source": default_source().model_dump(),
    }


@router.get("/api/pathophysiology/diseases")
async def diseases_api():
    return {
        "diseases": get_disease_processes(),
        "source": default_source().model_dump(),
    }


@router.get("/api/pathophysiology/compare")
async def compare_api():
    return {
        "pairs": get_compare_contrast_pairs(),
        "source": default_source().model_dump(),
    }


@router.get("/api/pathophysiology/scenarios/breakdown")
async def breakdown_scenarios_api(count: int = Query(5, ge=1, le=8)):
    return {
        "scenarios": get_breakdown_scenarios(count),
        "source": default_source().model_dump(),
    }


@router.post("/api/pathophysiology/scenarios/check")
async def check_breakdown_api(req: BreakdownCheckRequest, db: AsyncSession = Depends(get_db)):
    result = check_breakdown_answer(req.scenario_id, req.selected_index, req.selected_option)
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="scenarios",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/pathophysiology/flashcards")
async def flashcards_api(count: Optional[int] = Query(None, ge=1, le=30)):
    cards = get_flashcards(count)
    return {"cards": cards, "count": len(cards), "source": default_source().model_dump()}


@router.get("/api/pathophysiology/export/flashcards")
async def export_flashcards_markdown():
    return {"format": "markdown", "content": build_flashcards_markdown()}


@router.get("/api/pathophysiology/practice")
async def practice_api(count: int = Query(10, le=18)):
    questions = get_practice_questions(count)
    return {"questions": questions, "count": len(questions)}