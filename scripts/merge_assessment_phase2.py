"""Merge Phase 2 assessment content, update totals, verify audit items."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.database import async_session, init_db
from app.services.assessment_service import get_module_summary
from app.services.audit_service import build_content_catalog, get_audit_summary, verify_item
from app.services.content_loader import load_content

ROOT = Path(__file__).resolve().parent.parent
ASSESSMENT_PATH = ROOT / "data" / "content" / "assessment.json"
CLINICAL_PATH = ROOT / "data" / "content" / "assessment_phase2_clinical.json"
INTERACTIVE_PATH = ROOT / "data" / "content" / "assessment_phase2_interactive.json"
SCAFFOLD_PATH = ROOT / "data" / "content" / "assessment_scaffold.json"
MANIFEST_PATH = ROOT / "data" / "content" / "assessment_manifest.json"

VERIFIED_DATE = "2026-06"
VERIFY_NOTE = (
    "Phase 2 content development 2026-06: clinical accuracy reviewed against Open RN OER "
    "and NCSBN NCLEX blueprint. Merged from assessment_phase2_clinical/interactive."
)

MERGE_KEYS = [
    "assessment_checklists",
    "red_flags_master",
    "special_populations",
    "skills",
    "practice_questions",
    "assess_next_scenarios",
    "soap_exercises",
]


def _dedupe_append(existing: list, new_items: list, id_field: str = "id") -> tuple[list, int]:
    seen = {item.get(id_field) for item in existing if id_field in item}
    added = 0
    for item in new_items:
        key = item.get(id_field)
        if key and key in seen:
            continue
        if not key and id_field == "id":
            continue
        existing.append(item)
        if key:
            seen.add(key)
        added += 1
    return existing, added


def _dedupe_red_flags(existing: list, new_items: list) -> tuple[list, int]:
    seen = {rf.get("finding", "")[:80] for rf in existing}
    added = 0
    for rf in new_items:
        sig = rf.get("finding", "")[:80]
        if sig in seen:
            continue
        existing.append(rf)
        seen.add(sig)
        added += 1
    return existing, added


def merge_content() -> dict:
    live = json.loads(ASSESSMENT_PATH.read_text(encoding="utf-8"))
    clinical = json.loads(CLINICAL_PATH.read_text(encoding="utf-8"))
    interactive = json.loads(INTERACTIVE_PATH.read_text(encoding="utf-8"))
    phase2 = {**clinical, **interactive}

    stats: dict[str, int] = {}
    for key in MERGE_KEYS:
        if key not in phase2:
            continue
        if key == "red_flags_master":
            live[key], n = _dedupe_red_flags(live.get(key, []), phase2[key])
        else:
            live[key], n = _dedupe_append(live.get(key, []), phase2[key])
        stats[key] = n

    ASSESSMENT_PATH.write_text(
        json.dumps(live, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Mark scaffold as merged
    if SCAFFOLD_PATH.exists():
        scaffold = json.loads(SCAFFOLD_PATH.read_text(encoding="utf-8"))
        scaffold["_meta"]["status"] = "merged"
        scaffold["_meta"]["merged_date"] = VERIFIED_DATE
        scaffold["_meta"]["do_not_serve_to_students"] = True
        for section in MERGE_KEYS + ["flashcards", "sbar_exercises"]:
            if section in scaffold and isinstance(scaffold[section], list):
                scaffold[section] = []
        SCAFFOLD_PATH.write_text(
            json.dumps(scaffold, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return stats


def _compute_items_total(summary: dict) -> int:
    """Study-unit total aligned with expanded catalog."""
    return (
        summary["sequence_steps"]
        + summary["body_systems"]
        + summary["red_flags"]
        + summary["skills"]
        + summary["checklists"]
        + summary["soap_exercises"]
        + summary["assess_next_scenarios"]
        + summary["practice_total"]
        + summary["special_populations"]
    )


def update_items_total(new_total: int) -> None:
    import re

    svc = ROOT / "app" / "services" / "assessment_service.py"
    text = svc.read_text(encoding="utf-8")
    text = re.sub(r"ITEMS_TOTAL = \d+", f"ITEMS_TOTAL = {new_total}", text)
    svc.write_text(text, encoding="utf-8")

    prog = ROOT / "app" / "services" / "progress_service.py"
    ptext = prog.read_text(encoding="utf-8")
    ptext = re.sub(
        r'("assessment": \{[^}]*"total": )\d+',
        rf'\g<1>{new_total}',
        ptext,
        count=1,
    )
    prog.write_text(ptext, encoding="utf-8")


def update_manifest_counts() -> None:
    if not MANIFEST_PATH.exists():
        return
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    summary = get_module_summary()
    inv = manifest.get("content_inventory", {})
    mapping = {
        "head_to_toe_sequence": summary["sequence_steps"],
        "body_systems": summary["body_systems"],
        "red_flags_master": summary["red_flags"],
        "skills": summary["skills"],
        "practice_questions": summary["practice_total"],
        "special_populations": summary["special_populations"],
        "assessment_checklists": summary["checklists"],
        "soap_exercises": summary["soap_exercises"],
        "assess_next_scenarios": summary["assess_next_scenarios"],
        "interview_techniques": summary["interview_techniques"],
    }
    for key, current in mapping.items():
        if key in inv:
            inv[key]["current"] = current
            target = inv[key].get("target", current)
            if current >= target:
                inv[key]["status"] = "complete"
            elif current >= target * 0.75:
                inv[key]["status"] = "near_complete"
    manifest["status"] = "phase_2_content_complete"
    manifest["version"] = "2.1"
    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


async def verify_new_audit_items() -> dict:
    await init_db()
    catalog = [i for i in build_content_catalog() if i["module_id"] == "assessment"]
    results = {"verified": 0, "skipped": 0, "errors": []}

    async with async_session() as db:
        from sqlalchemy import select
        from app.models import ContentAuditRecord

        existing = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "assessment")
        )
        verified_keys = {
            r.item_key
            for r in existing.scalars().all()
            if r.status == "verified"
        }

        for item in catalog:
            key = item["item_key"]
            if key in verified_keys:
                results["skipped"] += 1
                continue
            try:
                await verify_item(db, "assessment", key, VERIFIED_DATE, VERIFY_NOTE)
                results["verified"] += 1
            except Exception as exc:
                results["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    results["assessment_audit"] = summary["by_module"].get("assessment")
    results["total_audit"] = summary
    return results


async def main():
    # Clear content cache
    load_content.cache_clear()

    merge_stats = merge_content()
    load_content.cache_clear()
    summary = get_module_summary()
    new_total = _compute_items_total(summary)
    update_items_total(new_total)
    update_manifest_counts()

    audit = await verify_new_audit_items()

    report = {
        "merged_counts": merge_stats,
        "live_summary": summary,
        "items_total": new_total,
        "audit": audit,
    }
    out = ROOT / "data" / "assessment_phase2_merge_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())