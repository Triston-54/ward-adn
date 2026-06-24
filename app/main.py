"""The Ward — FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import init_db
from app.routers import assessment, audit, dosage, maternal_child, mental_health, microbiology, pathophysiology, pharmacy, progress, socratic, terminology, verify
from app.services.progress_service import get_dashboard_stats
from app.database import async_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize database. Shutdown: cleanup."""
    await init_db()
    # Seed initial progress records
    async with async_session() as session:
        from app.services.progress_service import ensure_modules, ensure_user
        await ensure_user(session)
        await ensure_modules(session)
        await session.commit()
    yield


app = FastAPI(
    title=settings.app_name,
    description=f"{settings.tagline} — {settings.institution}",
    version=settings.app_version,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")

templates = Jinja2Templates(directory=str(settings.templates_dir))


# Include routers
app.include_router(progress.router)
app.include_router(terminology.router)
app.include_router(microbiology.router)
app.include_router(dosage.router)
app.include_router(assessment.router)
app.include_router(mental_health.router)
app.include_router(pathophysiology.router)
app.include_router(maternal_child.router)
app.include_router(socratic.router)
app.include_router(verify.router)
app.include_router(audit.router)
app.include_router(pharmacy.router)


@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    """Serve service worker at site root for full PWA scope (not limited to /static/)."""
    return FileResponse(
        settings.static_dir / "sw.js",
        media_type="application/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard — overview of all study modules."""
    async with async_session() as session:
        stats = await get_dashboard_stats(session)
        await session.commit()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"stats": stats, "settings": settings, "active_track": "nursing"},
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "ai_provider": settings.ai_provider,
    }