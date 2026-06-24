"""Microbiology module — infection control, chain builder, scenarios, practice."""
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ModuleProgressReport
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress
from app.services.microbiology_service import (
    MODULE_ID,
    build_clipboard_text,
    build_flashcards_markdown,
    build_study_sheet_html,
    default_source,
    evaluate_chain_break,
    get_break_chain_scenarios,
    get_break_points,
    get_concepts,
    get_gram_stain,
    get_hai_types,
    get_hand_hygiene,
    get_infection_chain,
    get_microbe_classification,
    get_module_summary,
    get_pathogen_flashcards,
    get_pathogens,
    get_practice_questions,
    get_ppe_guide,
    get_what_if_scenarios,
    get_chain_interventions,
)

router = APIRouter(tags=["microbiology"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


class ChainBreakRequest(BaseModel):
    link_id: str
    intervention_id: str


async def _module_context(db: AsyncSession) -> dict:
    stats = await get_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    summary = get_module_summary()
    return {
        "stats": stats,
        "module_progress": mod,
        "summary": summary,
        "infection_chain": get_infection_chain(),
        "concepts": get_concepts(),
    }


@router.get("/microbiology")
async def microbiology_redirect():
    return RedirectResponse(url="/modules/microbiology", status_code=301)


@router.get("/modules/microbiology", response_class=HTMLResponse)
async def microbiology_page(request: Request, db: AsyncSession = Depends(get_db)):
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/microbiology.html", ctx)


@router.get("/api/microbiology/stats")
async def microbiology_stats(db: AsyncSession = Depends(get_db)):
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


@router.post("/api/microbiology/progress")
async def report_progress(data: ModuleProgressReport, db: AsyncSession = Depends(get_db)):
    mod = await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}


@router.get("/api/microbiology/infection-chain")
async def infection_chain_api():
    return {
        "links": get_infection_chain(),
        "interventions": get_chain_interventions(),
        "source": default_source().model_dump(),
    }


@router.post("/api/microbiology/chain-break")
async def chain_break_api(req: ChainBreakRequest):
    result = evaluate_chain_break(req.link_id, req.intervention_id)
    result["source"] = default_source().model_dump()
    return result


@router.get("/api/microbiology/classification")
async def classification_api():
    return {"types": get_microbe_classification(), "source": default_source().model_dump()}


@router.get("/api/microbiology/pathogens")
async def pathogens_api():
    return {"pathogens": get_pathogens(), "source": default_source().model_dump()}


@router.get("/api/microbiology/concepts")
async def concepts_api():
    return {"concepts": get_concepts(), "source": default_source().model_dump()}


@router.get("/api/microbiology/gram-stain")
async def gram_stain_api():
    return {**get_gram_stain(), "source": default_source().model_dump()}


@router.get("/api/microbiology/clinical")
async def clinical_api():
    return {
        "hand_hygiene": get_hand_hygiene(),
        "ppe": get_ppe_guide(),
        "hai_types": get_hai_types(),
        "source": default_source().model_dump(),
    }


@router.get("/api/microbiology/scenarios/break-chain")
async def break_chain_api(count: int = Query(4, le=8)):
    return {"scenarios": get_break_chain_scenarios(count)}


@router.get("/api/microbiology/scenarios/what-if")
async def what_if_api(count: int = Query(3, le=6)):
    return {"scenarios": get_what_if_scenarios(count)}


@router.get("/api/microbiology/practice")
async def practice_api(
    count: int = Query(10, le=20),
    mode: str = Query("mixed", description="mixed | nclex | application"),
):
    questions = get_practice_questions(count, mode)
    return {"questions": questions, "count": len(questions), "mode": mode}


@router.get("/api/microbiology/break-points")
async def break_points_api():
    return {"break_points": get_break_points(), "source": default_source().model_dump()}


@router.get("/api/microbiology/flashcards")
async def flashcards_api(count: Optional[int] = Query(None, ge=1, le=50)):
    cards = get_pathogen_flashcards(count)
    return {"cards": cards, "count": len(cards), "source": default_source().model_dump()}


@router.get("/api/microbiology/export/clipboard")
async def export_clipboard():
    return {"format": "text", "content": build_clipboard_text()}


@router.get("/api/microbiology/export/study-sheet", response_class=HTMLResponse)
async def export_study_sheet():
    """Printable HTML study sheet — use browser Print → Save as PDF."""
    return HTMLResponse(build_study_sheet_html())


@router.get("/api/microbiology/export/flashcards")
async def export_flashcards_markdown():
    return {"format": "markdown", "content": build_flashcards_markdown()}