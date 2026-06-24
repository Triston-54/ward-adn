"""Sub-Agent 3: Microbiology Chain of Infection & foundational concepts audit."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select

from app.database import async_session, init_db
from app.models import ContentAuditRecord
from app.services.audit_service import build_content_catalog, flag_item, get_audit_summary, verify_item
from app.services.content_loader import load_content

VERIFIED_DATE = "2026-06"

MICRO_FLAGS: dict[str, str] = {
    "chain:agent": (
        "[Chain of Infection] Intervention lists 'vaccination' under the infectious agent link, "
        "but vaccination targets the susceptible host (builds immunity), not the pathogen itself. "
        "This contradicts chain_interventions.agent in the same JSON file (vaccine_host marked incorrect). "
        "Fix intervention: 'Antimicrobial/antiviral therapy, sterilization/disinfection, proper specimen handling' — "
        "remove vaccination."
    ),
    "chain:host": (
        "[Chain of Infection] Intervention includes 'prophylactic antibiotics' as a primary host strategy — "
        "oversimplified and conflicts with antimicrobial stewardship teaching (contributes to CDI/resistance). "
        "Fix: emphasize vaccination, nutrition, rest, protective/neutropenic precautions; note prophylactic "
        "antibiotics only for specific ordered indications (e.g., surgical prophylaxis)."
    ),
    "chain:reservoir": (
        "[Chain of Infection] 'Patient isolation' listed as reservoir intervention — pedagogically imprecise. "
        "Isolation primarily breaks mode of transmission; environmental cleaning/food safety correctly target reservoir. "
        "Fix: clarify isolation reduces exposure from human reservoir but pair with explicit transmission interventions."
    ),
    "concept:transmission-based-precautions": (
        "[Infection control] Varicella (chickenpox) listed under airborne precautions only. Per CDC 2007 isolation "
        "guidelines, varicella/zoster require BOTH airborne isolation (N95, negative-pressure AIIR) AND contact "
        "precautions until lesions crusted. Also note droplet distance: CDC uses ~3 ft; many facilities teach 3–6 ft "
        "— harmonize with influenza pathogen entry (3–6 ft)."
    ),
    "concept:antimicrobial-stewardship": (
        "[Foundational] 'Completing full courses' oversimplifies modern stewardship — duration should be shortest "
        "effective course per culture/sensitivity and guideline (avoid unnecessary prolonged antibiotics). "
        "Fix: 'Use shortest effective course per guideline; patient education on not sharing antibiotics and "
        "not saving leftovers.'"
    ),
}

# Ancillary foundational content reviewed but outside audit catalog (documented in output)
ANCILLARY_VERIFIED = [
    "microbe_classification (5 types: prokaryote bacteria vs eukaryote fungi/parasites, acellular viruses, prions)",
    "gram_stain_procedure (6 steps)",
    "gram_stain_interpretation (Gram+/- cell wall, examples including C. diff as Gram+)",
    "hand_hygiene (WHO 5 moments; soap-and-water for C. diff/norovirus/spores)",
    "ppe_guide",
    "break_points (5 chain break teaching bullets)",
    "chain_interventions interactive (agent/reservoir/exit/transmission/entry/host)",
    "break_chain_scenarios (4 scenarios)",
    "what_if_scenarios (4 scenarios)",
    "hai_types (CLABSI, CAUTI, VAP, SSI, CDI bundles)",
]


async def apply():
    await init_db()
    catalog = [i for i in build_content_catalog() if i["module_id"] == "microbiology"]
    micro = load_content("microbiology.json")

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        result = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "microbiology")
        )
        for rec in result.scalars().all():
            await db.delete(rec)
        await db.flush()

        for item in catalog:
            key = item["item_key"]
            try:
                if key in MICRO_FLAGS:
                    await flag_item(db, "microbiology", key, MICRO_FLAGS[key])
                    stats["flagged"] += 1
                else:
                    note = (
                        f"Microbiology audit 2026-06: '{item['title']}' verified for scientific/clinical accuracy "
                        f"(CDC/Open RN/NCSBN-aligned infection control fundamentals)."
                    )
                    await verify_item(db, "microbiology", key, VERIFIED_DATE, note)
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    pq = len(micro.get("practice_questions", [])) + len(micro.get("application_questions", []))
    result = {
        "agent": "Sub-Agent 3 — Microbiology Chain & Foundations",
        "catalog_items_reviewed": len(catalog),
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "breakdown": {
            "chain_links": 6,
            "concepts": 6,
            "pathogens": 8,
            "practice_questions": pq,
        },
        "ancillary_content_verified": ANCILLARY_VERIFIED,
        "recommended_catalog_additions": [
            "microbe_classification entries (prokaryote vs eukaryote foundational principle)",
            "gram_stain_procedure / gram_stain_interpretation",
            "hand_hygiene and ppe_guide blocks",
            "break_chain_scenarios and what_if_scenarios",
        ],
        "flagged_items": [{"item_key": k, "review_note": v} for k, v in MICRO_FLAGS.items()],
        "errors": stats["errors"],
        "module_summary": summary["by_module"].get("microbiology"),
    }

    out = Path(__file__).resolve().parent.parent / "data" / "microbiology_foundations_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())