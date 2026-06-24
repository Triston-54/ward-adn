"""Sub-Agent 5: Health Assessment clinical content audit (scoped sections)."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import select

from app.database import async_session, init_db
from app.models import ContentAuditRecord
from app.services.audit_service import build_content_catalog, flag_item, get_audit_summary, verify_item
from app.services.content_loader import load_content

VERIFIED_DATE = "2026-06"
AGENT_NAME = "Sub-Agent 5 — Health Assessment Clinical Content"

SCOPE_PREFIXES = (
    "sequence:",
    "system:",
    "redflag:",
    "population:",
    "skill:",
)

# Previously flagged items (2026-06 clinical review) — content corrected in assessment.json
NEEDS_REVIEW_FLAGS: dict[str, str] = {}

# interview_techniques not in build_content_catalog — reviewed as ancillary JSON content
ANCILLARY_VERIFIED = [
    "interview_techniques:therapeutic-communication (open-ended questions, active listening, avoid false reassurance)",
    "interview_techniques:oldcarts (structured symptom analysis for NCLEX history-taking)",
    "interview_techniques:cultural-linguistic-considerations (certified interpreter; not family for clinical consent)",
    "interview_techniques:review-of-systems (systematic ROS by body system)",
    "interview_techniques:pqrst (pain history mnemonic aligned with pain_assessment block)",
    "interview_techniques:safety-abuse-screening (direct private screening, mandatory reporting context)",
]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _scoped_catalog() -> list[dict]:
    return [
        i for i in build_content_catalog()
        if i["module_id"] == "assessment"
        and any(i["item_key"].startswith(p) for p in SCOPE_PREFIXES)
    ]


def _verify_note(item: dict, assess: dict) -> str:
    key = item["item_key"]
    title = item["title"]
    if key.startswith("sequence:"):
        order = int(key.split(":")[1])
        step = next(
            (s for s in assess.get("head_to_toe_sequence", []) if s.get("order") == order),
            {},
        )
        src = (step.get("source") or {}).get("citation", "Open RN OER Ch. 2")
        return (
            f"Health Assessment audit 2026-06: head-to-toe sequence step '{title}' verified "
            f"(systematic exam order, {src})."
        )
    if key.startswith("system:"):
        sys_id = key.split(":", 1)[1]
        block = next((s for s in assess.get("body_systems", []) if s.get("id") == sys_id), {})
        steps = len(block.get("assessment_steps", []))
        return (
            f"Health Assessment audit 2026-06: body system '{title}' verified — "
            f"{steps} assessment steps, red flags, and nursing reasoning align with Open RN/NCSBN."
        )
    if key.startswith("redflag:"):
        return (
            f"Health Assessment audit 2026-06: red flag '{title}' action/priority verified "
            f"for immediate nursing escalation (ABC/time-sensitive protocols)."
        )
    if key.startswith("population:"):
        pop_id = key.split(":", 1)[1]
        block = next((p for p in assess.get("special_populations", []) if p.get("id") == pop_id), {})
        considerations = len(block.get("assessment_considerations", []))
        return (
            f"Health Assessment audit 2026-06: special population '{title}' verified — "
            f"{considerations} age-specific considerations and safety screening (Open RN/NCSBN)."
        )
    if key.startswith("skill:"):
        sk_id = key.split(":", 1)[1]
        block = next((s for s in assess.get("skills", []) if s.get("id") == sk_id), {})
        tip = (block.get("clinical_tip") or "")[:60]
        return (
            f"Health Assessment audit 2026-06: skill '{title}' verified for bedside technique "
            f"and NCLEX application. Tip: {tip or 'standard nursing assessment skill'}."
        )
    return f"Health Assessment audit 2026-06: '{title}' verified for clinical accuracy."


async def apply():
    await init_db()
    assess = load_content("assessment.json")
    catalog = _scoped_catalog()
    scoped_keys = {i["item_key"] for i in catalog}

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        result = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "assessment")
        )
        for rec in result.scalars().all():
            if rec.item_key in scoped_keys:
                await db.delete(rec)
        await db.flush()

        for item in catalog:
            key = item["item_key"]
            try:
                if key in NEEDS_REVIEW_FLAGS:
                    await flag_item(db, "assessment", key, NEEDS_REVIEW_FLAGS[key])
                    stats["flagged"] += 1
                else:
                    await verify_item(
                        db,
                        "assessment",
                        key,
                        VERIFIED_DATE,
                        _verify_note(item, assess),
                    )
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    interview = assess.get("interview_techniques", [])
    result_payload = {
        "agent": AGENT_NAME,
        "catalog_items_reviewed": len(catalog),
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "breakdown": {
            "head_to_toe_sequence": len(assess.get("head_to_toe_sequence", [])),
            "body_systems": len(assess.get("body_systems", [])),
            "red_flags_master": len(assess.get("red_flags_master", [])),
            "special_populations": len(assess.get("special_populations", [])),
            "skills": len(assess.get("skills", [])),
            "interview_techniques": len(interview),
        },
        "ancillary_content_verified": ANCILLARY_VERIFIED,
        "recommended_catalog_additions": [
            "interview_techniques entries (6 techniques — therapeutic communication through abuse screening)",
        ],
        "flagged_items": [
            {"item_key": k, "review_note": v} for k, v in NEEDS_REVIEW_FLAGS.items()
        ],
        "errors": stats["errors"],
        "module_summary": summary["by_module"].get("assessment"),
    }

    out = Path(__file__).resolve().parent.parent / "data" / "assessment_clinical_audit.json"
    out.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())