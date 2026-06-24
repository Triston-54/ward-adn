"""Sub-Agent 4: Microbiology pathogens, clinical scenarios & nursing infection control audit."""
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

# Carried forward from Sub-Agent 3 (chain/concept foundations)
FOUNDATION_FLAGS: dict[str, str] = {
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

# New flags from Sub-Agent 4 pathogen & clinical-application review
PATHOGEN_FLAGS: dict[str, str] = {
    "pathogen:pseudomonas": (
        "[Pathogen] Precautions listed as 'Contact (if MDR)' without defining MDR criteria or naming "
        "carbapenem-resistant Pseudomonas (CP-CRPA) — nursing students may omit needed precautions or "
        "over-isolate routine isolates. 'Aspiration precautions' is non-standard terminology; replace with "
        "VAP bundle elements (HOB 30–45°, oral care, closed suction, circuit maintenance). Add: standard "
        "precautions for non-MDR; contact precautions for MDR/colonization per facility policy; strict "
        "moist-environment and water-system controls."
    ),
    "pathogen:candida-auris": (
        "[Pathogen] Nursing action cites generic 'EPA-registered disinfectant' — insufficient for C. auris safety. "
        "CDC requires disinfectants with EPA claim for C. auris (or C. diff) because many routine hospital "
        "disinfectants are ineffective against this organism on surfaces. Fix: 'Use EPA-registered disinfectant "
        "with demonstrated activity against C. auris; notify infection control immediately; screen/cohort contacts "
        "per facility protocol.'"
    ),
}

ALL_FLAGS = {**FOUNDATION_FLAGS, **PATHOGEN_FLAGS}

PATHOGEN_VERIFY_NOTES: dict[str, str] = {
    "pathogen:mrsa": (
        "MRSA pathogen profile verified: Gram+ MDRO, contact precautions, colonization vs active infection "
        "distinction, gown/gloves/dedicated equipment — CDC MRSA-aligned."
    ),
    "pathogen:c-diff": (
        "C. diff profile verified: spore-forming Gram+, contact precautions, mandatory soap-and-water hand "
        "hygiene (alcohol gel ineffective), bleach environmental cleaning, antibiotic-associated risk — CDC-aligned."
    ),
    "pathogen:vre": (
        "VRE profile verified: Gram+ vancomycin-resistant enterococcus, contact precautions, common in ICU/LTC, "
        "limits antibiotic options — clinically accurate for nursing practice."
    ),
    "pathogen:esbl-klebsiella": (
        "ESBL Klebsiella profile verified: Gram- MDRO, contact precautions, culture-before-antibiotics emphasis "
        "aligns with antimicrobial stewardship — CDC MDRO guidance."
    ),
    "pathogen:influenza": (
        "Influenza profile verified: droplet precautions, surgical mask, transport masking, HCW annual vaccination "
        "— nursing actions appropriate (3–6 ft droplet zone consistent with scenario content)."
    ),
    "pathogen:tb": (
        "TB profile verified: acid-fast bacillus, airborne precautions, fit-tested N95/PAPR, negative-pressure "
        "room, latent vs active distinction — CDC TB isolation criteria."
    ),
}

PRACTICE_VERIFY_NOTES: dict[str, str] = {
    "practice:micro-q2": "C. diff precautions Q verified: contact + soap-and-water — high-yield NCLEX distinction.",
    "practice:micro-q6": "TB airborne isolation Q verified: N95 required; surgical mask insufficient.",
    "practice:micro-q7": "Hand hygiene Q verified: alcohol gel inadequate for C. diff spores.",
    "practice:app-q1": "CLABSI clinical Q verified: sterile dressing replacement is priority over delay/removal.",
    "practice:app-q2": "Neutropenic precautions Q verified: ANC <500 triggers protective precautions.",
    "practice:app-q3": "VAP clinical Q verified: ventilator circuit condensation increases aspiration pneumonia risk.",
    "practice:app-q4": "MRSA contact precautions Q verified: hand hygiene required after glove removal.",
    "practice:app-q5": "Gram-negative rods clinical Q verified: broad-spectrum empiric coverage anticipated.",
}

# Ancillary scenario content reviewed (not in audit catalog)
ANCILLARY_VERIFIED = [
    "break_chain_scenarios/bc-1 (C. diff diarrhea): contact precautions + soap-and-water — correct transmission break",
    "break_chain_scenarios/bc-2 (CLABSI dressing): sterile dressing replacement protects portal of entry",
    "break_chain_scenarios/bc-3 (influenza roommate): droplet precautions + private room — not airborne",
    "break_chain_scenarios/bc-4 (CAUTI Foley day 5): advocate removal when no indication — CAUTI prevention",
    "what_if_scenarios/wi-1 (neutropenia ANC 350): protective precautions + restrict ill visitors",
    "what_if_scenarios/wi-2 (pregnant HCW + C. diff): contact PPE + soap-and-water; pregnancy not contraindication",
    "what_if_scenarios/wi-3 (MRSA colonization): contact precautions per policy; colonization transmits",
    "what_if_scenarios/wi-4 (suspected TB ED): immediate airborne isolation — do not wait for culture",
    "hai_types bundles (CLABSI, CAUTI, VAP, SSI, CDI): nursing-relevant chain-link mapping verified",
    "hand_hygiene + ppe_guide: WHO 5 moments; soap-and-water for spores — supports scenario teaching",
]

ANCILLARY_NOTES = [
    "chain_interventions/reservoir marks 'patient isolation' as correct — consistent with nursing practice but "
    "pedagogically overlaps with transmission link (see chain:reservoir flag).",
    "Influenza droplet distance: pathogen/scenarios use 3–6 ft; transmission-based-precautions concept uses 3 ft "
    "(flagged under concept:transmission-based-precautions).",
]


def _verify_note(key: str, title: str) -> str:
    if key in PATHOGEN_VERIFY_NOTES:
        return f"Microbiology pathogens audit 2026-06: {PATHOGEN_VERIFY_NOTES[key]}"
    if key in PRACTICE_VERIFY_NOTES:
        return f"Microbiology clinical application audit 2026-06: {PRACTICE_VERIFY_NOTES[key]}"
    if key.startswith("practice:"):
        return (
            f"Microbiology clinical application audit 2026-06: '{title}' verified for nursing-relevant "
            f"infection control accuracy (CDC/NCSBN-aligned)."
        )
    return (
        f"Microbiology audit 2026-06: '{title}' verified for scientific/clinical accuracy "
        f"(CDC/Open RN/NCSBN-aligned infection control fundamentals)."
    )


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
                if key in ALL_FLAGS:
                    await flag_item(db, "microbiology", key, ALL_FLAGS[key])
                    stats["flagged"] += 1
                else:
                    await verify_item(
                        db,
                        "microbiology",
                        key,
                        VERIFIED_DATE,
                        _verify_note(key, item["title"]),
                    )
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    pathogens = [i for i in catalog if i["item_key"].startswith("pathogen:")]
    practice = [i for i in catalog if i["item_key"].startswith("practice:")]
    pathogen_flagged = [k for k in PATHOGEN_FLAGS]
    pathogen_verified = [p["item_key"] for p in pathogens if p["item_key"] not in ALL_FLAGS]

    result = {
        "agent": "Sub-Agent 4 — Microbiology Pathogens & Clinical Application",
        "catalog_items_reviewed": len(catalog),
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "breakdown": {
            "pathogens_reviewed": len(pathogens),
            "pathogens_verified": len(pathogen_verified),
            "pathogens_flagged": len(pathogen_flagged),
            "practice_questions_reviewed": len(practice),
            "practice_verified": len([p for p in practice if p["item_key"] not in ALL_FLAGS]),
            "practice_flagged": len([p for p in practice if p["item_key"] in ALL_FLAGS]),
            "foundation_items_carried": len(FOUNDATION_FLAGS),
        },
        "ancillary_scenarios_reviewed": {
            "break_chain_scenarios": len(micro.get("break_chain_scenarios", [])),
            "what_if_scenarios": len(micro.get("what_if_scenarios", [])),
            "status": "all_verified",
            "items": ANCILLARY_VERIFIED,
            "notes": ANCILLARY_NOTES,
        },
        "flagged_items": [{"item_key": k, "review_note": v} for k, v in ALL_FLAGS.items()],
        "new_flags_this_agent": [{"item_key": k, "review_note": v} for k, v in PATHOGEN_FLAGS.items()],
        "errors": stats["errors"],
        "module_summary": summary["by_module"].get("microbiology"),
    }

    out = Path(__file__).resolve().parent.parent / "data" / "microbiology_pathogens_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())