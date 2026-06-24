"""NURS 148 — Maternal-Child Nursing (OB/Peds) module."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import MaternalChildDrillCheck, ModuleProgressReport
from app.services.maternal_child_manifest import get_build_status, get_manifest
from app.services.maternal_child_service import (
    MODULE_ID,
    check_complications_drill_answer,
    default_source,
    get_complications_drill_questions,
    build_flashcards_markdown,
    get_flashcards,
    get_labor_delivery,
    get_module_summary,
    get_pediatric_essentials,
    get_postpartum_newborn,
    get_practice_questions,
    get_pregnancy_stages,
    get_safety_red_flags,
)
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["maternal_child"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


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


@router.get("/maternal-child")
async def maternal_child_redirect():
    return RedirectResponse(url="/modules/maternal-child", status_code=301)


@router.get("/modules/maternal-child", response_class=HTMLResponse)
async def maternal_child_page(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/maternal_child.html", ctx)


@router.get("/api/maternal-child/stats")
async def maternal_child_stats(db: AsyncSession = Depends(get_db)):
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


@router.get("/api/maternal-child/manifest")
async def maternal_child_manifest():
    return {"manifest": get_manifest(), "build_status": get_build_status()}


@router.post("/api/maternal-child/progress")
async def report_progress(data: ModuleProgressReport, db: AsyncSession = Depends(get_db)):
    mod = await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}


@router.get("/api/maternal-child/antepartum")
async def antepartum_api():
    return {
        "topics": get_pregnancy_stages(),
        "source": default_source().model_dump(),
    }


@router.get("/api/maternal-child/intrapartum")
async def intrapartum_api():
    return {
        "topics": get_labor_delivery(),
        "source": default_source().model_dump(),
    }


@router.get("/api/maternal-child/postpartum-newborn")
async def postpartum_newborn_api():
    return {
        "topics": get_postpartum_newborn(),
        "source": default_source().model_dump(),
    }


@router.get("/api/maternal-child/pediatrics")
async def pediatrics_api():
    return {
        "topics": get_pediatric_essentials(),
        "source": default_source().model_dump(),
    }


@router.get("/api/maternal-child/safety")
async def safety_api():
    return {
        "flags": get_safety_red_flags(),
        "source": default_source().model_dump(),
    }


@router.get("/api/maternal-child/complications-drill")
async def complications_drill_api(count: int = Query(5, ge=1, le=10)):
    return {
        "questions": get_complications_drill_questions(count),
        "source": default_source().model_dump(),
    }


@router.post("/api/maternal-child/complications-drill/check")
async def check_complications_drill(
    req: MaternalChildDrillCheck,
    db: AsyncSession = Depends(get_db),
):
    result = check_complications_drill_answer(
        req.question_id,
        req.selected_index,
        req.selected_option,
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="complications_drill",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/maternal-child/flashcards")
async def flashcards_api(count: Optional[int] = Query(None, ge=1, le=50)):
    cards = get_flashcards(count)
    return {"cards": cards, "count": len(cards), "source": default_source().model_dump()}


@router.get("/api/maternal-child/export/flashcards")
async def export_flashcards_markdown():
    return {"format": "markdown", "content": build_flashcards_markdown()}


@router.get("/api/maternal-child/practice")
async def practice_api(count: int = Query(10, le=20)):
    questions = get_practice_questions(count)
    return {"questions": questions, "count": len(questions), "source": default_source().model_dump()}