"""Fast startup smoke test — DB, core services, routers, and module content (no live HTTP server)."""
from __future__ import annotations

import asyncio
import logging
import sys

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from app.database import async_session, init_db
from app.models import DosageCalculationRequest, WordBuildRequest
from app.routers.terminology import build_word
from app.services.assessment_export import (
    build_checklists_pack_html,
    build_head_to_toe_sheet_html,
    build_red_flags_sheet_html,
)
from app.services.assessment_manifest import get_manifest
from app.services.assessment_service import get_module_summary
from app.services.dosage_service import calculate_dosage
from app.services.content_loader import safe_sample
from app.services.maternal_child_manifest import get_build_status as mc_build_status, get_manifest as get_mc_manifest
from app.services.maternal_child_service import (
    ITEMS_TOTAL as MC_ITEMS_TOTAL,
    get_complications_drill_pool,
    get_complications_drill_questions,
    get_module_summary as mc_summary,
    get_safety_red_flags,
)
from app.services.mental_health_manifest import get_build_status as mh_build_status
from app.services.mental_health_service import (
    ITEMS_TOTAL as MH_ITEMS_TOTAL,
    get_module_summary as mh_summary,
    get_safety_drill_pool,
    get_therapeutic_communication,
)
from app.services.microbiology_service import (
    ITEMS_TOTAL as MICRO_ITEMS_TOTAL,
    get_infection_chain,
    get_module_summary as micro_summary,
    get_pathogens,
)
from app.services.audit_service import build_content_catalog, get_catalog_stats
from app.services.pathophysiology_manifest import get_build_status as patho_build_status, get_manifest as get_patho_manifest
from app.services.pathophysiology_service import (
    ITEMS_TOTAL as PATHO_ITEMS_TOTAL,
    get_module_summary as get_patho_summary,
)
from app.services.pharmacy_calculations_service import (
    ITEMS_TOTAL as PHARM_CALC_ITEMS_TOTAL,
    get_module_content as get_pharm_calc_content,
    get_module_summary as pharm_calc_summary,
)
from app.services.pharmacy_manifest import get_build_status as pharm_build_status, get_manifest as pharm_manifest
from app.services.pharmacy_progress_service import get_pharmacy_dashboard_stats
from app.services.progress_service import MODULES, get_dashboard_stats
from app.services.socratic_registry import (
    PATH_MODULE_MAP,
    SOCRATIC_MODULES,
    TOPIC_CATEGORIES,
    TRACKS,
    VALID_INTENTS,
    get_client_config,
)
from app.services.terminology_service import get_all_terms


async def check_database() -> dict:
    await init_db()
    async with async_session() as session:
        return await get_dashboard_stats(session)


async def check_terminology() -> None:
    terms = get_all_terms()
    assert len(terms) >= 20, f"Expected >= 20 terms, got {len(terms)}"
    assert len(terms) == MODULES["terminology"]["total"], (
        f"Terminology count {len(terms)} != MODULES total {MODULES['terminology']['total']}"
    )
    print(f"Terms loaded: {len(terms)}")

    result = await build_word(WordBuildRequest(prefix="tachy-", root="cardi", suffix="-ia"))
    assert result.built_term == "tachycardia", result.built_term
    print(f"Word build OK: {result.built_term}")


def check_dosage() -> None:
    result = calculate_dosage(
        DosageCalculationRequest(
            calc_type="liquid",
            ordered_dose=4,
            available_dose=10,
            available_volume=1,
        )
    )
    assert result.answer == 0.4, result.answer
    assert result.unit == "mL", result.unit
    print(f"Dosage calc OK: {result.answer} {result.unit}")


def check_pathophysiology() -> None:
    summary = get_patho_summary()
    assert summary["concepts_count"] == 10
    assert summary["disease_count"] == 12
    assert summary["compare_count"] == 5
    assert summary["scenario_count"] == 6
    assert summary["flashcard_count"] == 25
    assert summary["practice_count"] == 18
    assert summary["items_total"] == PATHO_ITEMS_TOTAL == 76
    assert "pathophysiology" in MODULES
    assert MODULES["pathophysiology"]["total"] == 76

    manifest = get_patho_manifest()
    assert manifest["status"] == "module_complete"
    implemented = [t for t in manifest["tabs"] if t["status"] == "implemented"]
    assert len(implemented) == 6

    build = patho_build_status()
    assert build["tabs_implemented"] == 6

    catalog = [i for i in build_content_catalog() if i["module_id"] == "pathophysiology"]
    assert len(catalog) == 76, f"Expected 76 audit catalog items, got {len(catalog)}"
    assert "pathophysiology" in get_catalog_stats()["by_module"]
    print(f"Pathophysiology OK ({summary['items_total']} items, {len(implemented)} tabs, {len(catalog)} audit)")


def check_assessment_exports() -> None:
    summary = get_module_summary()
    assert summary["sequence_steps"] == 10
    assert summary["red_flags"] == 20
    assert summary["checklists"] == 8
    assert summary["flashcards"] == 60

    assert "Assessment Sequence" in build_head_to_toe_sheet_html()
    assert "rf-card" in build_red_flags_sheet_html()
    assert "check-item" in build_checklists_pack_html()

    manifest = get_manifest()
    export_tab = next(t for t in manifest["tabs"] if t["id"] == "export")
    assert export_tab["status"] == "implemented"
    assert manifest["status"] == "module_complete"
    print(f"Assessment exports OK ({summary['sequence_steps']} steps, {summary['red_flags']} flags)")


def check_routers_import() -> None:
    """All routers referenced in app.main must import without error."""
    from app.routers import (
        assessment,
        audit,
        dosage,
        maternal_child,
        mental_health,
        microbiology,
        pathophysiology,
        pharmacy,
        progress,
        socratic,
        terminology,
        verify,
    )

    for name, mod in [
        ("assessment", assessment),
        ("audit", audit),
        ("dosage", dosage),
        ("maternal_child", maternal_child),
        ("mental_health", mental_health),
        ("microbiology", microbiology),
        ("pathophysiology", pathophysiology),
        ("pharmacy", pharmacy),
        ("progress", progress),
        ("socratic", socratic),
        ("terminology", terminology),
        ("verify", verify),
    ]:
        assert hasattr(mod, "router"), f"{name} missing APIRouter"
    print("All 12 routers import OK")


def check_maternal_child() -> None:
    from app.services.audit_service import MODULE_LABELS, build_content_catalog

    summary = mc_summary()
    assert summary["items_total"] == MC_ITEMS_TOTAL == MODULES["maternal_child"]["total"]
    assert summary["pregnancy_count"] >= 9
    assert summary["postpartum_count"] >= 9
    assert len(get_safety_red_flags()) >= 15
    assert len(get_complications_drill_pool()) >= 13
    assert "maternal_child" in MODULE_LABELS

    catalog = build_content_catalog()
    mc_catalog = [i for i in catalog if i["module_id"] == "maternal_child"]
    assert len(mc_catalog) == summary["items_total"]

    manifest = get_mc_manifest()
    assert manifest.get("tabs"), "Maternal-child manifest missing tabs"
    assert len(get_complications_drill_questions(count=3)) >= 1

    build = mc_build_status()
    assert build["tabs_implemented"] == 8
    print(
        f"Maternal-child OK ({summary['items_total']} items, "
        f"{summary['safety_flag_count']} red flags, {summary['drill_count']} drill scenarios)"
    )


def check_mental_health() -> None:
    summary = mh_summary()
    assert summary["items_total"] == MH_ITEMS_TOTAL == MODULES["mental_health"]["total"]
    assert len(get_therapeutic_communication()) >= 4
    assert len(get_safety_drill_pool()) >= 3
    build = mh_build_status()
    assert build["tabs_total"] >= 2
    print(
        f"Mental health OK ({summary['communication_count']} techniques, "
        f"{summary['safety_drill_count']} drill items)"
    )


def check_microbiology() -> None:
    chain = get_infection_chain()
    pathogens = get_pathogens()
    summary = micro_summary()
    assert len(chain) >= 6, "Expected infection chain links"
    assert len(pathogens) >= 5, "Expected healthcare pathogens"
    assert summary["items_total"] == MICRO_ITEMS_TOTAL == MODULES["microbiology"]["total"]
    print(
        f"Microbiology OK ({summary['chain_links']} links, "
        f"{summary['pathogens']} pathogens, {summary['practice_total']} practice)"
    )


async def check_pharmacy() -> None:
    manifest = pharm_manifest()
    assert manifest.get("stages"), "Pharmacy manifest missing stages"
    content = get_pharm_calc_content()
    assert content.get("module_id") == "pharmacy_calculations"
    summary = pharm_calc_summary()
    assert summary["items_total"] == PHARM_CALC_ITEMS_TOTAL == MODULES["pharmacy_calculations"]["total"]
    build = pharm_build_status()
    assert build["modules_total"] >= 1

    async with async_session() as session:
        stats = await get_pharmacy_dashboard_stats(session)
    assert "overall_percentage" in stats
    assert "module_catalog" in stats
    assert stats["module_catalog"], "Pharmacy module catalog must not be empty"
    print(f"Pharmacy OK ({len(manifest['stages'])} stages, {summary['calc_type_count']} calc types)")


def check_safe_sample() -> None:
    assert safe_sample([], 5) == []
    assert safe_sample([1, 2, 3], 0) == []
    sampled = safe_sample(["a", "b", "c"], 10)
    assert len(sampled) == 3
    assert len(set(sampled)) == 3

    from app.services.microbiology_service import get_break_chain_scenarios

    assert get_break_chain_scenarios(count=0) == []
    print("safe_sample edge cases OK")


def check_socratic_registry() -> None:
    for mid, spec in SOCRATIC_MODULES.items():
        track = spec.get("track", "nursing")
        assert track in TRACKS, f"Unknown track for {mid}: {track}"
        for topic in spec.get("topics", []):
            assert topic in TOPIC_CATEGORIES, f"Invalid topic {topic} in {mid}"
        for intent in VALID_INTENTS:
            assert isinstance(intent, str)

    for path, mid in PATH_MODULE_MAP.items():
        assert mid in SOCRATIC_MODULES, f"PATH_MODULE_MAP {path} → unknown {mid}"

    cfg = get_client_config("mental_health")
    assert cfg["module_label"] == "Mental Health"
    assert "psychosocial" in cfg["topics"]
    assert cfg["intents"] == list(VALID_INTENTS)
    print(f"Socratic registry OK ({len(SOCRATIC_MODULES)} modules, {len(PATH_MODULE_MAP)} path maps)")


def check_fastapi_app() -> None:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    critical_routes = [
        "/health",
        "/",
        "/pharmacy",
        "/pharmacy/modules/calculations",
        "/modules/mental-health",
        "/modules/pathophysiology",
        "/modules/maternal-child",
        "/modules/microbiology",
        "/api/pathophysiology/stats",
        "/api/pathophysiology/manifest",
        "/api/pathophysiology/export/flashcards",
        "/api/pharmacy/stats",
        "/api/pharmacy/manifest",
        "/api/pharmacy/calculations/stats",
        "/api/maternal-child/stats",
        "/api/maternal-child/export/flashcards",
        "/api/mental-health/manifest",
        "/api/socratic/config",
    ]
    for route in critical_routes:
        resp = client.get(route)
        assert resp.status_code < 500, f"{route} returned {resp.status_code}"
    print(f"FastAPI smoke OK ({len(critical_routes)} routes)")


async def main() -> None:
    stats = await check_database()
    print("DB OK")
    print(f"Modules: {len(MODULES)}")
    print(f"Overall: {stats.get('overall_percentage', 0)}%")

    check_routers_import()
    await check_terminology()
    check_dosage()
    check_pathophysiology()
    check_assessment_exports()
    check_maternal_child()
    check_mental_health()
    check_microbiology()
    await check_pharmacy()
    check_safe_sample()
    check_socratic_registry()
    check_fastapi_app()
    print("\nAll startup checks passed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"STARTUP FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc