"""Source verification API — central registry for verified nursing content."""
from fastapi import APIRouter, HTTPException

from app.services.verification_service import get_all_sources, get_module_sources, lookup_source

router = APIRouter(prefix="/api/verify", tags=["verification"])


@router.get("/sources")
async def list_all_sources():
    """Return all verified sources from the central registry."""
    return get_all_sources()


@router.get("/sources/{module_id}")
async def list_module_sources(module_id: str):
    """Return verified sources for a specific study module."""
    data = get_module_sources(module_id)
    if not data["sources"] and module_id not in ("general",):
        # Still return NCLEX/general sources via fallback in service
        data = get_module_sources("general")
        data["module_id"] = module_id
        data["note"] = f"No dedicated sources for '{module_id}'; showing general references."
    return data


@router.get("/source/{source_id}")
async def get_source_by_id(source_id: str):
    """Look up a single verified source by registry key."""
    source = lookup_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return source