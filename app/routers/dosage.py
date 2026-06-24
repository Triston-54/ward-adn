"""NURS 145 — Drug & Dosage Calculations module."""
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import (
    DosageCalculationRequest,
    DosageCalculationResult,
    DosagePracticeCheck,
    ModuleProgressReport,
    SavedCalculation,
    SavedCalculationCreate,
    SavedCalculationOut,
)
from app.services.content_loader import load_content
from app.services.dosage_service import (
    MODULE_ID,
    calculate_dosage,
    check_practice_answer,
    default_source,
    get_drug_class,
    get_drug_classes,
    get_first_principles,
    get_module_content,
    get_pharm_categories,
    get_pharmacology_safety,
    get_practice_problems,
)
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["dosage"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


async def _module_context(db: AsyncSession) -> dict:
    stats = await get_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    data = get_module_content()
    problems = get_practice_problems()
    return {
        "stats": stats,
        "module_progress": mod,
        "calc_types": data.get("calc_types", []),
        "error_trap_count": len(data.get("error_traps", [])),
        "practice_count": len(problems),
        "pharm_safety_count": len(data.get("pharmacology_safety", [])),
        "drug_class_count": len(data.get("drug_classes", [])),
        "pharm_count": len(data.get("pharmacology_safety", [])) + len(data.get("drug_classes", [])),
    }


@router.get("/dosage")
async def dosage_redirect():
    """Legacy route → new module path."""
    return RedirectResponse(url="/modules/dosage", status_code=301)


@router.get("/modules/dosage", response_class=HTMLResponse)
async def dosage_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the Dosage Calculations module."""
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/dosage.html", ctx)


@router.get("/api/dosage/stats")
async def dosage_stats(db: AsyncSession = Depends(get_db)):
    """Module-specific progress stats."""
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    data = get_module_content()
    fav_count = await db.execute(select(SavedCalculation))
    favorites = len(list(fav_count.scalars().all()))
    return {
        "module_id": MODULE_ID,
        "percentage": mod.percentage if mod else 0,
        "items_completed": mod.items_completed if mod else 0,
        "items_total": mod.items_total if mod else MODULES[MODULE_ID]["total"],
        "streak_days": mod.streak_days if mod else 0,
        "last_practiced": mod.last_practiced.isoformat() if mod and mod.last_practiced else None,
        "practice_count": len(data.get("practice_problems", [])),
        "favorites_count": favorites,
    }


@router.post("/api/dosage/progress")
async def report_progress(data: ModuleProgressReport, db: AsyncSession = Depends(get_db)):
    """Save study activity to SQLite."""
    mod = await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=data.items_studied,
        activity_type=data.activity_type,
        score=data.score,
    )
    return {"percentage": mod.percentage, "items_completed": mod.items_completed}


@router.post("/api/dosage/calculate", response_model=DosageCalculationResult)
async def calculate_api(req: DosageCalculationRequest):
    """Step-by-step dosage calculation with SymPy derivation."""
    return calculate_dosage(req)


@router.get("/api/dosage/first-principles/{calc_type}")
async def first_principles(calc_type: str):
    """First-principles dimensional analysis guide for a calculation type."""
    fp = get_first_principles(calc_type)
    return {
        "calc_type": calc_type,
        "principles": fp,
        "source": default_source().model_dump(),
    }


@router.get("/api/dosage/content")
async def get_content():
    """Error traps, pharmacology safety, drug classes, and calculation types."""
    return {
        "calc_types": get_module_content().get("calc_types", []),
        "error_traps": get_module_content().get("error_traps", []),
        "pharmacology_safety": get_pharmacology_safety(),
        "drug_classes": get_drug_classes(),
        "pharm_categories": get_pharm_categories(),
        "source": default_source().model_dump(),
    }


@router.get("/api/dosage/pharm/{class_id}")
async def get_pharm_class(class_id: str):
    """Single drug class reference card."""
    drug_class = get_drug_class(class_id)
    if not drug_class:
        return {"error": "Drug class not found", "class_id": class_id}
    return {"drug_class": drug_class, "source": default_source().model_dump()}


@router.get("/api/dosage/practice")
async def get_practice():
    """Return interactive practice problems."""
    problems = get_practice_problems()
    public = [
        {
            "id": p["id"],
            "calc_type": p.get("calc_type", ""),
            "question": p["question"],
            "options": p["options"],
        }
        for p in problems
    ]
    return {"problems": public, "source": default_source().model_dump()}


@router.post("/api/dosage/practice/check")
async def check_practice(req: DosagePracticeCheck, db: AsyncSession = Depends(get_db)):
    """Check a practice answer with immediate feedback."""
    result = check_practice_answer(req.problem_id, req.selected_index)
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="practice",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/dosage/favorites", response_model=list[SavedCalculationOut])
async def list_favorites(db: AsyncSession = Depends(get_db)):
    """List saved favorite calculations."""
    result = await db.execute(
        select(SavedCalculation).order_by(SavedCalculation.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/api/dosage/favorites", response_model=SavedCalculationOut)
async def save_favorite(req: SavedCalculationCreate, db: AsyncSession = Depends(get_db)):
    """Save a calculation as a favorite."""
    saved = SavedCalculation(
        calc_type=req.calc_type,
        label=req.label,
        inputs_json=req.inputs_json,
        result_json=req.result_json,
        is_favorite=True,
    )
    db.add(saved)
    await db.flush()
    await update_progress(db, module_id=MODULE_ID, items_completed=1, activity_type="calculator")
    return saved


@router.delete("/api/dosage/favorites/{calc_id}")
async def delete_favorite(calc_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a saved calculation."""
    result = await db.execute(select(SavedCalculation).where(SavedCalculation.id == calc_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()
    return {"status": "deleted", "id": calc_id}