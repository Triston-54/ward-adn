"""Health Assessment module (NURS 146) — head-to-toe, systems, red flags, practice."""
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import (
    AssessmentFlashcardReview,
    AssessmentPracticeCheck,
    AssessmentRedFlagDrillCheck,
    AssessmentScenarioCheck,
    AssessmentSoapValidate,
    ModuleProgressReport,
    UploadedFile,
)
from app.services.assessment_manifest import (
    get_build_status,
    get_interactive_roadmap,
    get_manifest,
    get_planned_tabs,
    get_scaffold,
    get_topic_outline,
)
from app.services.assessment_export import (
    build_checklists_pack_html,
    build_head_to_toe_sheet_html,
    build_red_flags_sheet_html,
)
from app.services.assessment_service import (
    ITEMS_TOTAL,
    MODULE_ID,
    check_assess_next_answer,
    check_practice_answer,
    check_red_flag_drill_answer,
    default_source,
    build_flashcards_markdown,
    get_assess_next_scenarios,
    get_assessment_checklist,
    get_assessment_checklists,
    get_body_system,
    get_body_systems,
    get_due_flashcards,
    get_flashcard_stats,
    get_head_to_toe_sequence,
    get_interview_techniques,
    get_module_summary,
    get_pain_assessment,
    get_practice_questions,
    get_red_flag_drill_questions,
    get_red_flags,
    get_skills,
    get_sbar_exercise,
    get_sbar_exercises,
    get_soap_exercise,
    get_soap_exercises,
    get_special_population,
    get_special_populations,
    get_vital_signs,
    record_flashcard_review,
    validate_soap_submission,
)
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress

router = APIRouter(tags=["assessment"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


async def _module_context(db: AsyncSession) -> dict:
    stats = await get_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    summary = get_module_summary()
    fc_stats = await get_flashcard_stats(db)
    return {
        "stats": stats,
        "module_progress": mod,
        "summary": summary,
        "flashcard_stats": fc_stats,
        "head_to_toe": get_head_to_toe_sequence(),
        "body_systems": get_body_systems(),
        "red_flag_count": summary["red_flags"],
    }


@router.get("/assessment")
async def assessment_redirect():
    """Legacy route → new module path."""
    return RedirectResponse(url="/modules/assessment", status_code=301)


@router.get("/modules/assessment", response_class=HTMLResponse)
async def assessment_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the Health Assessment module."""
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/assessment.html", ctx)


@router.get("/api/assessment/manifest")
async def assessment_manifest_api():
    """Module architecture — tabs, topics, build phases (developer/planning)."""
    manifest = get_manifest()
    return {
        "manifest": manifest,
        "topic_outline": get_topic_outline(),
        "planned_tabs": get_planned_tabs(),
        "interactive_roadmap": get_interactive_roadmap(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/scaffold")
async def assessment_scaffold_api():
    """Phase 2 placeholder content — not for student production UI."""
    scaffold = get_scaffold()
    meta = scaffold.get("_meta", {})
    public = {k: v for k, v in scaffold.items() if not k.startswith("_")}
    return {
        "meta": meta,
        "scaffold": public,
        "schemas": scaffold.get("_schemas", {}),
    }


@router.get("/api/assessment/build-status")
async def assessment_build_status_api():
    """Live vs target content counts and scaffold queue."""
    return get_build_status()


@router.get("/api/assessment/stats")
async def assessment_stats(db: AsyncSession = Depends(get_db)):
    """Module-specific progress stats."""
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    fc = await get_flashcard_stats(db)
    return {
        "module_id": MODULE_ID,
        "percentage": mod.percentage if mod else 0,
        "items_completed": mod.items_completed if mod else 0,
        "items_total": mod.items_total if mod else MODULES[MODULE_ID]["total"],
        "streak_days": mod.streak_days if mod else 0,
        "last_practiced": mod.last_practiced.isoformat() if mod and mod.last_practiced else None,
        "summary": get_module_summary(),
        "flashcards": fc,
    }


@router.post("/api/assessment/progress")
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


@router.get("/api/assessment/content")
async def assessment_content_api():
    """Vital signs, pain assessment, interview techniques, and skills."""
    return {
        "vital_signs": get_vital_signs(),
        "pain_assessment": get_pain_assessment(),
        "interview_techniques": get_interview_techniques(),
        "skills": get_skills(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/head-to-toe")
async def head_to_toe_api():
    """Head-to-toe assessment sequence."""
    return {
        "sequence": get_head_to_toe_sequence(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/systems")
async def systems_api():
    """All body systems for system-by-system study."""
    return {
        "systems": get_body_systems(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/systems/{system_id}")
async def system_detail_api(system_id: str):
    """Single body system with normal/abnormal findings."""
    system = get_body_system(system_id)
    if not system:
        return {"error": "System not found", "system_id": system_id}
    return {"system": system, "source": default_source().model_dump()}


@router.get("/api/assessment/red-flags")
async def red_flags_api():
    """Critical findings requiring immediate action."""
    return {
        "red_flags": get_red_flags(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/red-flag-drill")
async def red_flag_drill_api(
    count: int = Query(5, le=10),
    system: Optional[str] = Query(None),
):
    """Red flag triage drill — select correct immediate nursing action for a finding."""
    questions = get_red_flag_drill_questions(count, system)
    public = [
        {
            "id": q["id"],
            "finding": q["finding"],
            "system": q.get("system"),
            "priority": q.get("priority"),
            "options": q["options"],
        }
        for q in questions
    ]
    return {"questions": public, "count": len(public), "source": default_source().model_dump()}


@router.post("/api/assessment/red-flag-drill/check")
async def check_red_flag_drill(req: AssessmentRedFlagDrillCheck, db: AsyncSession = Depends(get_db)):
    """Check red flag drill answer with escalation path and clinical reasoning."""
    result = check_red_flag_drill_answer(
        req.flag_id, req.selected_index, req.selected_option
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="red_flags",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/assessment/practice")
async def practice_api(
    count: int = Query(10, le=20),
    mode: str = Query("mixed", description="mixed | priority | red_flags"),
    system: Optional[str] = Query(None),
):
    """NCLEX-style practice questions."""
    questions = get_practice_questions(count, mode, system)
    public = [
        {
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "system": q.get("system"),
            "nclex_category": q.get("nclex_category"),
        }
        for q in questions
    ]
    return {"questions": public, "count": len(public), "mode": mode, "source": default_source().model_dump()}


@router.post("/api/assessment/practice/check")
async def check_practice(req: AssessmentPracticeCheck, db: AsyncSession = Depends(get_db)):
    """Check a practice answer with immediate teaching feedback."""
    result = check_practice_answer(
        req.question_id, req.selected_index, req.selected_option
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="practice",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/assessment/special-populations")
async def special_populations_api():
    """Pediatric, geriatric, and OB assessment considerations."""
    return {
        "populations": get_special_populations(),
        "source": default_source().model_dump(),
    }


@router.get("/api/assessment/special-populations/{pop_id}")
async def special_population_detail_api(pop_id: str):
    """Single special population with normal/abnormal and red flags."""
    pop = get_special_population(pop_id)
    if not pop:
        return {"error": "Population not found", "pop_id": pop_id}
    return {"population": pop, "source": default_source().model_dump()}


@router.get("/api/assessment/checklists")
async def checklists_api():
    """Interactive assessment checklists for clinical documentation practice."""
    checklists = get_assessment_checklists()
    public = [
        {
            "id": c["id"],
            "title": c["title"],
            "category": c.get("category"),
            "description": c.get("description"),
            "item_count": len(c.get("items", [])),
        }
        for c in checklists
    ]
    return {"checklists": public, "source": default_source().model_dump()}


@router.get("/api/assessment/checklists/{checklist_id}")
async def checklist_detail_api(checklist_id: str):
    """Full checklist with items for interactive study."""
    checklist = get_assessment_checklist(checklist_id)
    if not checklist:
        return {"error": "Checklist not found", "checklist_id": checklist_id}
    return {"checklist": checklist, "source": default_source().model_dump()}


@router.get("/api/assessment/soap")
async def soap_exercises_api():
    """SOAP documentation practice scenarios."""
    exercises = get_soap_exercises()
    public = [
        {
            "id": e["id"],
            "title": e["title"],
            "patient_context": e.get("patient_context"),
        }
        for e in exercises
    ]
    return {"exercises": public, "source": default_source().model_dump()}


@router.get("/api/assessment/soap/{exercise_id}")
async def soap_exercise_detail_api(exercise_id: str):
    """Single SOAP exercise with findings and model documentation."""
    exercise = get_soap_exercise(exercise_id)
    if not exercise:
        return {"error": "Exercise not found", "exercise_id": exercise_id}
    return {"exercise": exercise, "source": default_source().model_dump()}


@router.post("/api/assessment/soap/validate")
async def soap_validate_api(req: AssessmentSoapValidate, db: AsyncSession = Depends(get_db)):
    """Rubric-based SOAP documentation feedback with section scores."""
    result = validate_soap_submission(
        req.exercise_id,
        req.subjective,
        req.objective,
        req.assessment,
        req.plan,
    )
    if not result.get("valid"):
        return result
    if result.get("passed"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="documentation",
            score=float(result["overall_score"]),
        )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/assessment/sbar")
async def sbar_exercises_api():
    """SBAR handoff practice scenarios."""
    exercises = get_sbar_exercises()
    public = [
        {
            "id": e["id"],
            "title": e["title"],
            "situation": e.get("situation"),
        }
        for e in exercises
    ]
    return {"exercises": public, "source": default_source().model_dump()}


@router.get("/api/assessment/sbar/{exercise_id}")
async def sbar_exercise_detail_api(exercise_id: str):
    """Single SBAR exercise with model handoff and teaching points."""
    exercise = get_sbar_exercise(exercise_id)
    if not exercise:
        return {"error": "Exercise not found", "exercise_id": exercise_id}
    return {"exercise": exercise, "source": default_source().model_dump()}


@router.get("/api/assessment/flashcards")
async def flashcards_api(
    count: int = Query(20, ge=1, le=60),
    system: Optional[str] = Query(None),
    due_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Normal vs abnormal flashcards with SRS — due cards prioritized."""
    cards = await get_due_flashcards(db, count, system=system, due_only=due_only)
    stats = await get_flashcard_stats(db)
    return {
        "cards": cards,
        "count": len(cards),
        "stats": stats,
        "source": default_source().model_dump(),
    }


@router.post("/api/assessment/flashcards/review")
async def flashcard_review_api(
    req: AssessmentFlashcardReview, db: AsyncSession = Depends(get_db)
):
    """Record spaced-repetition review for an assessment flashcard."""
    result = await record_flashcard_review(db, req.card_id, req.quality)
    if result.get("error"):
        return result
    await update_progress(
        db,
        module_id=MODULE_ID,
        items_completed=1,
        activity_type="flashcard",
    )
    return {**result, "source": default_source().model_dump()}


@router.get("/api/assessment/export/flashcards")
async def export_flashcards_api(system: Optional[str] = Query(None)):
    """Markdown export of the full flashcard deck."""
    content = build_flashcards_markdown(system)
    cards = get_module_summary()
    return {
        "format": "markdown",
        "content": content,
        "count": cards.get("flashcards", 0),
    }


@router.get("/api/assessment/export/head-to-toe", response_class=HTMLResponse)
async def export_head_to_toe_sheet():
    """Printable head-to-toe sequence sheet — use browser Print → Save as PDF."""
    return HTMLResponse(build_head_to_toe_sheet_html())


@router.get("/api/assessment/export/red-flags", response_class=HTMLResponse)
async def export_red_flags_sheet():
    """Printable red-flag quick reference cards — use browser Print → Save as PDF."""
    return HTMLResponse(build_red_flags_sheet_html())


@router.get("/api/assessment/export/checklist", response_class=HTMLResponse)
async def export_checklists_pack():
    """Printable assessment checklists pack — use browser Print → Save as PDF."""
    return HTMLResponse(build_checklists_pack_html())


@router.get("/api/assessment/scenarios/assess-next")
async def assess_next_api(count: int = Query(4, le=8)):
    """What would you assess next? scenario-based clinical judgment exercises."""
    scenarios = get_assess_next_scenarios(count)
    public = [
        {
            "id": s["id"],
            "title": s["title"],
            "setup": s["setup"],
            "findings_so_far": s.get("findings_so_far", []),
            "question": s["question"],
            "options": s["options"],
        }
        for s in scenarios
    ]
    return {"scenarios": public, "count": len(public), "source": default_source().model_dump()}


@router.post("/api/assessment/scenarios/check")
async def check_scenario(req: AssessmentScenarioCheck, db: AsyncSession = Depends(get_db)):
    """Check assess-next scenario answer with clinical reasoning feedback."""
    result = check_assess_next_answer(
        req.scenario_id, req.selected_index, req.selected_option
    )
    if result.get("correct"):
        await update_progress(
            db,
            module_id=MODULE_ID,
            items_completed=1,
            activity_type="scenarios",
            score=100.0,
        )
    return {**result, "source": default_source().model_dump()}


# ── File uploads ─────────────────────────────────────────────────────────────

@router.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form("syllabus"),
    db: AsyncSession = Depends(get_db),
):
    """Upload syllabus or evaluation sheet (basic file handling)."""
    allowed = {".pdf", ".docx", ".doc", ".txt", ".xlsx", ".csv"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        return {"error": f"File type {ext} not supported. Allowed: {', '.join(allowed)}"}

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = settings.uploads_dir / safe_name

    content = await file.read()
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)

    record = UploadedFile(
        filename=safe_name,
        original_name=file.filename or "unknown",
        file_type=file_type,
        size_bytes=len(content),
    )
    db.add(record)
    await db.flush()

    return {
        "id": record.id,
        "filename": file.filename,
        "stored_as": safe_name,
        "size_bytes": len(content),
        "file_type": file_type,
        "message": "File uploaded successfully. Parsing will be available in a future update.",
    }


@router.get("/api/uploads")
async def list_uploads(db: AsyncSession = Depends(get_db)):
    """List uploaded files."""
    result = await db.execute(
        select(UploadedFile).order_by(UploadedFile.uploaded_at.desc())
    )
    files = result.scalars().all()
    return {
        "files": [
            {
                "id": f.id,
                "original_name": f.original_name,
                "file_type": f.file_type,
                "size_bytes": f.size_bytes,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
            }
            for f in files
        ]
    }

