"""Progress tracking, streak logic, and sync for local SQLite storage."""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ModuleCompletion, ModuleProgress, StudySession, UserProgress

MODULES = {
    "terminology": {
        "name": "Medical Terminology",
        "total": 220,
        "url": "/modules/terminology",
        "icon": "terminology",
    },
    "microbiology": {
        "name": "Microbiology",
        "total": 47,
        "url": "/modules/microbiology",
        "icon": "microbiology",
    },
    "dosage": {
        "name": "NURS 145 — Drug & Dosage",
        "total": 53,
        "url": "/modules/dosage",
        "icon": "dosage",
    },
    "assessment": {
        "name": "NURS 146 — Health Assessment",
        "total": 132,
        "url": "/modules/assessment",
        "icon": "assessment",
    },
    "mental_health": {
        "name": "NURS 147 — Mental Health",
        "total": 55,
        "url": "/modules/mental-health",
        "icon": "mental_health",
    },
    "pathophysiology": {
        "name": "Pathophysiology",
        "total": 76,
        "url": "/modules/pathophysiology",
        "icon": "pathophysiology",
    },
    "maternal_child": {
        "name": "NURS 148 — Maternal-Child",
        "total": 115,
        "url": "/modules/maternal-child",
        "icon": "maternal_child",
    },
    "pharmacy_calculations": {
        "name": "Pharmacy Calculations & Advanced Problem Solving",
        "total": 48,
        "url": "/pharmacy/modules/calculations",
        "icon": "pharmacy_calculations",
        "track": "pharmacy",
    },
}

NURSING_MODULE_IDS = {mid for mid, info in MODULES.items() if info.get("track") != "pharmacy"}
PHARMACY_MODULE_IDS = {mid for mid, info in MODULES.items() if info.get("track") == "pharmacy"}

MILESTONE_THRESHOLDS = [10, 25, 50, 75, 100]


async def _migrate_legacy_progress(session: AsyncSession) -> None:
    """Copy legacy module_progress rows into module_completions if needed."""
    result = await session.execute(select(ModuleCompletion))
    if result.scalars().first():
        return

    legacy = await session.execute(select(ModuleProgress))
    for row in legacy.scalars().all():
        session.add(
            ModuleCompletion(
                module_id=row.module_id,
                module_name=row.module_name,
                percentage=row.percentage,
                items_completed=row.items_completed,
                items_total=row.items_total,
                last_practiced=row.last_practiced,
                streak_days=row.streak_days,
                last_streak_date=row.last_streak_date,
                notes=row.notes,
            )
        )
    await session.flush()


async def ensure_user(session: AsyncSession) -> UserProgress:
    """Ensure a single local user progress record exists."""
    result = await session.execute(select(UserProgress).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        user = UserProgress(
            display_name="ADN Student",
            program="New River CTC — ADN",
        )
        session.add(user)
        await session.flush()
    return user


async def ensure_modules(session: AsyncSession) -> list[ModuleCompletion]:
    """Ensure all module completion records exist."""
    await _migrate_legacy_progress(session)
    result = await session.execute(select(ModuleCompletion))
    existing = {m.module_id: m for m in result.scalars().all()}

    for mod_id, info in MODULES.items():
        if mod_id not in existing:
            completion = ModuleCompletion(
                module_id=mod_id,
                module_name=info["name"],
                items_total=info["total"],
            )
            session.add(completion)
            existing[mod_id] = completion
        elif existing[mod_id].items_total != info["total"]:
            # Keep catalog totals in sync (e.g. legacy migrations used 50 for terminology)
            existing[mod_id].items_total = info["total"]
            if existing[mod_id].items_completed:
                existing[mod_id].percentage = round(
                    (existing[mod_id].items_completed / info["total"]) * 100, 1
                )

    await session.flush()
    return list(existing.values())


def _compute_next_milestone(
    overall_pct: float, modules: list[ModuleCompletion]
) -> tuple[str, float]:
    """Derive the next meaningful study milestone."""
    for threshold in MILESTONE_THRESHOLDS:
        if overall_pct < threshold:
            return f"Reach {threshold}% overall progress", float(threshold)

    # Find the least-complete active module
    active = list(modules)
    if active:
        least = min(active, key=lambda m: m.percentage)
        if least.percentage < 100:
            remaining = least.items_total - least.items_completed
            return (
                f"Complete {remaining} more in {least.module_name}",
                min(least.percentage + 10, 100),
            )

    return "Maintain your study streak", 100.0


def _apply_streak(module: ModuleCompletion) -> None:
    """Update streak counters for a module after study activity."""
    today = date.today()
    if module.last_streak_date:
        if module.last_streak_date == today:
            return
        if module.last_streak_date == today - timedelta(days=1):
            module.streak_days += 1
        else:
            module.streak_days = 1
    else:
        module.streak_days = 1
    module.last_streak_date = today


async def get_all_progress(session: AsyncSession) -> list[ModuleCompletion]:
    """Return completion records for all modules."""
    await ensure_modules(session)
    result = await session.execute(
        select(ModuleCompletion).order_by(ModuleCompletion.module_id)
    )
    return list(result.scalars().all())


async def update_progress(
    session: AsyncSession,
    module_id: str,
    items_completed: int | None = None,
    items_total: int | None = None,
    activity_type: str = "practice",
    score: float | None = None,
    duration_seconds: int = 0,
) -> ModuleCompletion:
    """Update module completion and log a study session."""
    await ensure_modules(session)
    result = await session.execute(
        select(ModuleCompletion).where(ModuleCompletion.module_id == module_id)
    )
    module = result.scalar_one()

    if items_completed is not None:
        module.items_completed = min(
            module.items_completed + items_completed,
            module.items_total,
        )
        module.percentage = round(
            (module.items_completed / module.items_total) * 100, 1
        ) if module.items_total else 0

    if items_total is not None:
        module.items_total = items_total

    _apply_streak(module)
    module.last_practiced = datetime.now(timezone.utc)

    session.add(
        StudySession(
            module_id=module_id,
            activity_type=activity_type,
            score=score,
            items_count=items_completed or 1,
            duration_seconds=duration_seconds,
        )
    )
    await session.flush()
    return module


async def sync_progress(session: AsyncSession) -> dict:
    """
    Sync aggregate UserProgress from module completions and persist to SQLite.
    Called by the dashboard 'Sync Progress' button.
    """
    user = await ensure_user(session)
    modules = await get_all_progress(session)

    total_pct = sum(m.percentage for m in modules) / len(modules) if modules else 0
    max_streak = max((m.streak_days for m in modules), default=0)
    total_completed = sum(m.items_completed for m in modules)
    total_items = sum(m.items_total for m in modules)

    # Sum study session durations for total minutes
    sessions = await session.execute(select(StudySession))
    total_seconds = sum(s.duration_seconds for s in sessions.scalars().all())

    milestone_label, milestone_target = _compute_next_milestone(total_pct, modules)

    user.overall_percentage = round(total_pct, 1)
    user.current_streak = max_streak
    user.longest_streak = max(user.longest_streak, max_streak)
    user.total_study_minutes = total_seconds // 60
    user.next_milestone_label = milestone_label
    user.next_milestone_target = milestone_target
    user.last_synced_at = datetime.now(timezone.utc)

    await session.flush()

    return {
        "status": "synced",
        "message": "Progress saved to local database.",
        "user": user,
        "modules": modules,
        "synced_at": user.last_synced_at,
    }


async def get_dashboard_stats(session: AsyncSession) -> dict:
    """Aggregate stats for the dashboard."""
    user = await ensure_user(session)
    modules = await get_all_progress(session)

    total_pct = sum(m.percentage for m in modules) / len(modules) if modules else 0
    max_streak = max((m.streak_days for m in modules), default=0)
    total_completed = sum(m.items_completed for m in modules)
    total_items = sum(m.items_total for m in modules)

    recent = max(
        (m for m in modules if m.last_practiced),
        key=lambda m: m.last_practiced,
        default=None,
    )

    milestone_label, milestone_target = _compute_next_milestone(total_pct, modules)

    # Keep user record fresh without requiring manual sync
    if user.overall_percentage != round(total_pct, 1):
        user.overall_percentage = round(total_pct, 1)
        user.current_streak = max_streak
        user.next_milestone_label = milestone_label
        user.next_milestone_target = milestone_target

    return {
        "user": user,
        "overall_percentage": round(total_pct, 1),
        "max_streak": max_streak,
        "total_completed": total_completed,
        "total_items": total_items,
        "next_milestone_label": milestone_label,
        "next_milestone_target": milestone_target,
        "milestone_progress": min(
            round((total_pct / milestone_target) * 100, 1) if milestone_target else 0,
            100,
        ),
        "current_focus": recent.module_name if recent else "Medical Terminology",
        "current_focus_id": recent.module_id if recent else "terminology",
        "modules": modules,
        "module_catalog": MODULES,
    }