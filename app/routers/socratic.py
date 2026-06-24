"""Global Socratic tutor API — works from any study module."""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SocraticRequest, SocraticResponse
from app.config import settings
from app.services.ai_service import check_ollama_health, socratic_tutor
from app.services.progress_service import MODULES, update_progress
from app.services.socratic_registry import detect_module_from_path, get_client_config

router = APIRouter(tags=["socratic"])


@router.get("/api/socratic/config")
async def socratic_config(module_id: str | None = None):
    """Front-end registry — tracks, topics, and module defaults for WardSocratic."""
    return get_client_config(module_id)


@router.post("/api/socratic", response_model=SocraticResponse)
@router.post("/api/socratic/chat", response_model=SocraticResponse)
async def ask_socratic(request: SocraticRequest):
    """Context-aware Socratic tutor — guiding questions first, module-aware."""
    return await socratic_tutor(request)


@router.get("/api/socratic/health")
async def socratic_health():
    """Socratic AI layer status — Ollama probe when enabled."""
    health = await check_ollama_health()
    return {
        "ai_enabled": settings.ai_enabled,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ollama": health,
    }


@router.get("/api/socratic/detect-module")
async def socratic_detect_module(path: str = "/"):
    """Resolve module_id from a page path (for client-side verification)."""
    module_id = detect_module_from_path(path)
    return {"path": path, "module_id": module_id}


class SocraticProgressReport(BaseModel):
    module_id: str
    topic_category: Optional[str] = None


@router.post("/api/socratic/progress")
async def socratic_progress(
    data: SocraticProgressReport, db: AsyncSession = Depends(get_db)
):
    """Log Socratic study activity to the current module's progress."""
    module_id = data.module_id if data.module_id in MODULES else "general"
    if module_id == "general":
        module_id = "terminology"
    mod = await update_progress(
        db,
        module_id=module_id,
        items_completed=1,
        activity_type="socratic",
    )
    return {
        "module_id": mod.module_id,
        "percentage": mod.percentage,
        "items_completed": mod.items_completed,
    }