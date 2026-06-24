"""Pharmacy Track — dashboard and module routes."""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ModuleProgressReport
from app.services.pharmacy_calculations_service import (
    MODULE_ID as CALC_MODULE_ID,
    check_practice_answer,
    default_source as calc_default_source,
    get_calc_types,
    get_clinical_scenarios,
    get_error_traps,
    get_module_content as get_calc_content,
    get_module_summary as get_calc_summary,
    get_practice_problems,
    get_topic_outline,
)
from app.services.pharmacy_manifest import get_build_status, get_manifest
from app.services.pharmacy_progress_service import get_pharmacy_dashboard_stats
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["pharmacy"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


async def _calculations_context(db: AsyncSession) -> dict:
    stats = await get_pharmacy_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == CALC_MODULE_ID), None)
    content = get_calc_content()
    return {
        "stats": stats,
        "nursing_stats": await get_dashboard_stats(db),
        "module_progress": mod,
        "content": content,
        "summary": get_calc_summary(),
        "manifest": get_manifest(),
        "tabs": [t for t in content.get("tabs", []) if t.get("status") == "implemented"],
    }


@router.get("/pharmacy", response_class=HTMLResponse)
async def pharmacy_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Dedicated Pharmacy Track dashboard."""
    stats = await get_pharmacy_dashboard_stats(db)
    nursing_stats = await get_dashboard_stats(db)
    stats["user"] = nursing_stats["user"]
    return templates.TemplateResponse(
        request,
        "pharmacy_dashboard.html",
        {
            "stats": stats,
            "nursing_stats": nursing_stats,
            "settings": settings,
            "active_track": "pharmacy",
        },
    )


@router.get("/api/pharmacy/stats")
async def pharmacy_stats(db: AsyncSession = Depends(get_db)):
    """Pharmacy Track aggregate progress."""
    return await get_pharmacy_dashboard_stats(db)


@router.get("/api/pharmacy/manifest")
async def pharmacy_manifest():
    return {"manifest": get_manifest(), "build_status": get_build_status()}


@router.get("/pharmacy/modules/calculations", response_class=HTMLResponse)
async def pharmacy_calculations_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Pharmacy Calculations module scaffold."""
    ctx = await _calculations_context(db)
    ctx["active_track"] = "pharmacy"
    ctx["stats"]["user"] = ctx["nursing_stats"]["user"]
    return templates.TemplateResponse(request, "modules/pharmacy_calculations.html", ctx)


@router.get("/api/pharmacy/calculations/stats")
async def pharmacy_calculations_stats(db: AsyncSession = Depends(get_db)):
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == CALC_MODULE_ID), None)
    return {
        "module_id": CALC_MODULE_ID,
        "percentage": mod.percentage if mod else 0,
        "items_completed": mod.items_completed if mod else 0,
        "items_total": mod.items_total if mod else MODULES[CALC_MODULE_ID]["total"],
        "streak_days": mod.streak_days if mod else 0,
        "summary": get_calc_summary(),
    }


@router.get("/api/pharmacy/calculations/content")
async def pharmacy_calculations_content():
    return {
        **get_calc_content(),
        "source": calc_default_source().model_dump(),
    }


@router.get("/api/pharmacy/calculations/topics")
async def pharmacy_calculations_topics():
    return {
        "topics": get_topic_outline(),
        "calc_types": get_calc_types(),
        "source": calc_default_source().model_dump(),
    }


@router.get("/api/pharmacy/calculations/practice")
async def pharmacy_calculations_practice():
    problems = get_practice_problems()
    return {
        "problems": [
            {k: v for k, v in p.items() if k != "correct_index"}
            for p in problems
        ],
        "count": len(problems),
        "source": calc_default_source().model_dump(),
    }


@router.get("/api/pharmacy/calculations/traps")
async def pharmacy_calculations_traps():
    return {
        "error_traps": get_error_traps(),
        "count": len(get_error_traps()),
        "source": calc_default_source().model_dump(),
    }


@router.get("/api/pharmacy/calculations/scenarios")
async def pharmacy_calculations_scenarios():
    return {
        "scenarios": get_clinical_scenarios(),
        "count": len(get_clinical_scenarios()),
        "source": calc_default_source().model_dump(),
    }


class PracticeAnswerRequest(BaseModel):
    problem_id: str
    selected_index: int


@router.post("/api/pharmacy/calculations/practice/check")
async def pharmacy_calculations_practice_check(data: PracticeAnswerRequest):
    return check_practice_answer(data.problem_id, data.selected_index)


@router.post("/api/pharmacy/calculations/progress")
async def pharmacy_calculations_progress(
    data: ModuleProgressReport, db: AsyncSession = Depends(get_db)
):
    mod = await update_progress(
        db,
        module_id=CALC_MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}