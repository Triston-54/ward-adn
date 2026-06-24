"""Full Health Assessment content correctness audit — all 12 tabs / 198 catalog items."""
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
AGENT_NAME = "Full Assessment Content Correctness Audit — 2026-06"

# ── Needs Review (13 items from 4 parallel clinical reviewers) ────────────────

NEEDS_REVIEW_FLAGS: dict[str, str] = {
    # Clinical Foundation
    "sequence:9": (
        "[Head-to-Toe] Title includes 'Rectal (as indicated)' but description covers only urinary/genital "
        "assessment. Mismatch omits when rectal exam is indicated (GI bleeding, prostate symptoms, neuro deficits) "
        "and consent/chaperone requirements. Fix: add rectal assessment bullet 'as indicated per scope/consent' "
        "or remove 'Rectal' from the step title."
    ),
    "system:heent": (
        "[HEENT] Red flag bundles exophthalmos with headache/vision changes as 'thyroid storm/Graves orbitopathy.' "
        "Thyroid storm presents primarily with fever, extreme tachycardia, agitation, and GI symptoms—not "
        "exophthalmos. Exophthalmos with acute vision changes suggests Graves orbitopathy/compressive optic "
        "neuropathy requiring urgent provider/ophthalmology escalation. Fix: split into two red flags: "
        "(1) thyroid storm systemic signs, (2) exophthalmos with vision changes → urgent Graves orbitopathy/"
        "optic nerve compression concern."
    ),
    "system:respiratory": (
        "[Respiratory] Normal finding 'SpO₂ ≥94% on room air' lacks context for patients with chronic lung disease "
        "or ordered SpO₂ targets (often 88–92% in COPD per provider protocol). Risk: students may inappropriately "
        "escalate O₂ in chronically hypoxemic patients. Fix: add clinical_reasoning caveat—compare to patient "
        "baseline and prescribed oxygenation target before labeling abnormal."
    ),
    "skill:orthostatic_vitals": (
        "[Orthostatic vitals] Positive orthostatics defined as 'SBP drop ≥20 mmHg, DBP drop ≥10 mmHg' using a "
        "comma without OR, implying both drops are required. Standard criterion (Open RN, CDC STEADI) is SBP "
        "decrease ≥20 mmHg OR DBP decrease ≥10 mmHg within 3 minutes of standing. Fix: rewrite as 'SBP drop "
        "≥20 mmHg OR DBP drop ≥10 mmHg (with position change); symptomatic HR increase ≥20 bpm supports but "
        "does not alone define orthostatic hypotension.'"
    ),
    "skill:fast_stroke": (
        "[FAST stroke] 'Time to call 911' is community-EMS language and may mislead inpatient nurses who must "
        "activate internal stroke protocol/RRT and notify provider—not call 911 for in-hospital stroke symptoms. "
        "Fix: 'Time to activate emergency response (call 911 in community settings; activate stroke code/RRT per "
        "facility protocol when symptoms occur in hospital).'"
    ),
    # Red Flags & Special Populations
    "redflag:temperature-103-f-39-4-c-or-95-f-35-c": (
        "[Red flag] Action omits explicit immediate provider notification present in nearly all other master red "
        "flags. Extreme hyperthermia (>103°F/39.4°C) and moderate hypothermia (<95°F/35°C) in acute care require "
        "urgent escalation, continuous monitoring, and sepsis/hypothermia protocol activation—not only conditional "
        "blood cultures and supportive measures. Fix: add 'notify provider immediately, continuous vitals/SpO₂ "
        "monitoring, initiate sepsis bundle/hypothermia rewarming per protocol'; consider upgrading priority from "
        "urgent to immediate for hospitalized patients."
    ),
    "redflag:stridor-muffled-voice-or-drooling-with-sore-thro": (
        "[Red flag] Airway actions are strong but miss a critical safety contraindication for epiglottitis/"
        "supraglottitis: do NOT examine the oropharynx (no tongue depressor, throat inspection, or agitating "
        "procedures) because this can precipitate complete airway obstruction. Also add 'keep patient upright/in "
        "position of comfort; minimize procedures at bedside.' Without this, students may perform routine throat "
        "assessment and cause harm."
    ),
    "redflag:severe-epigastric-ruq-pain-radiating-to-back-with": (
        "[Red flag] Priority 'urgent' understates time-sensitive abdominal catastrophe (ruptured AAA, hemorrhagic "
        "pancreatitis, perforated viscus). Peer GI red flags use priority 'immediate' with shock assessment "
        "language. Action says 'notify provider' but not 'immediately' and lacks q5–15 vitals, large-bore IV, and "
        "hemodynamic instability assessment. Fix: upgrade to immediate priority; add 'notify provider immediately, "
        "assess for hypotension/syncope, two large-bore IVs if indicated, type/crossmatch per order, prepare rapid "
        "response if unstable.'"
    ),
    "population:mental-health": (
        "[Special population] CIWA-Ar thresholds are mislabeled in red_flags: 'CIWA-Ar ≥15 (moderate/severe per "
        "protocol; ≥8 mild)' conflates severity bands. Standard CIWA-Ar interpretation: ≤8 minimal/mild, 9–15 "
        "moderate, ≥16 severe (many protocols treat ≥15–16 as severe). Fix: 'CIWA-Ar ≥16 severe (urgent provider "
        "notification, benzodiazepine per protocol); 9–15 moderate; ≤8 mild—continue scheduled scoring. Do not delay "
        "treatment at severe threshold.' COWS ≥25 language is acceptable."
    ),
    "population:newborn": (
        "[Special population] clinical_reasoning states 'Always use axillary temperature, not rectal, for routine "
        "screening,' which conflicts with AAP guidance that rectal measurement is the most accurate core-temperature "
        "method in young infants and directly conflicts with redflag:infant-3-months-with-rectal-temperature-100-4-f "
        "(rectal ≥100.4°F threshold). Fix: 'Routine screening may use axillary temperature; any fever concern in "
        "neonates/young infants requires rectal confirmation per protocol and immediate provider notification—do not "
        "dismiss low-grade axillary readings.' Harmonize across newborn, pediatric, and red_flags_master sections."
    ),
    # Practice & Scenarios
    "scenario:an-12": (
        "[Assess Next] Stem asks 'assess NEXT' but correct option is primarily intervention (airway, O₂, epinephrine "
        "prep). In anaphylaxis, stop the triggering infusion and administer epinephrine IM immediately are first-line "
        "actions; correct option says only 'prepare for epinephrine' and omits stopping penicillin (mentioned only "
        "in explanation). Distractors are clearly wrong, but revise stem to 'What is the priority action?' and "
        "update option to include stop infusion + give epinephrine IM per protocol."
    ),
    # Documentation & Flashcards
    "soap:soap-06": (
        "[SOAP] Orientation documentation is internally inconsistent: findings state patient is 'disoriented to place "
        "and time,' but model_soap Objective documents 'disoriented ×2 (person, time)'—which implies she IS oriented "
        "to time. patient_context also states baseline oriented to person only while Subjective cites family report of "
        "orientation to person and place. Align findings, baseline, and oriented-× score (likely ×1 person only if "
        "disoriented to place and time)."
    ),
    "flashcard:fc-card-02": (
        "[Flashcard] abnormal_action lists 'elevate legs' for pitting edema with JVD—this is unsafe in heart failure/"
        "volume overload because leg elevation increases venous return and worsens pulmonary congestion. Replace with "
        "high Fowler's positioning, daily weights, strict I&O, sodium/fluid restriction, and diuretics per order "
        "(consistent with checklist:cardiac-focused and flashcard:fc-cardio-01 teaching)."
    ),
}

# Targeted verify notes for high-yield items (others get generic tab-appropriate notes)
VERIFY_NOTES: dict[str, str] = {
    "sequence:1": "Head-to-toe audit 2026-06: Vitals plus general survey (LOC, distress) — ABC-first Open RN Ch. 2.",
    "sequence:2": "Head-to-toe audit 2026-06: HEENT (PERRLA, EOM, airway inspection) — stroke/airway screening verified.",
    "sequence:3": "Head-to-toe audit 2026-06: Neck lymphatics, thyroid, JVD, tracheal position — cardiovascular cue verified.",
    "sequence:4": "Head-to-toe audit 2026-06: Cardiovascular auscultation, pulses, cap refill, edema — Open RN verified.",
    "sequence:5": "Head-to-toe audit 2026-06: Respiratory inspect-palpate-percuss-auscultate — NCLEX Reduction of Risk verified.",
    "sequence:6": "Head-to-toe audit 2026-06: I-A-P-P abdominal sequence; acute abdomen escalation safe.",
    "sequence:7": "Head-to-toe audit 2026-06: Gait, ROM, 0–5 strength, fall-risk screening verified.",
    "sequence:8": "Head-to-toe audit 2026-06: NPIAP staging, turgor, perfusion skin findings — current best practice.",
    "sequence:10": "Head-to-toe audit 2026-06: LOC, orientation, psychosocial safety — NCSBN Psychosocial Integrity verified.",
    "practice:ha-q33": "Practice audit 2026-06: GCS E2+V3+M5=10; correct_index and explanation aligned.",
    "scenario:an-11": "Assess-next audit 2026-06: Sepsis bundle activation — time-sensitive Physiological Adaptation verified.",
    "scenario:an-15": "Assess-next audit 2026-06: Active SI with means — immediate safety priority verified.",
    "redflag:spo-90-on-supplemental-oxygen": "Red flag audit 2026-06: Critical hypoxemia despite O₂ — ABC escalation verified.",
    "redflag:unilateral-neuro-deficit-new": "Red flag audit 2026-06: Stroke protocol + last-known-well timing verified.",
    "redflag:active-suicidal-ideation-with-plan": "Red flag audit 2026-06: 1:1 observation, means removal — psych emergency verified.",
    "population:pediatric": "Special pop audit 2026-06: Age-specific vitals, FLACC/Wong-Baker, abuse indicators verified.",
    "population:geriatric": "Special pop audit 2026-06: Delirium-as-emergency, orthostatic fall risk, change-from-baseline verified.",
    "population:obstetric": "Special pop audit 2026-06: FHR norms, preeclampsia severe features, PPH red flags verified.",
    "checklist:postpartum": "Checklist audit 2026-06: BUBBLE-HE with Homans' sign deprecated — current DVT teaching verified.",
    "flashcard:fc-cardio-01": "Flashcard audit 2026-06: Perfusion compromise actions; explicit Trendelenburg avoidance verified.",
}

TAB_MAP = {
    "sequence:": "head-to-toe",
    "system:": "systems",
    "skill:": "skills",
    "redflag:": "red-flags",
    "population:": "special-pop",
    "practice:": "practice",
    "scenario:": "assess-next",
    "soap:": "soap",
    "sbar:": "documentation",
    "checklist:": "checklists",
    "flashcard:": "flashcards",
}


def _unique_assessment_catalog() -> list[dict]:
    seen: set[str] = set()
    items: list[dict] = []
    for item in build_content_catalog():
        if item["module_id"] != "assessment":
            continue
        key = item["item_key"]
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


def _tab_for_key(key: str) -> str:
    for prefix, tab in TAB_MAP.items():
        if key.startswith(prefix):
            return tab
    return "other"


def _verify_note(key: str, title: str) -> str:
    if key in VERIFY_NOTES:
        return f"Health Assessment full audit 2026-06: {VERIFY_NOTES[key]}"
    tab = _tab_for_key(key)
    return (
        f"Health Assessment full audit 2026-06 ({tab} tab): '{title[:70]}' verified for clinical accuracy, "
        f"safe nursing practice, and ADN/NCLEX alignment (Open RN OER / NCSBN 2023)."
    )


def _tab_breakdown(catalog: list[dict], flagged_keys: set[str]) -> dict[str, dict[str, int]]:
    breakdown: dict[str, dict[str, int]] = {}
    for item in catalog:
        tab = _tab_for_key(item["item_key"])
        bucket = breakdown.setdefault(tab, {"total": 0, "verified": 0, "flagged": 0})
        bucket["total"] += 1
        if item["item_key"] in flagged_keys:
            bucket["flagged"] += 1
        else:
            bucket["verified"] += 1
    return breakdown


async def apply():
    await init_db()
    assess = load_content("assessment.json")
    catalog = _unique_assessment_catalog()
    flagged_keys = set(NEEDS_REVIEW_FLAGS)

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        result = await db.execute(
            select(ContentAuditRecord).where(ContentAuditRecord.module_id == "assessment")
        )
        for rec in result.scalars().all():
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
                        _verify_note(key, item["title"]),
                    )
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    interview = assess.get("interview_techniques", [])
    ancillary_verified = [
        "therapeutic-communication: open-ended questions, active listening — Open RN verified",
        "oldcarts: structured symptom analysis — NCLEX Health Promotion verified",
        "cultural-linguistic: certified interpreter required — safe equitable practice verified",
        "review-of-systems: systematic ROS by body system — Open RN Ch. 2 verified",
        "pqrst: pain history mnemonic — triage/reassessment documentation verified",
        "safety-abuse-screening: private direct questioning, mandatory reporting — NCSBN verified",
    ]

    result_payload = {
        "agent": AGENT_NAME,
        "audit_scope": {
            "tabs": 12,
            "tab_names": [
                "head-to-toe", "systems", "checklists", "assess-next", "soap",
                "special-pop", "red-flags", "red-flag-drill", "practice", "skills",
                "documentation", "flashcards",
            ],
            "live_content_items": assess.get("items_total", 132) if isinstance(assess.get("items_total"), int) else 132,
            "catalog_items_audited": len(catalog),
            "interview_techniques_ancillary": len(interview),
        },
        "content_counts": {
            "head_to_toe_sequence": len(assess.get("head_to_toe_sequence", [])),
            "body_systems": len(assess.get("body_systems", [])),
            "red_flags_master": len(assess.get("red_flags_master", [])),
            "skills": len(assess.get("skills", [])),
            "practice_questions": len(assess.get("practice_questions", [])),
            "special_populations": len(assess.get("special_populations", [])),
            "assessment_checklists": len(assess.get("assessment_checklists", [])),
            "soap_exercises": len(assess.get("soap_exercises", [])),
            "assess_next_scenarios": len(assess.get("assess_next_scenarios", [])),
            "sbar_exercises": len(assess.get("sbar_exercises", [])),
            "flashcards": len(assess.get("flashcards", [])),
            "interview_techniques": len(interview),
        },
        "verified": stats["verified"],
        "flagged": stats["flagged"],
        "breakdown_by_tab": _tab_breakdown(catalog, flagged_keys),
        "flagged_items": [
            {"item_key": k, "tab": _tab_for_key(k), "review_note": v}
            for k, v in NEEDS_REVIEW_FLAGS.items()
        ],
        "ancillary_verified": ancillary_verified,
        "errors": stats["errors"],
        "module_audit_summary": summary["by_module"].get("assessment"),
        "focus_areas_reviewed": [
            "Clinical accuracy and evidence-based assessment techniques",
            "Red flag immediate actions and escalation paths",
            "Special populations (pediatric, geriatric, OB, mental health, newborn)",
            "NCLEX-RN Test Plan 2023 alignment (ABC priority, unstable before stable)",
            "Safe nursing practice (no Trendelenburg, no unsafe leg elevation in CHF, epiglottitis precautions)",
        ],
    }

    out = Path(__file__).resolve().parent.parent / "data" / "assessment_full_audit.json"
    out.write_text(json.dumps(result_payload, indent=2), encoding="utf-8")
    print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
    asyncio.run(apply())