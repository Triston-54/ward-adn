"""Apply Content Correctness Audit Phase decisions to content_audit_records."""
from __future__ import annotations

import asyncio
import json
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

VERIFIED_DATE = "2026-06"
DEFAULT_SOURCE = "Content Correctness Audit Phase 2026-06 — nursing/NCLEX accuracy verified"

# ── Flagged items with review_note (all other catalog items in module → verified) ──

TERMINOLOGY_FLAGS: dict[str, str] = {
    "term:antibiotic": "Definition is etymology gloss ('Against life'), not clinical definition. Fix: 'Drug that inhibits or destroys bacteria.'",
    "term:anuria": "Definition 'absence of urine output' is imprecise. Clinically anuria is <50–100 mL/24 h in adults, not necessarily zero. Fix definition accordingly.",
    "term:bronchodilator": "Definition describes the process, not the drug class. Fix: 'Agent/medication that widens the bronchi.'",
    "term:diaphragm": "Breakdown incorrectly uses phren (mind). Diaphragm = partition/barrier muscle. Fix breakdown to reflect anatomical etymology.",
    "term:diuretic": "Definition describes action, not drug class; breakdown omits dia-. Fix definition and breakdown with dia (through) + ur + -etic.",
    "term:etiology": "Definition says 'Study of disease cause' — that is etiology research, not etiology itself. Fix: 'Cause or origin of a disease.'",
    "term:fowler-s": "Definition '45–90°' conflates Fowler and High Fowler; omits Semi-Fowler (30–45°). Fix with tiered angle ranges.",
    "term:gastroenterology": "breakdown/clinical_relevance fields swapped; suffix shows '-entero' instead of '-logy'. Fix field alignment.",
    "term:hypodermic": "Prefix labeled hypo- but hypodermic uses hyp- (under). Per Ehrlich: prefix='hyp-', breakdown='hyp- + derm + -ic'.",
    "term:ketoacidosis": "Breakdown omits acid combining form. Fix: 'ket/o + acid + -osis'.",
    "term:laparotomy": "Root incorrectly '-tomy' (suffix). Fix: root='lapar/o', suffix='-otomy'.",
    "term:lateral": "Definition conflates anatomical 'pertaining to side' with side-lying position. Fix anatomical definition; note position separately.",
    "term:leukocytosis": "Breakdown omits cyt (cell). Fix: 'leuk/o + cyt + -osis'.",
    "term:nephrectomy": "Breakdown typo 'nephrr'. Fix: 'nephr + -ectomy'.",
    "term:quarantine": "Conflates quarantine (exposed persons) with isolation (infected persons). Fix with distinct definitions per CDC.",
    "term:thrombocytopenia": "Breakdown omits cyt/o (cell). Fix: 'thromb/o + cyt/o + -penia'.",
    "term:vasoconstrictor": "Definition describes process, not agent. Fix: 'Agent/medication that narrows blood vessels.'",
    "term:vasodilator": "Definition describes process, not agent. Fix: 'Agent/medication that widens blood vessels.'",
    "term:oliguria": "Cross-module: <400 mL/24 h definition conflicts with assessment hourly trigger <30 mL/hr (~720 mL/day). Add dual-definition teaching note bridging hourly I&O vs 24-hr AKI criteria.",
    "term:hypotension": "Cross-module: no numeric threshold in term; assessment uses SBP <90 (shock) vs geriatric SBP <100. Add context-specific thresholds to clinical_relevance.",
}

MICROBIOLOGY_FLAGS: dict[str, str] = {
    "chain:agent": "Intervention lists vaccination under infectious agent link; vaccination targets susceptible host. Remove vaccination; use antimicrobial therapy, sterilization, specimen handling.",
    "concept:transmission-based-precautions": "Varicella requires BOTH airborne (N95, negative pressure) AND contact precautions per CDC 2007 — not airborne alone until lesions crusted.",
}

DOSAGE_FLAGS: dict[str, str] = {
    "calc:geriatric": "Blanket 50–75% dose reduction on calc card is misleading for narrow-index drugs (insulin, warfarin, digoxin). Add qualifier: teaching estimate only; verify drug-specific/renal guidance.",
}

ASSESSMENT_FLAGS: dict[str, str] = {
    "system:heent": "Red flag 'Exophthalmos + headache — glaucoma emergency' is mismatched. Exophthalmos suggests thyroid eye disease; acute glaucoma = severe eye pain, halos, mid-dilated pupil. Replace red flag.",
    "redflag:systolic-bp-90-with-symptoms": "Recommends Trendelenburg — outdated/harmful. Replace with supine positioning, leg elevation if tolerated, IV fluids, frequent reassessment.",
    "redflag:oliguria-30-ml-hr-for-2-hours": "Hourly <30 mL/hr trigger conflicts with term:oliguria <400 mL/24 h. Add dual-definition note (hourly nursing trigger vs 24-hr AKI definition).",
    "scenario:an-03": "Explanation cites febrile infant <3 months protocol but patient is 4 months. Align age-stratified fever guidance to case age or note 4-month ED pathway.",
}

MODULE_SOURCES: dict[str, str] = {
    "terminology": "Ehrlich & Schroeder 8th Ed.; ACC/AHA/ADA thresholds where applicable — audit verified 2026-06",
    "microbiology": "CDC isolation guidelines 2007; Open RN Microbiology OER; NCLEX Safety & Infection Control — audit verified 2026-06",
    "dosage": "SymPy calculator cross-check; dimensional analysis formulas; ISMP high-alert safety — audit verified 2026-06",
    "assessment": "Open RN Nursing Skills; NCSBN NCLEX blueprint; clinical red-flag protocols — audit verified 2026-06",
}


async def apply():
    await init_db()
    catalog = build_content_catalog()
    flags_by_module = {
        "terminology": TERMINOLOGY_FLAGS,
        "microbiology": MICROBIOLOGY_FLAGS,
        "dosage": DOSAGE_FLAGS,
        "assessment": ASSESSMENT_FLAGS,
    }

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        await db.execute(delete(ContentAuditRecord))
        await db.flush()

        for item in catalog:
            mid = item["module_id"]
            key = item["item_key"]
            module_flags = flags_by_module.get(mid, {})
            try:
                if key in module_flags:
                    await flag_item(db, mid, key, module_flags[key])
                    stats["flagged"] += 1
                else:
                    note = MODULE_SOURCES.get(mid, DEFAULT_SOURCE)
                    if mid == "terminology":
                        note = f"Ehrlich 8th Ed.; {item['title']} — definition and word parts verified"
                    await verify_item(db, mid, key, VERIFIED_DATE, note)
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{mid}/{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    result = {
        "stats": stats,
        "summary": {
            "total": summary["total"],
            "verified": summary["verified"],
            "needs_review": summary["needs_review"],
            "unreviewed": summary["unreviewed"],
            "by_module": summary["by_module"],
        },
    }
    out_path = Path(__file__).resolve().parent.parent / "data" / "audit_phase_result.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())