"""Apply final terminology content fixes and mark audit items verified."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from app.database import async_session, init_db
from app.services.audit_service import get_audit_summary, verify_item
from app.services.terminology_service import get_all_terms

VERIFIED_DATE = "2026-06"
TERMS_PATH = Path(__file__).resolve().parent.parent / "data" / "content" / "terminology_terms.json"

# Field-level patches keyed by term (lowercase)
TERM_PATCHES: dict[str, dict] = {
    "antibiotic": {
        "definition": "Drug that inhibits or destroys bacteria",
    },
    "anuria": {
        "definition": "Critically low urine output (<50–100 mL in 24 hours)",
        "clinical_relevance": (
            "Medical emergency — assess for obstruction, hypovolemia, or renal failure. "
            "Do not wait for complete absence of urine; notify provider immediately."
        ),
    },
    "bronchodilator": {
        "definition": "Medication that causes bronchodilation",
    },
    "diaphragm": {
        "root": "diaphragm",
        "breakdown": "diaphragma (partition) — separates thorax and abdomen",
    },
    "diuretic": {
        "prefix": "dia-",
        "root": "ur",
        "suffix": "-etic",
        "breakdown": "dia + ur + -etic",
        "definition": "Medication that promotes diuresis (increased urine output)",
        "clinical_relevance": (
            "Loop diuretics (furosemide) and thiazides are common — monitor potassium, "
            "daily weights, and strict I&O. Report sudden weight gain or decreased output."
        ),
    },
    "etiology": {
        "definition": "Cause or origin of a disease",
    },
    "fowler's": {
        "definition": (
            "Head-of-bed elevation — Semi-Fowler 30–45°, Fowler 45–60°, High Fowler 60–90°"
        ),
        "clinical_relevance": (
            "High Fowler for dyspnea and aspiration risk during meals; Semi-Fowler for comfort "
            "and post-op. Elevate HOB before oral intake to reduce aspiration."
        ),
    },
    "gastroenterology": {
        "category": "specialty",
        "prefix": None,
        "root": "gastr",
        "suffix": "-entero + -logy",
        "breakdown": "gastr + enter + -logy",
        "clinical_relevance": (
            "GI nursing: bowel prep before endoscopy, post-procedure flatus return, "
            "NPO status, tube feeding tolerance, and nutrition assessment."
        ),
    },
    "hypodermic": {
        "prefix": "hyp-",
        "breakdown": "hyp + derm + -ic",
    },
    "ketoacidosis": {
        "root": "keto + acid",
        "breakdown": "keto + acid + -osis",
    },
    "laparotomy": {
        "prefix": None,
        "root": "lapar/o",
        "suffix": "-tomy",
        "breakdown": "lapar/o + -tomy",
    },
    "lateral": {
        "definition": "Pertaining to the side (anatomical position)",
        "clinical_relevance": (
            "Lateral recumbent (side-lying) recovery position prevents airway obstruction; "
            "distinct from anatomical lateral meaning 'toward the side of the body.'"
        ),
    },
    "leukocytosis": {
        "breakdown": "leuk + cyt + -osis",
    },
    "nephrectomy": {
        "breakdown": "nephr + -ectomy",
    },
    "thrombocytopenia": {
        "breakdown": "thromb/o + cyt/o + -penia",
    },
    "vasoconstrictor": {
        "definition": "Medication or agent that causes vasoconstriction",
    },
    "vasodilator": {
        "definition": "Medication or agent that causes vasodilation",
    },
    "carcinoma": {
        "clinical_relevance": (
            "Malignant tumor of epithelial origin — common types include breast, lung, and colon. "
            "Nurses monitor treatment side effects (chemo neutropenia, radiation skin care) and patient education."
        ),
    },
    "sign": {
        "clinical_relevance": (
            "Signs are objective, observable, or measurable findings (e.g., fever 38.9°C on thermometer, rash, BP). "
            "Symptoms are subjective patient reports (e.g., 'I feel feverish')."
        ),
    },
    "contraindication": {
        "clinical_relevance": (
            "Always verify before administering: morphine contraindicated with respiratory depression; "
            "metformin held before iodinated contrast; beta-blockers cautioned in severe asthma."
        ),
    },
    "carotid": {
        "clinical_relevance": (
            "Palpate one carotid at a time (never both simultaneously). Auscultate for bruit — "
            "stenosis increases stroke/TIA risk. Post–carotid endarterectomy: monitor neuro status, "
            "bleeding at incision, and blood pressure extremes."
        ),
    },
}

VERIFY_NOTES: dict[str, str] = {
    "term:antibiotic": "Polish 2026-06: Definition updated to drug-class (not etymology).",
    "term:anuria": "Polish 2026-06: Clinical threshold <50–100 mL/24h; not complete absence.",
    "term:bronchodilator": "Polish 2026-06: Agent-class definition.",
    "term:diaphragm": "Polish 2026-06: Etymology corrected — diaphragma partition, not phren (mind).",
    "term:diuretic": "Polish 2026-06: Added dia- prefix, agent definition, loop/thiazide nursing monitoring.",
    "term:etiology": "Polish 2026-06: Definition = cause/origin, not study of causes.",
    "term:fowler-s": "Polish 2026-06: Tiered angle ranges; aspiration and dyspnea nursing application.",
    "term:gastroenterology": "Polish 2026-06: Fixed swapped word-part fields; GI nursing clinical_relevance.",
    "term:hypodermic": "Polish 2026-06: Prefix hyp- per Ehrlich.",
    "term:ketoacidosis": "Polish 2026-06: Breakdown includes acid combining form.",
    "term:laparotomy": "Polish 2026-06: Root lapar/o, suffix -tomy corrected.",
    "term:lateral": "Polish 2026-06: Anatomical definition vs side-lying position clarified.",
    "term:leukocytosis": "Polish 2026-06: Breakdown includes cyt (cell).",
    "term:nephrectomy": "Polish 2026-06: Typo nephrr fixed.",
    "term:thrombocytopenia": "Polish 2026-06: Breakdown includes cyt/o.",
    "term:vasoconstrictor": "Polish 2026-06: Agent-class definition.",
    "term:vasodilator": "Polish 2026-06: Agent-class definition.",
    "term:carcinoma": "Polish 2026-06: Epithelial origin and nursing monitoring — not 'most common overall.'",
    "term:sign": "Polish 2026-06: Objective vs subjective distinction clarified.",
    "term:contraindication": "Polish 2026-06: Concrete nursing examples added.",
    "term:carotid": "Polish 2026-06: Palpation, stroke risk, auscultation, post-op monitoring.",
    "term:hypotension": "Polish 2026-06: SBP <90, orthostatic criteria, supine positioning — verified.",
    "term:quarantine": "Polish 2026-06: Quarantine vs isolation distinction — verified.",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def apply_term_patches() -> int:
    data = json.loads(TERMS_PATH.read_text(encoding="utf-8"))
    terms = data.get("terms", [])
    lookup = {t["term"].lower(): t for t in terms}
    patched = 0

    for key, fields in TERM_PATCHES.items():
        term = lookup.get(key)
        if not term:
            print(f"WARN: term not found: {key}")
            continue
        for field, value in fields.items():
            term[field] = value
        term.setdefault("source", {})["verified_date"] = VERIFIED_DATE
        patched += 1

    TERMS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return patched


async def verify_audit_items() -> dict:
    await init_db()
    results = {"verified": [], "errors": []}

    async with async_session() as db:
        for item_key, note in VERIFY_NOTES.items():
            try:
                await verify_item(db, "terminology", item_key, VERIFIED_DATE, note)
                results["verified"].append(item_key)
            except Exception as exc:
                results["errors"].append(f"{item_key}: {exc}")
        await db.commit()
        results["summary"] = await get_audit_summary(db)

    return results


async def main():
    patched = apply_term_patches()
    audit = await verify_audit_items()
    out = {
        "terms_patched": patched,
        "audit_verified": len(audit["verified"]),
        "audit_errors": audit["errors"],
        "terminology_summary": audit["summary"]["by_module"].get("terminology"),
        "total_summary": audit["summary"],
    }
    out_path = Path(__file__).resolve().parent.parent / "data" / "polish_terminology_applied.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    asyncio.run(main())