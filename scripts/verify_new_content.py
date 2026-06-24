"""Verify newly added curriculum content in the audit catalog."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.database import async_session, init_db
from app.services.audit_service import build_content_catalog, get_audit_summary, verify_item

VERIFIED_DATE = "2026-06"

NEW_CONTENT: dict[tuple[str, str], str] = {
    # Terminology — infection-control integration
    ("terminology", "term:colonization"): (
        "Added 2026-06: Colonization vs infection distinction with MRSA precaution context — CDC MDRO aligned."
    ),
    ("terminology", "term:bacteremia"): (
        "Added 2026-06: Bloodstream bacteria definition linked to sepsis screening and CLABSI prevention."
    ),
    ("terminology", "term:mdro"): (
        "Added 2026-06: MDRO overview with MRSA/VRE/ESBL examples — ties to Microbiology pathogen module."
    ),
    # Microbiology — concepts
    ("microbiology", "concept:nursing-vital-sign-thresholds-cross-module"): (
        "Added 2026-06: Cross-module vital sign triggers (hypotension, oliguria dual-definition, fever, SpO₂) — "
        "integrates Terminology, Assessment, and sepsis teaching."
    ),
    ("microbiology", "concept:hand-hygiene-exceptions-spores-non-enveloped-viruses"): (
        "Added 2026-06: Soap-and-water requirements for C. diff, norovirus, spores — NCLEX high-yield hand hygiene gap."
    ),
    # Microbiology — practice
    ("microbiology", "practice:micro-q9"): (
        "Added 2026-06: Norovirus hand hygiene MCQ — soap-and-water required, alcohol gel insufficient."
    ),
    ("microbiology", "practice:app-q6"): (
        "Added 2026-06: Post-op sepsis recognition scenario — early escalation, cultures, lactate per protocol."
    ),
    # Microbiology — scenarios
    ("microbiology", "scenario:bc-5"): (
        "Added 2026-06: Norovirus unit outbreak Break-the-Chain — contact precautions + soap-and-water."
    ),
    ("microbiology", "scenario:wi-5"): (
        "Added 2026-06: Purulent surgical wound What-If — drainage containment, SSI/sepsis monitoring."
    ),
    # Dosage — safety
    ("dosage", "trap:geriatric_blanket"): (
        "Added 2026-06: Error trap — blanket geriatric % on narrow-index drugs (insulin, warfarin, digoxin)."
    ),
    ("dosage", "practice:d013"): (
        "Added 2026-06: Clinical judgment practice — insulin is NOT subject to geriatric percentage reduction."
    ),
}

# Existing scenarios now cataloged for audit tracking
PRIOR_SCENARIOS: dict[tuple[str, str], str] = {
    ("microbiology", f"scenario:{sid}"): (
        "Catalog addition 2026-06: Scenario clinically verified in Sub-Agent 4 audit — now tracked in audit catalog."
    )
    for sid in ("bc-1", "bc-2", "bc-3", "bc-4", "wi-1", "wi-2", "wi-3", "wi-4")
}

ALL_VERIFY = {**PRIOR_SCENARIOS, **NEW_CONTENT}


async def apply():
    await init_db()
    catalog_keys = {(i["module_id"], i["item_key"]) for i in build_content_catalog()}
    results = {"verified": [], "skipped": [], "errors": []}

    async with async_session() as db:
        for key, note in ALL_VERIFY.items():
            if key not in catalog_keys:
                results["skipped"].append({"key": f"{key[0]}/{key[1]}", "reason": "not in catalog"})
                continue
            try:
                await verify_item(db, key[0], key[1], VERIFIED_DATE, note)
                results["verified"].append(f"{key[0]}/{key[1]}")
            except Exception as exc:
                results["errors"].append(f"{key[0]}/{key[1]}: {exc}")
        await db.commit()
        summary = await get_audit_summary(db)

    results["catalog_total"] = len(catalog_keys)
    results["summary"] = summary
    out = Path(__file__).resolve().parent.parent / "data" / "new_content_verified.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())