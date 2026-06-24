"""Pathophysiology module full content audit — all 76 catalog items."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.database import async_session, init_db
from app.models import ContentAuditRecord
from app.services.audit_service import build_content_catalog, flag_item, get_audit_summary, verify_item
from app.services.content_loader import load_content

VERIFIED_DATE = "2026-06"
AGENT_NAME = "Pathophysiology Full Content Audit — 2026-06"

# Items requiring human follow-up after clinical review (metadata / teaching-depth nuance)
NEEDS_REVIEW_FLAGS: dict[str, str] = {
    "concept:immune-response": (
        "[Core Concepts] Clinical content is accurate (innate vs adaptive immunity, neutropenic precautions). "
        "source_ref cites 'Open RN — Microbiology' Ch. 7 rather than Pathophysiology module source — "
        "cross-module citation inconsistency for content inventory. Fix: align source_ref to Pathophysiology "
        "OER chapter or document intentional cross-link in manifest."
    ),
}

HIGH_YIELD_VERIFY_NOTES: dict[str, str] = {
    # Core concepts — safety-critical
    "concept:electrolyte-balance": (
        "Na⁺/K⁺/Ca²⁺ roles, acid-base K⁺ shifts, digoxin toxicity with hypokalemia, hyperkalemia ECG "
        "progression, and never IV K⁺ push — verified for NCLEX Reduction of Risk Potential."
    ),
    "concept:acid-base-abg": (
        "ABG interpretation sequence (pH → PaCO₂ vs HCO₃⁻ → compensation → anion gap), MUDPILES mnemonic, "
        "and COPD baseline compensation caveat verified — Open RN Ch. 10 aligned."
    ),
    "concept:compensation-decompensation": (
        "RAAS, baroreceptor, and respiratory compensation examples with CHF/septic decompensation "
        "triggers verified for Physiological Adaptation prioritization."
    ),
    "concept:clotting-hemostasis": (
        "Primary/secondary hemostasis, anticoagulant MOA, and HIT thrombosis despite low platelets "
        "verified — critical bleeding precaution teaching."
    ),
    "concept:inflammation-stages": (
        "Cardinal signs, vascular/cellular phases verified. Updated Sepsis-3 language (infection + organ "
        "dysfunction) replaces outdated SIRS-only framing in clinical_relevance."
    ),
    # Disease processes — high-yield
    "disease:chf": (
        "RAAS cascade, left vs right manifestations, daily weight thresholds, diuretic K⁺/renal monitoring "
        "verified — Open RN Ch. 19 aligned."
    ),
    "disease:copd": (
        "Emphysema/bronchitis patho, compensated chronic respiratory acidosis wording corrected, "
        "SpO₂ 88–92% titration and ABG baseline monitoring verified (GOLD/NCLEX-aligned)."
    ),
    "disease:hypovolemic-shock": (
        "Volume loss cascade, flat JVD differentiation, fluid resuscitation priorities, and cardiac "
        "status assessment before fluids verified."
    ),
    "disease:cardiogenic-shock": (
        "Pump failure cascade, pulmonary congestion, inotrope vs fluid overload contraindication, "
        "and poor forward flow urine output wording verified."
    ),
    "disease:sepsis": (
        "Distributive shock patho, hour-1 bundle, qSOFA screening, lactate escalation, MAP ≥65 "
        "verified — Surviving Sepsis Campaign 2021 aligned."
    ),
    "disease:dka": (
        "Insulin deficiency → ketogenesis, K⁺ transcellular shifts, fluids before insulin, hold insulin "
        "if K⁺ <3.3 mEq/L verified — ADA crisis management aligned."
    ),
    "disease:dm-type2": (
        "Insulin resistance cascade, micro/macrovascular complications, HHNS threshold, hypoglycemia "
        "15/15 rule verified."
    ),
    "disease:renal-failure": (
        "Prerenal/intrarenal/postrenal etiologies, hyperkalemia, metabolic acidosis, dialysis access "
        "care verified."
    ),
    "disease:ards": (
        "Non-cardiogenic edema, surfactant dysfunction, ARDSnet low tidal volume, prone positioning "
        "verified."
    ),
    "disease:stroke": (
        "Ischemic vs hemorrhagic, penumbra, CT before thrombolytics, NPO/swallow, HOB 30° verified."
    ),
    # Compare & contrast
    "compare:shock-hypo-vs-cardio": (
        "JVD/lung sounds differentiation before fluid bolus — classic NCLEX shock discrimination verified."
    ),
    "compare:dka-vs-hhns": (
        "Ketones/acidosis vs hyperosmolarity, glucose ranges, K⁺ replacement before insulin verified."
    ),
    "compare:prerenal-vs-intrarenal": (
        "BUN:Cr ratio, urine Na, FENa, muddy brown casts verified; diuretic confounder caveat added."
    ),
    # Scenarios
    "scenario:wb-na-k-pump": (
        "Na⁺/K⁺-ATPase failure → cellular K⁺ leak post-arrest; peaked T waves mechanism verified."
    ),
    "scenario:wb-insulin-deficiency": (
        "DKA K⁺ 5.8 mEq/L — total body depletion vs serum level; never IV K⁺ push verified."
    ),
    "scenario:wb-capillary-permeability": (
        "Septic distributive shock with warm skin and capillary leak despite fluids verified."
    ),
    # Flashcards — safety
    "flashcard:fc-7": (
        "COPD O₂ titration updated: SpO₂ 88–92%, ABG baseline, excessive O₂ CO₂ retention risk "
        "(hypoxic-drive oversimplification removed)."
    ),
    "flashcard:fc-11": (
        "DKA insulin hold threshold K⁺ <3.3 mEq/L and false-normal serum K⁺ verified."
    ),
    "flashcard:fc-15": (
        "Hyperkalemia ECG progression peaked T → QRS → sine wave verified."
    ),
    "flashcard:fc-19": (
        "Berlin ARDS P/F <300 with PEEP ≥5 and bilateral infiltrates verified."
    ),
    "flashcard:fc-23": (
        "qSOFA as screening/risk stratification (not standalone sepsis diagnosis) verified."
    ),
    # Practice — prioritization
    "practice:patho-q2": (
        "Cardiogenic vs hypovolemic shock — JVD and crackles as differentiator verified."
    ),
    "practice:patho-q4": (
        "DKA K⁺ monitoring before insulin; never IV K⁺ push verified."
    ),
    "practice:patho-q6": (
        "Septic shock refractory hypotension → vasopressor after fluids verified."
    ),
    "practice:patho-q8": (
        "Stroke protocol + CT before thrombolytics verified."
    ),
    "practice:patho-q18": (
        "K⁺ 6.8 mEq/L — continuous cardiac monitoring and immediate escalation verified."
    ),
}

SECTION_MAP = {
    "concept:": "core_concepts",
    "disease:": "disease_processes",
    "compare:": "compare_contrast",
    "scenario:": "what_breaks_down",
    "flashcard:": "flashcards",
    "practice:": "practice",
}


def _section_for_key(key: str) -> str:
    for prefix, section in SECTION_MAP.items():
        if key.startswith(prefix):
            return section
    return "other"


def _verify_note(key: str, title: str) -> str:
    if key in HIGH_YIELD_VERIFY_NOTES:
        return f"Pathophysiology audit 2026-06: {HIGH_YIELD_VERIFY_NOTES[key]}"
    section = _section_for_key(key)
    return (
        f"Pathophysiology audit 2026-06 ({section}): '{title[:70]}' verified for disease process "
        f"accuracy, nursing priorities, and NCLEX Physiological Integrity alignment (Open RN OER / NCSBN)."
    )


def _section_breakdown(catalog: list[dict], flagged_keys: set[str]) -> dict[str, dict[str, int]]:
    breakdown: dict[str, dict[str, int]] = {}
    for item in catalog:
        section = _section_for_key(item["item_key"])
        bucket = breakdown.setdefault(section, {"total": 0, "verified": 0, "flagged": 0})
        bucket["total"] += 1
        if item["item_key"] in flagged_keys:
            bucket["flagged"] += 1
        else:
            bucket["verified"] += 1
    return breakdown


async def apply():
    await init_db()
    patho = load_content("pathophysiology.json")
    catalog = [i for i in build_content_catalog() if i["module_id"] == "pathophysiology"]
    flagged_keys = set(NEEDS_REVIEW_FLAGS)

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        result = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "pathophysiology")
        )
        for rec in result.scalars().all():
            await db.delete(rec)
        await db.flush()

        for item in catalog:
            key = item["item_key"]
            try:
                if key in NEEDS_REVIEW_FLAGS:
                    await flag_item(db, "pathophysiology", key, NEEDS_REVIEW_FLAGS[key])
                    stats["flagged"] += 1
                else:
                    await verify_item(
                        db,
                        "pathophysiology",
                        key,
                        VERIFIED_DATE,
                        _verify_note(key, item["title"]),
                    )
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    content_fixes = [
        "concept:inflammation-stages — Sepsis-3 organ dysfunction language replaced outdated SIRS-only framing",
        "disease:copd — clinical manifestation corrected to compensated chronic respiratory acidosis (not primary metabolic alkalosis)",
        "disease:copd — nursing O₂ priorities updated to SpO₂ 88–92% titration with ABG baseline monitoring",
        "disease:cardiogenic-shock — urine output description corrected (poor forward flow, not volume depletion)",
        "disease:pneumonia — positioning priority clarified (reposition q2h; affected-side-up only for abscess/effusion)",
        "disease:sepsis — patho cascade updated from SIRS terminology to dysregulated cytokine response",
        "compare:prerenal-vs-intrarenal — diuretic/bicarbonate/GI bleed confounder caveat added to clinical_pearls",
        "flashcard:fc-7 — COPD O₂ caution updated (removed hypoxic-drive oversimplification; ABG baseline emphasis)",
        "flashcard:fc-19 — Berlin ARDS P/F ratio includes PEEP ≥5 requirement",
    ]

    result_payload = {
        "agent": AGENT_NAME,
        "catalog_items_reviewed": len(catalog),
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "content_counts": {
            "core_concepts": len(patho.get("core_concepts", [])),
            "disease_processes": len(patho.get("disease_processes", [])),
            "compare_contrast_pairs": len(patho.get("compare_contrast_pairs", [])),
            "what_breaks_down_scenarios": len(patho.get("what_breaks_down_scenarios", [])),
            "flashcards": len(patho.get("flashcards", [])),
            "practice_questions": len(patho.get("practice_questions", [])),
        },
        "breakdown_by_section": _section_breakdown(catalog, flagged_keys),
        "content_fixes_applied": content_fixes,
        "flagged_items": [
            {"item_key": k, "section": _section_for_key(k), "review_note": v}
            for k, v in NEEDS_REVIEW_FLAGS.items()
        ],
        "errors": stats["errors"],
        "module_audit_summary": summary["by_module"].get("pathophysiology"),
        "focus_areas_reviewed": [
            "Shock types (hypovolemic, cardiogenic, septic/distributive) — differentiation and treatment",
            "Heart failure — RAAS cascade, compensation/decompensation, daily weights",
            "COPD — chronic hypercapnia, O₂ titration, ABG baseline interpretation",
            "Diabetes — DKA vs HHNS, K⁺ management before insulin",
            "Electrolytes and acid-base — ABG interpretation, anion gap, Kussmaul respirations",
            "Renal failure — prerenal vs intrarenal AKI, hyperkalemia ECG progression",
            "Scenarios and practice — correct_index, rationale, NCLEX prioritization",
        ],
    }

    out = Path(__file__).resolve().parent.parent / "data" / "pathophysiology_audit.json"
    out.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())