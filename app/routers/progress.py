"""Progress tracking API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ModuleProgressOut, ProgressUpdate, SyncProgressResponse, UserProgressOut
from app.services.progress_service import (
    get_all_progress,
    get_dashboard_stats,
    sync_progress,
    update_progress,
)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/dashboard")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate dashboard statistics."""
    return await get_dashboard_stats(db)


@router.get("/modules", response_model=list[ModuleProgressOut])
async def list_modules(db: AsyncSession = Depends(get_db)):
    """List completion status for all modules."""
    modules = await get_all_progress(db)
    return modules


@router.post("/update", response_model=ModuleProgressOut)
async def update_module_progress(
    data: ProgressUpdate, db: AsyncSession = Depends(get_db)
):
    """Update progress for a module after study activity."""
    progress = await update_progress(
        db,
        module_id=data.module_id,
        items_completed=data.items_completed,
        items_total=data.items_total,
        activity_type=data.activity_type,
        score=data.score,
        duration_seconds=data.duration_seconds,
    )
    return progress


@router.post("/sync", response_model=SyncProgressResponse)
async def sync_user_progress(db: AsyncSession = Depends(get_db)):
    """Sync and persist aggregate progress to the local SQLite database."""
    result = await sync_progress(db)
    return SyncProgressResponse(
        status=result["status"],
        message=result["message"],
        user=UserProgressOut.model_validate(result["user"]),
        modules=[ModuleProgressOut.model_validate(m) for m in result["modules"]],
        synced_at=result["synced_at"],
    )