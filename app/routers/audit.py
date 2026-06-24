"""Content audit routes — correctness review preparation."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import AuditFlagRequest, AuditItemOut, AuditSummaryOut, AuditVerifyRequest
from app.services.audit_service import (
    AUDIT_STATUSES,
    MODULE_LABELS,
    clear_item_audit,
    flag_item,
    get_audit_items,
    get_audit_summary,
    get_catalog_stats,
    verify_item,
)

router = APIRouter(tags=["audit"])
templates = Jinja2Templates(directory=str(settings.templates_dir))


@router.get("/admin/audit", response_class=HTMLResponse)
async def audit_page_redirect(request: Request):
    """Admin-style alias → content audit view."""
    return templates.TemplateResponse(
        request,
        "audit.html",
        {
            "modules": MODULE_LABELS,
            "statuses": AUDIT_STATUSES,
            "catalog_stats": get_catalog_stats(),
        },
    )


@router.get("/audit", response_class=HTMLResponse)
async def content_audit_page(request: Request):
    """Content Audit view for marking verified items and flagging review needs."""
    return templates.TemplateResponse(
        request,
        "audit.html",
        {
            "modules": MODULE_LABELS,
            "statuses": AUDIT_STATUSES,
            "catalog_stats": get_catalog_stats(),
        },
    )


@router.get("/api/audit/summary", response_model=AuditSummaryOut)
async def audit_summary_api(db: AsyncSession = Depends(get_db)):
    """Aggregate audit counts by status and module."""
    return await get_audit_summary(db)


@router.get("/api/audit/catalog-stats")
async def catalog_stats_api():
    """Static catalog size (no DB)."""
    return get_catalog_stats()


@router.get("/api/audit/items")
async def audit_items_api(
    module_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List auditable items merged with stored audit status."""
    items, total = await get_audit_items(
        db,
        module_id=module_id,
        status=status,
        item_type=item_type,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "statuses": list(AUDIT_STATUSES),
        "modules": MODULE_LABELS,
    }


@router.post("/api/audit/items/{module_id}/{item_key}/verify", response_model=AuditItemOut)
async def verify_item_api(
    module_id: str,
    item_key: str,
    body: AuditVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Mark an item as verified with date and source note."""
    try:
        result = await verify_item(
            db,
            module_id,
            item_key,
            verified_date=body.verified_date,
            source_note=body.source_note,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/audit/items/{module_id}/{item_key}/flag", response_model=AuditItemOut)
async def flag_item_api(
    module_id: str,
    item_key: str,
    body: AuditFlagRequest,
    db: AsyncSession = Depends(get_db),
):
    """Flag an item as needing review."""
    try:
        result = await flag_item(db, module_id, item_key, body.review_note)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/audit/items/{module_id}/{item_key}")
async def clear_item_api(
    module_id: str,
    item_key: str,
    db: AsyncSession = Depends(get_db),
):
    """Reset item to unreviewed (remove audit record)."""
    try:
        result = await clear_item_audit(db, module_id, item_key)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc