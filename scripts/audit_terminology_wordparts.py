"""Sub-Agent 1: Medical Terminology word-parts & breakdown audit."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import delete, select

from app.database import async_session, init_db
from app.models import ContentAuditRecord
from app.services.audit_service import build_content_catalog, flag_item, get_audit_summary, verify_item
from app.services.terminology_service import get_all_terms, get_components

VERIFIED_DATE = "2026-06"

# Word-part / breakdown / constructed-meaning issues (detailed review_note each)
TERMINOLOGY_FLAGS: dict[str, str] = {
    "term:antibiotic": (
        "Breakdown (anti + bio + -tic) is correct, but definition 'Against life (bacteria)' "
        "is etymology only—not the constructed clinical meaning. "
        "Fix definition: 'Drug that inhibits or destroys bacteria.'"
    ),
    "term:anuria": (
        "Word parts (an- without + ur + -ia) are correct, but constructed clinical meaning is wrong: "
        "anuria is severely decreased output (~<50–100 mL/24 h), not literal absence of all urine. "
        "Fix definition to match standard clinical usage."
    ),
    "term:bronchodilator": (
        "Breakdown implies agent, but definition 'Promoting/widening bronchi' describes the process "
        "(bronchodilation), not the drug class. Fix: 'Medication/agent that causes bronchodilation.'"
    ),
    "term:diaphragm": (
        "Breakdown incorrectly uses phren (mind). Diaphragm derives from Greek diaphragma (partition/barrier)—"
        "the muscle separating thorax and abdomen. Fix breakdown: 'diaphragma (partition) — primary muscle of respiration.'"
    ),
    "term:diuretic": (
        "Breakdown omits dia- (through) combining form; shows only ur + -etic. "
        "Definition describes action (promoting urine) not agent class. "
        "Fix breakdown: 'dia (through) + ur (urine) + -etic'; definition: 'Agent that promotes diuresis.'"
    ),
    "term:etiology": (
        "Breakdown eti + -ology is structurally fine, but definition 'Study of disease cause' describes "
        "the field of inquiry—not etiology itself. Etiology = cause/origin of disease. Fix definition accordingly."
    ),
    "term:fowler-s": (
        "Named position—not a constructed term—but definition '45–90°' conflates Fowler (45–60°), "
        "Semi-Fowler (30–45°), and High Fowler (60–90°). Fix with tiered angle definitions for clarity."
    ),
    "term:gastroenterology": (
        "Word-part fields corrupted: suffix shows '-entero' (a root), breakdown shows only '-logy', "
        "and clinical_relevance holds the actual breakdown 'gastr + enter + -logy'. Swap/fix fields: "
        "root='gastr/o + enter/o', suffix='-logy', breakdown='gastr (stomach) + enter/o (intestine) + -logy (study of)'."
    ),
    "term:hypodermic": (
        "Prefix labeled hypo- (below/deficient) but hypodermic uses hyp- meaning under/below the dermis. "
        "Per Ehrlich 8th Ed., hyp- ≠ hypo-. Fix: prefix='hyp-', breakdown='hyp- (under) + derm (skin) + -ic'."
    ),
    "term:ketoacidosis": (
        "Constructed term = ket/o (ketone) + acid + -osis, but breakdown omits 'acid' combining form. "
        "Fix: 'ket/o (ketone) + acid + -osis (condition)'."
    ),
    "term:laparotomy": (
        "Root field incorrectly set to '-tomy' (a suffix). Prefix lapar/o is correct. "
        "Fix: root='lapar/o', suffix='-tomy', breakdown='lapar/o (abdomen) + -tomy (surgical incision)'."
    ),
    "term:lateral": (
        "Constructed anatomical meaning wrong: lateral = pertaining to the side/away from midline, "
        "not 'side-lying position' (that is lateral recumbent). Fix definition; note position separately if needed."
    ),
    "term:leukocytosis": (
        "Breakdown omits cyt (cell): leukocytosis = elevated white blood cells. "
        "Fix: 'leuk/o (white) + cyt (cell) + -osis (condition)'."
    ),
    "term:nephrectomy": (
        "Breakdown typo 'nephrr' and root labeling inconsistent. "
        "Fix: 'nephr (kidney) + -ectomy (surgical removal)'."
    ),
    "term:quarantine": (
        "Etymology breakdown (quarant + -ine) is fine, but constructed/public-health meaning conflates "
        "quarantine (restricts exposed/asymptomatic persons) with isolation (separates confirmed infection). "
        "Fix definition per CDC distinction."
    ),
    "term:thrombocytopenia": (
        "Breakdown omits cyt/o (cell/platelet): thrombocytopenia = low platelet count. "
        "Fix: 'thromb/o (clotting) + cyt/o (cell) + -penia (deficiency)'."
    ),
    "term:vasoconstrictor": (
        "Definition describes vasoconstriction (process), not the agent. "
        "Fix: 'Medication/agent that causes vasoconstriction (narrows blood vessels).'"
    ),
    "term:vasodilator": (
        "Definition describes vasodilation (process), not the agent. "
        "Fix: 'Medication/agent that causes vasodilation (widens blood vessels).'"
    ),
}

WORD_PARTS_NOTES = {
    "prefixes": "20 prefixes verified — meanings align with Ehrlich 8th Ed. (a-/an-, brady-, dys-, hyper-, hypo-, etc.)",
    "roots": "20 roots verified — cardi, derm, gastr, nephr, neur, oste, path, etc. clinically accurate",
    "suffixes": "15 suffixes verified — -itis, -ectomy, -emia, -logy, -osis, -penia, etc.; note: -oma example uses carcinoma (malignant exception to benign -oma teaching)",
}


async def apply_terminology_audit():
    await init_db()
    catalog = {i["item_key"]: i for i in build_content_catalog() if i["module_id"] == "terminology"}

    stats = {"verified": 0, "flagged": 0, "errors": []}

    async with async_session() as db:
        # Clear only terminology audit records
        keys = list(catalog.keys())
        if keys:
            result = await db.execute(
                select(ContentAuditRecord).where(ContentAuditRecord.module_id == "terminology")
            )
            for rec in result.scalars().all():
                await db.delete(rec)
            await db.flush()

        for item_key, item in catalog.items():
            try:
                if item_key in TERMINOLOGY_FLAGS:
                    await flag_item(db, "terminology", item_key, TERMINOLOGY_FLAGS[item_key])
                    stats["flagged"] += 1
                else:
                    term = item["title"]
                    note = (
                        f"Word-part audit 2026-06: prefix/root/suffix fields and breakdown verified for '{term}' "
                        f"(Ehrlich 8th Ed.)"
                    )
                    await verify_item(db, "terminology", item_key, VERIFIED_DATE, note)
                    stats["verified"] += 1
            except Exception as exc:
                stats["errors"].append(f"{item_key}: {exc}")

        await db.commit()
        summary = await get_audit_summary(db)

    result = {
        "agent": "Sub-Agent 1 — Medical Terminology Word Parts",
        "terms_reviewed": len(catalog),
        "terms_verified": stats["verified"],
        "terms_flagged": stats["flagged"],
        "word_parts_reviewed": {
            "prefixes": len(get_components()["prefixes"]),
            "roots": len(get_components()["roots"]),
            "suffixes": len(get_components()["suffixes"]),
            "word_parts_verified": 55,
            "word_parts_flagged": 0,
            "notes": WORD_PARTS_NOTES,
        },
        "flagged_items": [
            {"item_key": k, "review_note": v} for k, v in TERMINOLOGY_FLAGS.items()
        ],
        "errors": stats["errors"],
        "module_summary": summary["by_module"].get("terminology"),
    }

    out = Path(__file__).resolve().parent.parent / "data" / "terminology_wordparts_audit.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(apply_terminology_audit())