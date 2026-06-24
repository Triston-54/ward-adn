"""NURS 147 — Mental Health Nursing module."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import MentalHealthDrillCheck, ModuleProgressReport
from app.services.mental_health_manifest import get_build_status, get_manifest
from app.services.mental_health_service import (
    MODULE_ID,
    check_communication_scenario_answer,
    check_de_escalation_scenario_answer,
    check_safety_drill_answer,
    default_source,
    get_communication_barriers,
    get_communication_scenarios,
    get_de_escalation,
    get_disorders,
    get_module_summary,
    get_practice_questions,
    get_safety_drill_questions,
    get_safety_risk_flags,
    get_screening_tools,
    get_therapeutic_communication,
)
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["mental_health"])
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


@router.get("/mental-health")
async def mental_health_redirect():
    return RedirectResponse(url="/modules/mental-health", status_code=301)


@router.get("/modules/mental-health", response_class=HTMLResponse)
async def mental_health_page(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/mental_health.html", ctx)


@router.get("/api/mental-health/stats")
async def mental_health_stats(db: AsyncSession = Depends(get_db)):
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


@router.get("/api/mental-health/manifest")
async def mental_health_manifest():
    return {"manifest": get_manifest(), "build_status": get_build_status()}


@router.post("/api/mental-health/progress")
async def report_progress(data: ModuleProgressReport, db: AsyncSession = Depends(get_db)):
    mod = await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}


@router.get("/api/mental-health/communication")
async def communication_api():
    return {
        "techniques": get_therapeutic_communication(),
        "barriers": get_communication_barriers(),
        "source": default_source().model_dump(),
    }


@router.get("/api/mental-health/safety-risk")
async def safety_risk_api():
    return {
        "flags": get_safety_risk_flags(),
        "screening_tools": get_screening_tools(),
        "source": default_source().model_dump(),
    }


@router.get("/api/mental-health/safety-drill")
async def safety_drill_api(count: int = Query(5, ge=1, le=10)):
    return {
        "questions": get_safety_drill_questions(count),
        "source": default_source().model_dump(),
    }


@router.post("/api/mental-health/safety-drill/check")
async def check_safety_drill(req: MentalHealthDrillCheck, db: AsyncSession = Depends(get_db)):
    result = check_safety_drill_answer(req.question_id, req.selected_index, req.selected_option)
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="safety_drill",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/mental-health/communication-scenarios")
async def communication_scenarios_api():
    return {
        "scenarios": get_communication_scenarios(),
        "source": default_source().model_dump(),
    }


@router.get("/api/mental-health/disorders")
async def disorders_api():
    return {
        "disorders": get_disorders(),
        "source": default_source().model_dump(),
    }


@router.get("/api/mental-health/de-escalation")
async def de_escalation_api():
    return {
        "items": get_de_escalation(),
        "source": default_source().model_dump(),
    }


@router.post("/api/mental-health/de-escalation/check")
async def check_de_escalation(req: MentalHealthDrillCheck, db: AsyncSession = Depends(get_db)):
    result = check_de_escalation_scenario_answer(
        req.question_id, req.selected_index, req.selected_option
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="de_escalation",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/mental-health/practice")
async def practice_api(count: int = Query(10, ge=1, le=15)):
    return {
        "questions": get_practice_questions(count),
        "source": default_source().model_dump(),
    }


@router.post("/api/mental-health/communication-scenarios/check")
async def check_communication_scenario(
    req: MentalHealthDrillCheck, db: AsyncSession = Depends(get_db)
):
    result = check_communication_scenario_answer(
        req.question_id, req.selected_index, req.selected_option
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="communication",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}