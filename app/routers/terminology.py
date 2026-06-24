"""Medical Terminology module — word builder, flashcards, practice, export."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import (
    CustomTerm,
    CustomTermCreate,
    CustomTermFavoriteUpdate,
    CustomTermOut,
    ModuleProgressReport,
    SourceRef,
    WordBuildRequest,
    WordBuildResult,
)
from app.services.content_loader import load_content
from app.services.progress_service import MODULES, get_all_progress, get_dashboard_stats, update_progress
from app.services.terminology_service import (
    MODULE_ID,
    _default_source,
    build_clipboard_text,
    build_study_sheet_html,
    generate_mixed_practice,
    generate_mc_questions,
    generate_type_questions,
    get_all_terms,
    get_components,
    get_due_flashcards,
    get_flashcard_stats,
    record_flashcard_review,
    search_terms,
)

router = APIRouter(tags=["terminology"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


class FlashcardReviewRequest(BaseModel):
    card_key: str
    quality: int  # 0=again, 1=hard, 2=good, 3=easy


async def _module_context(db: AsyncSession) -> dict:
    stats = await get_dashboard_stats(db)
    modules = await get_all_progress(db)
    mod = next((m for m in modules if m.module_id == MODULE_ID), None)
    fc_stats = await get_flashcard_stats(db)
    data = load_content("terminology.json")
    return {
        "stats": stats,
        "module_progress": mod,
        "flashcard_stats": fc_stats,
        "prefixes": data.get("prefixes", []),
        "roots": data.get("roots", []),
        "suffixes": data.get("suffixes", []),
        "term_count": len(get_all_terms()),
    }


@router.get("/terminology")
async def terminology_redirect():
    """Legacy route → new module path."""
    return RedirectResponse(url="/modules/terminology", status_code=301)


@router.get("/modules/terminology", response_class=HTMLResponse)
async def terminology_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Render the Medical Terminology module."""
    ctx = await _module_context(db)
    return templates.TemplateResponse(request, "modules/terminology.html", ctx)


@router.get("/api/terminology/stats")
async def terminology_stats(db: AsyncSession = Depends(get_db)):
    """Module-specific progress and SRS stats."""
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
        "flashcards": fc,
        "term_count": len(get_all_terms()),
    }


@router.post("/api/terminology/progress")
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


@router.get("/api/terminology/components")
async def get_components_api():
    return {**get_components(), "source": _default_source().model_dump()}


@router.post("/api/terminology/build", response_model=WordBuildResult)
async def build_word(req: WordBuildRequest):
    def _normalize(part: str) -> str:
        return part.strip().lower().strip("-")

    def _combine_root_suffix(root: str, suffix: str) -> str:
        if root and suffix and root[-1] in "aeiou" and suffix[0] in "aeiou":
            root = root[:-1]
        return root + suffix

    prefix = _normalize(req.prefix or "")
    root = _normalize(req.root)
    suffix = _normalize(req.suffix or "")

    components_data = get_components()
    prefixes = {_normalize(p["element"]): p for p in components_data["prefixes"]}
    roots = {_normalize(r["element"]): r for r in components_data["roots"]}
    suffixes = {_normalize(s["element"]): s for s in components_data["suffixes"]}

    components = []
    meanings = []

    if prefix and prefix in prefixes:
        p = prefixes[prefix]
        components.append({"type": "prefix", "element": p["element"], "meaning": p["meaning"]})
        meanings.append(p["meaning"])
    elif prefix:
        components.append({"type": "prefix", "element": prefix, "meaning": "(unknown prefix)"})

    if root in roots:
        r = roots[root]
        components.append({"type": "root", "element": r["element"], "meaning": r["meaning"]})
        meanings.append(r["meaning"])
    else:
        components.append({"type": "root", "element": root, "meaning": "(check root spelling)"})

    if suffix and suffix in suffixes:
        s = suffixes[suffix]
        components.append({"type": "suffix", "element": s["element"], "meaning": s["meaning"]})
        meanings.append(s["meaning"])
    elif suffix:
        components.append({"type": "suffix", "element": suffix, "meaning": "(unknown suffix)"})

    built = f"{prefix}{_combine_root_suffix(root, suffix)}"
    known = {t["term"].lower(): t for t in get_all_terms()}
    clinical_note = (
        "Breaking terms into parts helps you decode unfamiliar words on exams "
        "and in clinical documentation — a core ADN competency."
    )
    likely_meaning = " + ".join(meanings) if meanings else "Unable to derive meaning"

    if built.lower() in known:
        t = known[built.lower()]
        likely_meaning = t["definition"]
        clinical_note = t.get("clinical_relevance", clinical_note)

    return WordBuildResult(
        built_term=built,
        components=components,
        likely_meaning=likely_meaning,
        clinical_note=clinical_note,
        source=_default_source(),
    )


@router.get("/api/terminology/terms")
async def search_terms_api(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, le=250),
    db: AsyncSession = Depends(get_db),
):
    terms, total = search_terms(q, category, limit)

    result = await db.execute(select(CustomTerm).order_by(CustomTerm.term))
    for c in result.scalars().all():
        entry = {
            "term": c.term,
            "definition": c.definition,
            "prefix": c.prefix,
            "root": c.root,
            "suffix": c.suffix,
            "clinical_relevance": c.clinical_note,
            "category": "custom",
            "source": {"title": "User-added", "citation": "Personal notes"},
        }
        if not q or q.lower() in c.term.lower() or q.lower() in c.definition.lower():
            if len(terms) < limit:
                terms.append(entry)
                total += 1

    return {"terms": terms, "total": total, "source": _default_source().model_dump()}


@router.get("/api/terminology/term/{term_name}")
async def get_term_detail(term_name: str):
    known = {t["term"].lower(): t for t in get_all_terms()}
    term = known.get(term_name.lower())
    if not term:
        return {"error": "Term not found", "term": term_name}
    return {"term": term, "source": term.get("source", _default_source().model_dump())}


@router.get("/api/terminology/practice")
async def get_practice(
    count: int = Query(10, le=30),
    mode: str = Query("mixed", description="mixed | mc | type"),
    db: AsyncSession = Depends(get_db),
):
    """Practice: multiple choice, type-the-term, or mixed."""
    if mode == "mc":
        raw = generate_mc_questions(count)
    elif mode == "type":
        raw = generate_type_questions(count)
    else:
        mc_n = count // 2
        raw = generate_mixed_practice(mc_n, count - mc_n)

    output = []
    for q in raw:
        if q["type"] == "multiple_choice":
            output.append({
                **q,
                "source": SourceRef(**q["source"]) if isinstance(q.get("source"), dict) else _default_source(),
            })
        else:
            output.append(q)

    # Serialize pydantic sources for MC
    serialized = []
    for q in output:
        item = dict(q)
        if "source" in item and hasattr(item["source"], "model_dump"):
            item["source"] = item["source"].model_dump()
        serialized.append(item)

    return {"questions": serialized, "count": len(serialized), "mode": mode}


@router.get("/api/terminology/flashcards")
async def get_flashcards(
    count: int = Query(20, le=50),
    due_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Flashcards with SRS — due cards prioritized."""
    cards = await get_due_flashcards(db, count)
    if due_only:
        cards = [c for c in cards if c["due"]]
    stats = await get_flashcard_stats(db)
    return {"cards": cards[:count], "count": len(cards[:count]), "stats": stats}


@router.post("/api/terminology/flashcards/review")
async def review_flashcard(req: FlashcardReviewRequest, db: AsyncSession = Depends(get_db)):
    """Record SRS review result."""
    result = await record_flashcard_review(db, req.card_key, req.quality)
    await update_progress(db, MODULE_ID, items_completed=1, activity_type="flashcard")
    return result


@router.get("/api/terminology/custom", response_model=list[CustomTermOut])
async def list_custom_terms(db: AsyncSession = Depends(get_db)):
    """List user-added custom terminology entries."""
    result = await db.execute(
        select(CustomTerm).order_by(CustomTerm.is_favorite.desc(), CustomTerm.term)
    )
    return list(result.scalars().all())


@router.post("/api/terminology/custom", response_model=CustomTermOut)
async def add_custom_term(req: CustomTermCreate, db: AsyncSession = Depends(get_db)):
    """Save a user-defined term to SQLite."""
    entry = CustomTerm(
        term=req.term.strip(),
        definition=req.definition.strip(),
        prefix=req.prefix.strip() if req.prefix else None,
        root=req.root.strip() if req.root else None,
        suffix=req.suffix.strip() if req.suffix else None,
        clinical_note=req.clinical_note.strip() if req.clinical_note else None,
    )
    db.add(entry)
    await db.flush()
    return entry


@router.patch("/api/terminology/custom/{term_id}", response_model=CustomTermOut)
async def update_custom_term(
    term_id: int,
    data: CustomTermFavoriteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Toggle favorite status on a custom term."""
    result = await db.execute(select(CustomTerm).where(CustomTerm.id == term_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Custom term not found")
    entry.is_favorite = data.is_favorite
    await db.flush()
    return entry


@router.get("/api/terminology/export/clipboard")
async def export_clipboard(count: int = Query(50, le=300)):
    terms, _ = search_terms(limit=count)
    return {"format": "text", "content": build_clipboard_text(terms), "count": len(terms)}


@router.get("/api/terminology/export/study-sheet", response_class=HTMLResponse)
async def export_study_sheet(
    count: int = Query(50, le=300),
    category: Optional[str] = Query(None),
):
    """Printable HTML study sheet — use browser Print → Save as PDF."""
    terms, _ = search_terms(category=category, limit=count)
    title = f"Study Sheet ({len(terms)} terms)"
    if category:
        title = f"{category.title()} — {title}"
    return HTMLResponse(build_study_sheet_html(terms, title))


@router.get("/api/terminology/export/flashcards")
async def export_flashcards_text(count: int = Query(50, le=300)):
    terms, _ = search_terms(limit=count)
    lines = ["# The Ward — Medical Terminology Flashcards\n"]
    for i, t in enumerate(terms, 1):
        lines += [
            f"## Card {i}",
            f"**Front:** {t['term']}",
            f"**Back:** {t['definition']}",
        ]
        if t.get("breakdown"):
            lines.append(f"**Breakdown:** {t['breakdown']}")
        if t.get("clinical_relevance"):
            lines.append(f"**Clinical:** {t['clinical_relevance']}")
        lines.append("")
    return {"format": "markdown", "content": "\n".join(lines), "count": len(terms)}


@router.get("/api/terminology/export/json")
async def export_terms_json():
    """Export all verified terms as JSON for offline study or import."""
    from app.services.terminology_service import get_all_terms

    terms = get_all_terms()
    return {
        "format": "json",
        "module": "terminology",
        "total": len(terms),
        "source": "Ehrlich & Schroeder, 8th Ed.",
        "terms": terms,
    }