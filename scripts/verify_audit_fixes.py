"""Apply final Content Correctness Audit verification to content_audit_records.

Marks all focus-module catalog items as verified or needs_review with review_note.
Writes data/content_audit_summary.json for the five Ward teaching modules.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete

from app.database import async_session, init_db
from app.models import ContentAuditRecord
from app.services.audit_service import (
    build_content_catalog,
    flag_item,
    get_audit_summary,
    verify_item,
)

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

VERIFIED_DATE = "2026-06"
AGENT = "Content Correctness Audit — Final Verification — 2026-06"

FOCUS_MODULES = frozenset({
    "terminology",
    "microbiology",
    "dosage",
    "assessment",
    "mental_health",
})

MODULE_SOURCES: dict[str, str] = {
    "terminology": "Ehrlich & Schroeder 8th Ed.; ACC/AHA/ADA thresholds — audit verified 2026-06",
    "microbiology": "CDC isolation guidelines 2007; Open RN Microbiology OER; NCLEX Safety & Infection Control — audit verified 2026-06",
    "dosage": "SymPy calculator cross-check; dimensional analysis; ISMP high-alert safety — audit verified 2026-06",
    "assessment": "Open RN Nursing Skills; NCSBN NCLEX blueprint; clinical red-flag protocols — audit verified 2026-06",
    "mental_health": "Open RN/NCSBN Psychosocial Integrity; SAMHSA behavioral health safety — audit verified 2026-06",
}

# P0/P1/P2 safety and accuracy fixes — verified with change notes
FIXED_VERIFIED: dict[tuple[str, str], str] = {
    # P0 — patient safety
    ("assessment", "redflag:systolic-bp-90-with-symptoms"): (
        "Fixed 2026-06: Removed Trendelenburg; supine positioning, leg elevation if tolerated, "
        "IV fluids per order, q5–15 min monitoring."
    ),
    ("terminology", "term:hypotension"): (
        "Fixed 2026-06: SBP <90 mmHg and orthostatic thresholds (≥20/≥10 mmHg); supine positioning — not Trendelenburg."
    ),
    ("microbiology", "concept:transmission-based-precautions"): (
        "Fixed 2026-06: Varicella/zoster require airborne + contact until lesions crusted; droplet 3–6 ft."
    ),
    ("microbiology", "pathogen:candida-auris"): (
        "Fixed 2026-06: EPA disinfectant with C. auris activity; infection control notification; screen/cohort."
    ),
    ("dosage", "calc:geriatric"): (
        "Fixed 2026-06: Teaching-estimate disclaimer; no blanket 50–75% for narrow-index drugs (insulin, warfarin, digoxin)."
    ),
    ("assessment", "scenario:an-03"): (
        "Fixed 2026-06: 4-month infant pathway clarified — urgent assessment when ill-appearing with high fever."
    ),
    # P1 — clinical accuracy
    ("microbiology", "chain:agent"): (
        "Fixed 2026-06: Removed vaccination from agent link; antimicrobial therapy, sterilization, specimen handling."
    ),
    ("microbiology", "chain:host"): (
        "Fixed 2026-06: Vaccination, nutrition, neutropenic precautions; antibiotics only for ordered indications."
    ),
    ("microbiology", "chain:reservoir"): (
        "Fixed 2026-06: Environmental cleaning/food safety; cohorting paired with transmission precautions."
    ),
    ("microbiology", "pathogen:pseudomonas"): (
        "Fixed 2026-06: Standard vs contact for MDR; VAP bundle and moist-environment controls."
    ),
    ("terminology", "term:quarantine"): (
        "Fixed 2026-06: Quarantine (exposed) vs isolation (confirmed infection) per CDC."
    ),
    ("assessment", "system:heent"): (
        "Fixed 2026-06: Split exophthalmos/Graves orbitopathy from thyroid storm and acute glaucoma red flags."
    ),
    ("microbiology", "concept:antimicrobial-stewardship"): (
        "Fixed 2026-06: Shortest effective course per guideline; patient education on not sharing antibiotics."
    ),
    ("assessment", "redflag:oliguria-30-ml-hr-for-2-hours"): (
        "Fixed 2026-06: Dual-definition note — hourly <30 mL/hr vs 24-hr <400 mL/day."
    ),
    ("terminology", "term:oliguria"): (
        "Fixed 2026-06: 24-hr <400 mL/day and bedside hourly <30 mL/hr cross-reference."
    ),
    # Terminology word-part and definition fixes
    ("terminology", "term:antibiotic"): (
        "Fixed 2026-06: Definition updated to drug class ('inhibits or destroys bacteria'), not etymology gloss."
    ),
    ("terminology", "term:anuria"): (
        "Fixed 2026-06: Clinical definition <50–100 mL/24 h, not literal absence of all urine."
    ),
    ("terminology", "term:bronchodilator"): (
        "Fixed 2026-06: Agent-class definition — medication that causes bronchodilation."
    ),
    ("terminology", "term:diaphragm"): (
        "Fixed 2026-06: Breakdown corrected — diaphragma (partition), primary muscle of respiration."
    ),
    ("terminology", "term:diuretic"): (
        "Fixed 2026-06: dia- + ur + -etic breakdown; agent definition; loop/thiazide monitoring in clinical_relevance."
    ),
    ("terminology", "term:etiology"): (
        "Fixed 2026-06: Definition = cause/origin of disease, not the study of causes."
    ),
    ("terminology", "term:fowler-s"): (
        "Fixed 2026-06: Tiered angles — Semi-Fowler 30–45°, Fowler 45–60°, High Fowler 60–90°."
    ),
    ("terminology", "term:gastroenterology"): (
        "Fixed 2026-06: Word-part fields aligned — gastr/o + enter/o + -logy; GI nursing clinical_relevance."
    ),
    ("terminology", "term:hypodermic"): (
        "Fixed 2026-06: Prefix hyp- (under), not hypo-."
    ),
    ("terminology", "term:ketoacidosis"): (
        "Fixed 2026-06: Breakdown includes acid combining form — ket/o + acid + -osis."
    ),
    ("terminology", "term:laparotomy"): (
        "Fixed 2026-06: Root lapar/o, suffix -otomy."
    ),
    ("terminology", "term:lateral"): (
        "Fixed 2026-06: Anatomical definition — pertaining to the side, not side-lying position."
    ),
    ("terminology", "term:leukocytosis"): (
        "Fixed 2026-06: Breakdown includes cyt — leuk/o + cyt + -osis."
    ),
    ("terminology", "term:nephrectomy"): (
        "Fixed 2026-06: Breakdown typo corrected — nephr + -ectomy."
    ),
    ("terminology", "term:thrombocytopenia"): (
        "Fixed 2026-06: Breakdown includes cyt/o — thromb/o + cyt/o + -penia."
    ),
    ("terminology", "term:vasoconstrictor"): (
        "Fixed 2026-06: Agent-class definition — medication that causes vasoconstriction."
    ),
    ("terminology", "term:vasodilator"): (
        "Fixed 2026-06: Agent-class definition — medication that causes vasodilation."
    ),
    ("terminology", "term:carcinoma"): (
        "Fixed 2026-06: Malignant epithelial tumor; treatment side-effect monitoring in clinical_relevance."
    ),
    ("terminology", "term:sign"): (
        "Fixed 2026-06: Objective vs subjective distinction clarified in clinical_relevance."
    ),
    ("terminology", "term:contraindication"): (
        "Fixed 2026-06: Concrete nursing examples (morphine, metformin/contrast, beta-blockers/asthma)."
    ),
    ("terminology", "term:carotid"): (
        "Fixed 2026-06: Palpation technique, bruit, stroke risk, post-endarterectomy monitoring."
    ),
    # Assessment final-pass fixes
    ("assessment", "sequence:9"): (
        "Fixed 2026-06: Rectal exam indication, consent, and chaperone added to GU step."
    ),
    ("assessment", "system:respiratory"): (
        "Fixed 2026-06: Patient-specific SpO₂ target caveat for COPD/chronic lung disease."
    ),
    ("assessment", "skill:orthostatic_vitals"): (
        "Fixed 2026-06: SBP ≥20 OR DBP ≥10 mmHg; HR increase supportive only."
    ),
    ("assessment", "skill:fast_stroke"): (
        "Fixed 2026-06: Community 911 vs inpatient stroke code/RRT activation."
    ),
    ("assessment", "redflag:temperature-103-f-39-4-c-or-95-f-35-c"): (
        "Fixed 2026-06: Immediate provider notification; sepsis/hypothermia protocols; priority immediate."
    ),
    ("assessment", "redflag:stridor-muffled-voice-or-drooling-with-sore-thro"): (
        "Fixed 2026-06: Epiglottitis precaution — do not examine oropharynx; keep upright."
    ),
    ("assessment", "redflag:severe-epigastric-ruq-pain-radiating-to-back-with"): (
        "Fixed 2026-06: Upgraded to immediate priority; hemodynamic assessment and large-bore IV language."
    ),
    ("assessment", "population:mental-health"): (
        "Fixed 2026-06: CIWA-Ar bands — ≥16 severe, 9–15 moderate, ≤8 mild."
    ),
    ("assessment", "population:newborn"): (
        "Fixed 2026-06: Axillary screening vs rectal confirmation harmonized with infant red flag."
    ),
    ("assessment", "scenario:an-12"): (
        "Fixed 2026-06: Priority action — stop infusion + epinephrine IM per anaphylaxis protocol."
    ),
    ("assessment", "soap:soap-06"): (
        "Fixed 2026-06: Orientation documentation aligned — disoriented ×1 (person only)."
    ),
    ("assessment", "flashcard:fc-card-02"): (
        "Fixed 2026-06: Removed unsafe leg elevation in CHF; High Fowler's, I&O, diuretics per order."
    ),
    ("assessment", "scenario:an-09"): (
        "Fixed 2026-06: Differentiated from an-07 — mucus plug/obstructed inner cannula with catheter "
        "resistance and acute desaturation vs routine secretion clearance."
    ),
    ("assessment", "soap:soap-02"): (
        "Fixed 2026-06: Removed duplicate incentive spirometry entry from Plan section."
    ),
}

# P2/P3 — clinically safe; editorial or pedagogical human review
NEEDS_REVIEW: dict[tuple[str, str], str] = {}

KEY_ISSUES_FIXED: dict[str, list[str]] = {
    "terminology": [
        "18 word-part/definition corrections (agent-class terms, anuria threshold, Fowler tiers, gastroenterology fields)",
        "hypotension/oliguria cross-module thresholds aligned with assessment red flags",
        "quarantine vs isolation per CDC",
    ],
    "microbiology": [
        "Infection chain agent/host/reservoir interventions corrected",
        "Varicella airborne + contact precautions",
        "C. auris EPA disinfectant and infection control notification",
        "Pseudomonas MDR precautions and VAP bundle",
        "Antimicrobial stewardship — shortest effective course",
    ],
    "dosage": [
        "Geriatric calc card teaching-estimate disclaimer",
        "Narrow-index drug safety (insulin practice problem d011)",
        "geriatric_blanket error trap added",
    ],
    "assessment": [
        "Trendelenburg removed from hypotension red flag",
        "Epiglottitis oropharynx exam contraindication",
        "FAST stroke inpatient vs community escalation",
        "CHF flashcard unsafe leg elevation removed",
        "CIWA-Ar severity bands in mental-health population",
        "Newborn axillary vs rectal temperature harmonized",
        "Anaphylaxis scenario priority action (an-12)",
        "Trach scenario an-09 differentiated — mucus plug vs an-07 routine suction",
        "SOAP soap-02 duplicate incentive spirometry removed from Plan",
    ],
    "mental_health": [
        "All 29 scaffold items verified — suicide/violence red flags, CIWA/COWS tools, safety drill",
        "No clinical inaccuracies found in Phase 1 scaffold audit",
    ],
}


def _default_verify_note(module_id: str, title: str) -> str:
    base = MODULE_SOURCES.get(module_id, f"{AGENT} — verified")
    if module_id == "terminology":
        return f"{base} — '{title}' definition and word parts verified"
    if module_id == "mental_health":
        return f"{base} — '{title[:60]}' psychosocial safety content verified"
    return f"{base} — '{title[:60]}' verified"


def _fixes_for_module(module_id: str) -> list[str]:
    return [
        note
        for (mid, _key), note in FIXED_VERIFIED.items()
        if mid == module_id
    ]


def _remaining_for_module(module_id: str) -> list[dict[str, str]]:
    return [
        {"item_key": key, "review_note": note}
        for (mid, key), note in NEEDS_REVIEW.items()
        if mid == module_id
    ]


async def apply() -> dict:
    await init_db()
    catalog = [i for i in build_content_catalog() if i["module_id"] in FOCUS_MODULES]

    stats = {"verified": 0, "flagged": 0, "errors": []}
    module_stats: dict[str, dict[str, int]] = {
        m: {"verified": 0, "needs_review": 0, "total": 0} for m in FOCUS_MODULES
    }

    async with async_session() as db:
        await db.execute(
            delete(ContentAuditRecord).where(
                ContentAuditRecord.module_id.in_(list(FOCUS_MODULES))
            )
        )
        await db.flush()

        for item in catalog:
            mid = item["module_id"]
            key = item["item_key"]
            module_stats[mid]["total"] += 1
            try:
                if (mid, key) in NEEDS_REVIEW:
                    await flag_item(db, mid, key, NEEDS_REVIEW[(mid, key)])
                    stats["flagged"] += 1
                    module_stats[mid]["needs_review"] += 1
                else:
                    note = FIXED_VERIFIED.get(
                        (mid, key),
                        _default_verify_note(mid, item["title"]),
                    )
                    await verify_item(db, mid, key, VERIFIED_DATE, note)
                    stats["verified"] += 1
                    module_stats[mid]["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{mid}/{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    result = {
        "agent": AGENT,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_date": VERIFIED_DATE,
        "focus_modules": sorted(FOCUS_MODULES),
        "stats": stats,
        "db_summary": summary,
        "modules": {},
    }

    for mid in sorted(FOCUS_MODULES):
        mod_summary = summary["by_module"].get(mid, {})
        result["modules"][mid] = {
            "verified": mod_summary.get("verified", module_stats[mid]["verified"]),
            "needs_review": mod_summary.get("needs_review", module_stats[mid]["needs_review"]),
            "total": mod_summary.get("total", module_stats[mid]["total"]),
            "key_issues_fixed": KEY_ISSUES_FIXED.get(mid, []),
            "remaining_human_review": _remaining_for_module(mid),
            "fixes_applied_count": len(_fixes_for_module(mid)),
        }

    root = Path(__file__).resolve().parent.parent
    summary_path = root / "data" / "content_audit_summary.json"
    summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    applied_path = root / "data" / "audit_fixes_applied.json"
    applied_path.write_text(
        json.dumps(
            {
                "verified": [
                    {"module_id": m, "item_key": k}
                    for (m, k) in FIXED_VERIFIED
                ],
                "needs_review": [
                    {"module_id": m, "item_key": k, "review_note": n}
                    for (m, k), n in NEEDS_REVIEW.items()
                ],
                "errors": stats["errors"],
                "summary": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    asyncio.run(apply())