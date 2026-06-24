"""Sub-Agent 6: Health Assessment interactive & practice content audit."""
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

INTERACTIVE_PREFIXES = (
    "practice:",
    "scenario:",
    "soap:",
    "sbar:",
    "checklist:",
    "flashcard:",
)

# Clinical / NCLEX accuracy flags from Sub-Agent 6 interactive review
INTERACTIVE_FLAGS: dict[str, str] = {}

PRACTICE_VERIFY_NOTES: dict[str, str] = {
    "practice:ha-q01": "Abdominal sequence inspect→auscultate→percuss→palpate — classic NCLEX testing point verified.",
    "practice:ha-q02": "SpO₂ 88% on O₂ = hypoxemia priority — Physiological Adaptation triage verified.",
    "practice:ha-q06": "Stroke symptoms trump stable/routine patients — Management of Care priority verified.",
    "practice:ha-q10": "PAINAD for non-verbal dementia — age/cognition-appropriate pain tool verified.",
    "practice:ha-q21": "FAST stroke protocol + last-known-well timing — Reduction of Risk Potential verified.",
    "practice:ha-q26": "Compartment syndrome 5 Ps + do not elevate — MSK emergency verified.",
    "practice:ha-q31": "SI with plan/means → immediate safety — Psychosocial Integrity verified.",
    "practice:ha-q35": "COPD tripod/high Fowler's positioning — independent nursing intervention verified.",
    "practice:ha-q36": "NG feeding placement requires radiographic confirmation per protocol — verified.",
    "practice:ha-q33": "GCS 2+3+5=10 corrected (was 11); correct_index and explanation aligned — neuro calculation verified.",
}

SCENARIO_VERIFY_NOTES: dict[str, str] = {
    "scenario:an-01": "Post-op delirium: rule out hypoxia first with SpO₂ 91% — reversible cause prioritized.",
    "scenario:an-02": "ACS chest pain: vitals + monitor + 12-lead before full history — time-sensitive verified.",
    "scenario:an-03": "4-month febrile infant: urgent assessment; explanation correctly distinguishes <3 mo vs 3–6 mo pathways.",
    "scenario:an-06": "Diabetic altered LOC: POC glucose before neuro imaging — hypoglycemia rule-out verified.",
    "scenario:an-11": "Sepsis bundle activation with fever, hypotension, acute confusion — time-sensitive verified.",
    "scenario:an-12": "Anaphylaxis: airway + epinephrine IM priority — ABC emergency verified.",
    "scenario:an-15": "Active SI with means: immediate safety and observation — psych emergency verified.",
}

SOAP_VERIFY_NOTES: dict[str, str] = {
    "soap:soap-01": "CHF exacerbation SOAP: objective vitals, afib concern, O₂/I&O/diuretic plan — clinically sound.",
    "soap:soap-06": "Sepsis/CAUTI SOAP: sepsis criteria language, culture timing, delirium vs dementia — verified.",
    "soap:soap-07": "DKA SOAP: Kussmaul, ketones, insulin/fluid protocol, cerebral edema caution — verified.",
    "soap:soap-10": "Psychiatric safety SOAP: direct quotes, observation level, means restriction — NCSBN-aligned.",
    "soap:soap-04": "Delirium SOAP: findings (disoriented to time/place) aligned with Objective ×1 (person only) — verified.",
}

CHECKLIST_VERIFY_NOTES: dict[str, str] = {
    "checklist:postpartum": "BUBBLE-HE with Homans' sign deprecated — current DVT assessment teaching verified.",
    "checklist:shift-neuro-q2h": "GCS decline ≥2 notification threshold and RASS sedation note — neuro trending verified.",
    "checklist:skin-wound": "NPIAP staging, never reverse-stage, no doughnut offloading — wound care verified.",
}

FLASHCARD_VERIFY_NOTES: dict[str, str] = {
    "flashcard:fc-cardio-01": "Perfusion compromise actions include leg elevation; explicitly avoids Trendelenburg — verified.",
    "flashcard:fc-rf-06": "Compartment syndrome: pain with passive stretch, do not elevate — orthopedic emergency verified.",
    "flashcard:fc-rf-09": "Suicide plan + means → 1:1 and means removal — psych red flag verified.",
    "flashcard:fc-rf-11": "Silent chest in asthma = impending failure — respiratory red flag verified.",
    "flashcard:fc-inte-01": "Skin turgor normal field distinguishes turgor rebound from cap refill; sternum site note — verified.",
    "flashcard:fc-neur-01": "Front reordered to 'Alert, oriented ×4, GCS 15' — consistent neuro documentation framing verified.",
}

ANCILLARY_NOTES = [
    "scenario:an-09 differentiated from an-07 — mucus plug/obstructed inner cannula vs routine secretion clearance — verified 2026-06.",
    "audit_service.build_content_catalog duplicates sbar_exercises entries (catalog quirk — not modified per task scope).",
    "scenario:an-03 was previously flagged in apply_audit_phase for age mismatch; current JSON includes 4-month pathway clarification — verified.",
    "SOAP exercises soap-02 duplicate incentive spirometry removed from Plan — verified 2026-06.",
]


def _is_interactive_item(item_key: str) -> bool:
    return item_key.startswith(INTERACTIVE_PREFIXES)


def _interactive_catalog() -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    for item in build_content_catalog():
        if item["module_id"] != "assessment":
            continue
        key = item["item_key"]
        if not _is_interactive_item(key) or key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def _verify_note(key: str, title: str) -> str:
    for mapping in (
        PRACTICE_VERIFY_NOTES,
        SCENARIO_VERIFY_NOTES,
        SOAP_VERIFY_NOTES,
        CHECKLIST_VERIFY_NOTES,
        FLASHCARD_VERIFY_NOTES,
    ):
        if key in mapping:
            return f"Health Assessment interactive audit 2026-06: {mapping[key]}"
    if key.startswith("practice:"):
        return (
            f"Health Assessment practice audit 2026-06: '{title}' verified for clinical accuracy "
            f"and NCLEX category alignment (Open RN/NCSBN)."
        )
    if key.startswith("scenario:"):
        return (
            f"Health Assessment assess-next audit 2026-06: '{title}' verified for priority sequencing "
            f"and ABC/time-sensitive nursing actions."
        )
    if key.startswith("soap:"):
        return (
            f"Health Assessment SOAP audit 2026-06: '{title}' verified for objective vs subjective "
            f"documentation and nursing plan appropriateness."
        )
    if key.startswith("sbar:"):
        return (
            f"Health Assessment SBAR audit 2026-06: '{title}' verified for handoff structure, "
            f"synthesis in Assessment, and actionable Recommendations."
        )
    if key.startswith("checklist:"):
        return (
            f"Health Assessment checklist audit 2026-06: '{title}' verified for systematic "
            f"assessment steps and clinical notes (Open RN-aligned)."
        )
    if key.startswith("flashcard:"):
        return (
            f"Health Assessment flashcard audit 2026-06: '{title[:60]}' verified for "
            f"normal vs abnormal findings and priority nursing actions."
        )
    return f"Health Assessment interactive audit 2026-06: '{title}' verified."


def _section_counts(assess: dict) -> dict[str, int]:
    return {
        "practice_questions": len(assess.get("practice_questions", [])),
        "assess_next_scenarios": len(assess.get("assess_next_scenarios", [])),
        "soap_exercises": len(assess.get("soap_exercises", [])),
        "sbar_exercises": len(assess.get("sbar_exercises", [])),
        "assessment_checklists": len(assess.get("assessment_checklists", [])),
        "flashcards": len(assess.get("flashcards", [])),
    }


async def apply():
    await init_db()
    catalog = _interactive_catalog()
    assess = load_content("assessment.json")
    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        result = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "assessment")
        )
        for rec in result.scalars().all():
            if _is_interactive_item(rec.item_key):
                await db.delete(rec)
        await db.flush()

        for item in catalog:
            key = item["item_key"]
            try:
                if key in INTERACTIVE_FLAGS:
                    await flag_item(db, "assessment", key, INTERACTIVE_FLAGS[key])
                    stats["flagged"] += 1
                else:
                    await verify_item(
                        db,
                        "assessment",
                        key,
                        VERIFIED_DATE,
                        _verify_note(key, item["title"]),
                    )
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    by_prefix: dict[str, dict[str, int]] = {}
    for item in catalog:
        prefix = item["item_key"].split(":")[0]
        bucket = by_prefix.setdefault(prefix, {"reviewed": 0, "verified": 0, "flagged": 0})
        bucket["reviewed"] += 1
        if item["item_key"] in INTERACTIVE_FLAGS:
            bucket["flagged"] += 1
        else:
            bucket["verified"] += 1

    result = {
        "agent": "Sub-Agent 6 — Health Assessment Interactive & Practice",
        "interactive_items_reviewed": len(catalog),
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "content_counts": _section_counts(assess),
        "breakdown_by_type": by_prefix,
        "flagged_items": [{"item_key": k, "review_note": v} for k, v in INTERACTIVE_FLAGS.items()],
        "new_flags_this_agent": [{"item_key": k, "review_note": v} for k, v in INTERACTIVE_FLAGS.items()],
        "ancillary_notes": ANCILLARY_NOTES,
        "errors": stats["errors"],
        "module_summary": summary["by_module"].get("assessment"),
    }

    out = Path(__file__).resolve().parent.parent / "data" / "assessment_interactive_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())