"""Content audit catalog and status — preparation for correctness review phase."""
from __future__ import annotations

import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ContentAuditRecord
from app.services.assessment_service import get_module_summary as assessment_summary
from app.services.content_loader import load_content
from app.services.maternal_child_service import get_module_summary as maternal_child_summary
from app.services.terminology_service import get_all_terms

AUDIT_STATUSES = ("unreviewed", "verified", "needs_review")

MODULE_LABELS = {
    "terminology": "Medical Terminology",
    "microbiology": "Microbiology",
    "dosage": "NURS 145 — Dosage",
    "assessment": "NURS 146 — Health Assessment",
    "mental_health": "NURS 147 — Mental Health",
    "pathophysiology": "Pathophysiology",
    "maternal_child": "NURS 148 — Maternal-Child",
    "pharmacy_calculations": "Pharmacy Calculations",
}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _catalog_item(
    module_id: str,
    item_key: str,
    item_type: str,
    title: str,
    subtitle: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "module_id": module_id,
        "item_key": item_key,
        "item_type": item_type,
        "title": title,
        "subtitle": subtitle,
        "status": "unreviewed",
        "verified_date": None,
        "source_note": None,
        "review_note": None,
        "updated_at": None,
    }


def build_content_catalog() -> list[dict[str, Any]]:
    """Enumerate auditable concepts, calculations, and practice items from content JSON."""
    items: list[dict[str, Any]] = []

    # ── Terminology ───────────────────────────────────────────────────────────
    for term in get_all_terms():
        key = f"term:{_slug(term['term'])}"
        subtitle = (term.get("definition") or "")[:120]
        if len(term.get("definition", "")) > 120:
            subtitle += "…"
        items.append(_catalog_item("terminology", key, "concept", term["term"], subtitle))

    # ── Microbiology ──────────────────────────────────────────────────────────
    micro = load_content("microbiology.json")
    for p in micro.get("healthcare_pathogens", micro.get("pathogens", [])):
        name = p.get("name", "")
        items.append(_catalog_item(
            "microbiology",
            f"pathogen:{_slug(name)}",
            "concept",
            name,
            p.get("full_name") or p.get("type"),
        ))
    for concept in micro.get("concepts", []):
        cid = concept.get("id") or _slug(concept.get("title", concept.get("name", "concept")))
        items.append(_catalog_item(
            "microbiology",
            f"concept:{cid}",
            "concept",
            concept.get("title", concept.get("name", cid)),
            (concept.get("content") or concept.get("summary") or concept.get("description", ""))[:100] or None,
        ))
    for link in micro.get("infection_chain", []):
        lid = link.get("id") or _slug(link.get("name", "link"))
        items.append(_catalog_item(
            "microbiology",
            f"chain:{lid}",
            "concept",
            link.get("name", lid),
            link.get("description", "")[:100] or None,
        ))
    for q in micro.get("practice_questions", []) + micro.get("application_questions", []):
        qid = q.get("id", _slug(q.get("question", "q")[:40]))
        items.append(_catalog_item(
            "microbiology",
            f"practice:{qid}",
            "practice",
            (q.get("question", qid))[:80] + ("…" if len(q.get("question", "")) > 80 else ""),
            q.get("nclex_category"),
        ))
    for sc in micro.get("break_chain_scenarios", []) + micro.get("what_if_scenarios", []):
        sid = sc.get("id", _slug(sc.get("title", "scenario")[:40]))
        items.append(_catalog_item(
            "microbiology",
            f"scenario:{sid}",
            "scenario",
            sc.get("title", sid),
            sc.get("target_link") or "what-if",
        ))

    # ── Dosage ────────────────────────────────────────────────────────────────
    dosage = load_content("dosage.json")
    for calc in dosage.get("calc_types", []):
        items.append(_catalog_item(
            "dosage",
            f"calc:{calc['id']}",
            "calculation",
            calc.get("name", calc["id"]),
            calc.get("formula"),
        ))
    for trap in dosage.get("error_traps", []):
        tid = trap.get("id") or _slug(trap.get("title", "trap"))
        items.append(_catalog_item(
            "dosage",
            f"trap:{tid}",
            "concept",
            trap.get("title", tid),
            trap.get("trap"),
        ))
    for prob in dosage.get("practice_problems", []):
        pid = prob.get("id", _slug(prob.get("question", "p")[:40]))
        items.append(_catalog_item(
            "dosage",
            f"practice:{pid}",
            "practice",
            (prob.get("question", pid))[:80] + ("…" if len(prob.get("question", "")) > 80 else ""),
            prob.get("calc_type"),
        ))
    for safety in dosage.get("pharmacology_safety", []):
        sid = safety.get("id") or _slug(safety.get("title", "safety"))
        items.append(_catalog_item(
            "dosage",
            f"pharm-safety:{sid}",
            "concept",
            safety.get("title", sid),
            (safety.get("concept") or "")[:100] or None,
        ))
    for drug_class in dosage.get("drug_classes", []):
        dc_id = drug_class.get("id") or _slug(drug_class.get("name", "drug"))
        items.append(_catalog_item(
            "dosage",
            f"pharm:{dc_id}",
            "concept",
            drug_class.get("name", dc_id),
            drug_class.get("category_label") or drug_class.get("category"),
        ))

    # ── Mental Health ─────────────────────────────────────────────────────────
    mh = load_content("mental_health.json")
    for tech in mh.get("therapeutic_communication", []):
        tid = tech.get("id") or _slug(tech.get("technique", "tech"))
        items.append(_catalog_item(
            "mental_health",
            f"comm:{tid}",
            "concept",
            tech.get("technique", tid),
            (tech.get("description") or "")[:100] or None,
        ))
    for barrier in mh.get("communication_barriers", []):
        bid = barrier.get("id") or _slug(barrier.get("barrier", "barrier"))
        items.append(_catalog_item(
            "mental_health",
            f"barrier:{bid}",
            "concept",
            barrier.get("barrier", bid),
            (barrier.get("description") or "")[:100] or None,
        ))
    for flag in mh.get("safety_risk_flags", []):
        fid = flag.get("id") or _slug(flag.get("finding", "flag")[:50])
        items.append(_catalog_item(
            "mental_health",
            f"redflag:{fid}",
            "concept",
            (flag.get("finding", ""))[:80],
            flag.get("category"),
        ))
    for tool in mh.get("screening_tools", []):
        tool_id = tool.get("id") or _slug(tool.get("name", "tool"))
        items.append(_catalog_item(
            "mental_health",
            f"tool:{tool_id}",
            "concept",
            tool.get("name", tool_id),
            (tool.get("purpose") or "")[:100] or None,
        ))
    for q in mh.get("safety_drill", []):
        items.append(_catalog_item(
            "mental_health",
            f"drill:{q['id']}",
            "practice",
            (q.get("finding", q["id"]))[:80] + ("…" if len(q.get("finding", "")) > 80 else ""),
            q.get("category"),
        ))
    for sc in mh.get("communication_scenarios", []):
        items.append(_catalog_item(
            "mental_health",
            f"scenario:{sc['id']}",
            "scenario",
            sc.get("title", sc["id"]),
            sc.get("category"),
        ))
    for disorder in mh.get("disorders", []):
        did = disorder.get("id") or _slug(disorder.get("name", "disorder"))
        items.append(_catalog_item(
            "mental_health",
            f"disorder:{did}",
            "concept",
            disorder.get("name", did),
            disorder.get("category"),
        ))
    for item in mh.get("de_escalation", []):
        deid = item.get("id") or _slug(item.get("title", "deesc"))
        items.append(_catalog_item(
            "mental_health",
            f"deesc:{deid}",
            "scenario" if item.get("type") == "scenario" else "concept",
            item.get("title", deid),
            item.get("category") or item.get("type"),
        ))
    for q in mh.get("practice_questions", []):
        items.append(_catalog_item(
            "mental_health",
            f"practice:{q['id']}",
            "practice",
            (q.get("question", q["id"]))[:80] + ("…" if len(q.get("question", "")) > 80 else ""),
            q.get("nclex_category"),
        ))

    # ── Pathophysiology ───────────────────────────────────────────────────────
    patho = load_content("pathophysiology.json")
    for concept in patho.get("core_concepts", []):
        cid = concept.get("id") or _slug(concept.get("title", "concept"))
        items.append(_catalog_item(
            "pathophysiology",
            f"concept:{cid}",
            "concept",
            concept.get("title", cid),
            (concept.get("summary") or concept.get("content", ""))[:100] or None,
        ))
    for disease in patho.get("disease_processes", []):
        did = disease.get("id") or _slug(disease.get("name", "disease"))
        items.append(_catalog_item(
            "pathophysiology",
            f"disease:{did}",
            "concept",
            disease.get("name", did),
            disease.get("category"),
        ))
    for pair in patho.get("compare_contrast_pairs", []):
        pid = pair.get("id") or _slug(pair.get("title", "pair"))
        items.append(_catalog_item(
            "pathophysiology",
            f"compare:{pid}",
            "concept",
            pair.get("title", pid),
            "Compare & contrast",
        ))
    for sc in patho.get("what_breaks_down_scenarios", []):
        sid = sc.get("id", _slug(sc.get("title", "scenario")[:40]))
        items.append(_catalog_item(
            "pathophysiology",
            f"scenario:{sid}",
            "scenario",
            sc.get("title", sid),
            "What breaks down",
        ))
    for fc in patho.get("flashcards", []):
        items.append(_catalog_item(
            "pathophysiology",
            f"flashcard:{fc['id']}",
            "concept",
            (fc.get("front", fc["id"]))[:80] + ("…" if len(fc.get("front", "")) > 80 else ""),
            fc.get("category"),
        ))
    for q in patho.get("practice_questions", []):
        items.append(_catalog_item(
            "pathophysiology",
            f"practice:{q['id']}",
            "practice",
            (q.get("question", q["id"]))[:80] + ("…" if len(q.get("question", "")) > 80 else ""),
            q.get("nclex_category"),
        ))

    # ── Assessment ────────────────────────────────────────────────────────────
    assess = load_content("assessment.json")
    for step in assess.get("head_to_toe_sequence", []):
        items.append(_catalog_item(
            "assessment",
            f"sequence:{step.get('order', 0)}",
            "concept",
            step.get("step", f"Step {step.get('order')}"),
            step.get("description", "")[:100] or None,
        ))
    for sys in assess.get("body_systems", []):
        items.append(_catalog_item(
            "assessment",
            f"system:{sys['id']}",
            "concept",
            sys.get("name", sys["id"]),
            f"{len(sys.get('assessment_steps', []))} steps",
        ))
    for rf in assess.get("red_flags_master", []):
        rfid = _slug(rf.get("finding", "flag")[:50])
        items.append(_catalog_item(
            "assessment",
            f"redflag:{rfid}",
            "concept",
            (rf.get("finding", ""))[:80],
            rf.get("system"),
        ))
    for q in assess.get("practice_questions", []):
        items.append(_catalog_item(
            "assessment",
            f"practice:{q['id']}",
            "practice",
            (q.get("question", q["id"]))[:80] + ("…" if len(q.get("question", "")) > 80 else ""),
            q.get("system"),
        ))
    for ex in assess.get("soap_exercises", []):
        items.append(_catalog_item(
            "assessment",
            f"soap:{ex['id']}",
            "concept",
            ex.get("title", ex["id"]),
            "SOAP documentation",
        ))
    for sb in assess.get("sbar_exercises", []):
        items.append(_catalog_item(
            "assessment",
            f"sbar:{sb['id']}",
            "concept",
            sb.get("title", sb["id"]),
            "SBAR handoff",
        ))
    for sc in assess.get("assess_next_scenarios", []):
        items.append(_catalog_item(
            "assessment",
            f"scenario:{sc['id']}",
            "scenario",
            sc.get("title", sc["id"]),
            "Assess-next exercise",
        ))
    for cl in assess.get("assessment_checklists", []):
        items.append(_catalog_item(
            "assessment",
            f"checklist:{cl['id']}",
            "concept",
            cl.get("title", cl["id"]),
            f"{len(cl.get('items', []))} items",
        ))
    for pop in assess.get("special_populations", []):
        items.append(_catalog_item(
            "assessment",
            f"population:{pop['id']}",
            "concept",
            pop.get("name", pop["id"]),
            pop.get("age_range"),
        ))
    for sk in assess.get("skills", []):
        items.append(_catalog_item(
            "assessment",
            f"skill:{sk['id']}",
            "concept",
            sk.get("title", sk["id"]),
            "Assessment technique",
        ))
    for fc in assess.get("flashcards", []):
        items.append(_catalog_item(
            "assessment",
            f"flashcard:{fc['id']}",
            "concept",
            (fc.get("front", fc["id"]))[:80] + ("…" if len(fc.get("front", "")) > 80 else ""),
            fc.get("system_name", fc.get("system")),
        ))

    # ── Maternal-Child ────────────────────────────────────────────────────────
    mc = load_content("maternal_child.json")
    for section_key, item_type in (
        ("pregnancy_stages", "concept"),
        ("labor_delivery", "concept"),
        ("postpartum_newborn", "concept"),
        ("pediatric_essentials", "concept"),
    ):
        for topic in mc.get(section_key, []):
            tid = topic.get("id") or _slug(topic.get("title", "topic"))
            items.append(_catalog_item(
                "maternal_child",
                f"topic:{tid}",
                item_type,
                topic.get("title", tid),
                topic.get("category"),
            ))
    for flag in mc.get("safety_red_flags", []):
        fid = flag.get("id") or _slug(flag.get("finding", "flag")[:50])
        items.append(_catalog_item(
            "maternal_child",
            f"redflag:{fid}",
            "concept",
            (flag.get("finding", ""))[:80],
            flag.get("category"),
        ))
    for q in mc.get("complications_drill", []):
        items.append(_catalog_item(
            "maternal_child",
            f"drill:{q['id']}",
            "scenario",
            (q.get("finding", q["id"]))[:80] + ("…" if len(q.get("finding", "")) > 80 else ""),
            q.get("category"),
        ))
    for q in mc.get("practice_questions", []):
        items.append(_catalog_item(
            "maternal_child",
            f"practice:{q['id']}",
            "practice",
            (q.get("question", q["id"]))[:80] + ("…" if len(q.get("question", "")) > 80 else ""),
            q.get("nclex_category"),
        ))
    for fc in mc.get("flashcards", []):
        items.append(_catalog_item(
            "maternal_child",
            f"flashcard:{fc['id']}",
            "concept",
            (fc.get("front", fc["id"]))[:80] + ("…" if len(fc.get("front", "")) > 80 else ""),
            fc.get("category"),
        ))

    # ── Pharmacy Calculations ─────────────────────────────────────────────────
    pharm_calc = load_content("pharmacy_calculations.json")
    for calc in pharm_calc.get("calc_types", []):
        items.append(_catalog_item(
            "pharmacy_calculations",
            f"calc:{calc['id']}",
            "calculation",
            calc.get("name", calc["id"]),
            calc.get("formula") or calc.get("formula_hint"),
        ))
    for topic in pharm_calc.get("topic_outline", []):
        tid = topic.get("id") or _slug(topic.get("title", "topic"))
        items.append(_catalog_item(
            "pharmacy_calculations",
            f"topic:{tid}",
            "concept",
            topic.get("title", tid),
            topic.get("priority"),
        ))
    for trap in pharm_calc.get("error_traps", []):
        trap_id = trap.get("id") or _slug(trap.get("title", "trap"))
        items.append(_catalog_item(
            "pharmacy_calculations",
            f"trap:{trap_id}",
            "concept",
            trap.get("title", trap_id),
            trap.get("trap"),
        ))
    for prob in pharm_calc.get("practice_problems", []):
        pid = prob.get("id", _slug(prob.get("question", "p")[:40]))
        items.append(_catalog_item(
            "pharmacy_calculations",
            f"practice:{pid}",
            "practice",
            (prob.get("question", pid))[:80] + ("…" if len(prob.get("question", "")) > 80 else ""),
            prob.get("calc_type"),
        ))
    for sc in pharm_calc.get("clinical_scenarios", []):
        sid = sc.get("id") or _slug(sc.get("title", "scenario")[:40])
        items.append(_catalog_item(
            "pharmacy_calculations",
            f"scenario:{sid}",
            "scenario",
            sc.get("title", sid),
            sc.get("setting"),
        ))

    return items


def get_catalog_stats() -> dict[str, Any]:
    """Static catalog counts without DB."""
    catalog = build_content_catalog()
    by_module: dict[str, int] = {}
    for item in catalog:
        by_module[item["module_id"]] = by_module.get(item["module_id"], 0) + 1
    return {
        "total_catalog": len(catalog),
        "by_module": by_module,
        "modules": MODULE_LABELS,
        "assessment_summary": assessment_summary(),
        "maternal_child_summary": maternal_child_summary(),
    }


async def _load_audit_map(session: AsyncSession) -> dict[tuple[str, str], ContentAuditRecord]:
    result = await session.execute(select(ContentAuditRecord))
    records = result.scalars().all()
    return {(r.module_id, r.item_key): r for r in records}


def _merge_item(catalog_item: dict, record: Optional[ContentAuditRecord]) -> dict:
    merged = dict(catalog_item)
    if record:
        merged.update({
            "status": record.status,
            "verified_date": record.verified_date,
            "source_note": record.source_note,
            "review_note": record.review_note,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        })
    return merged


async def get_audit_items(
    session: AsyncSession,
    module_id: Optional[str] = None,
    status: Optional[str] = None,
    item_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Return catalog items merged with stored audit status."""
    catalog = build_content_catalog()
    audit_map = await _load_audit_map(session)

    merged = [_merge_item(item, audit_map.get((item["module_id"], item["item_key"]))) for item in catalog]

    if module_id:
        merged = [i for i in merged if i["module_id"] == module_id]
    if status and status in AUDIT_STATUSES:
        merged = [i for i in merged if i["status"] == status]
    if item_type:
        merged = [i for i in merged if i["item_type"] == item_type]
    if search:
        q = search.lower()
        merged = [
            i for i in merged
            if q in i["title"].lower()
            or q in (i.get("subtitle") or "").lower()
            or q in i["item_key"].lower()
        ]

    total = len(merged)
    page = merged[offset : offset + limit]
    return page, total


async def get_audit_summary(session: AsyncSession) -> dict[str, Any]:
    catalog = build_content_catalog()
    audit_map = await _load_audit_map(session)

    counts = {"verified": 0, "needs_review": 0, "unreviewed": 0}
    by_module: dict[str, dict[str, int]] = {
        mid: {"verified": 0, "needs_review": 0, "unreviewed": 0, "total": 0}
        for mid in MODULE_LABELS
    }

    for item in catalog:
        record = audit_map.get((item["module_id"], item["item_key"]))
        status = record.status if record else "unreviewed"
        counts[status] = counts.get(status, 0) + 1
        mod = by_module.setdefault(item["module_id"], {"verified": 0, "needs_review": 0, "unreviewed": 0, "total": 0})
        mod["total"] += 1
        mod[status] = mod.get(status, 0) + 1

    return {
        "total": len(catalog),
        **counts,
        "by_module": by_module,
        "modules": MODULE_LABELS,
    }


async def _get_or_create_record(
    session: AsyncSession,
    module_id: str,
    item_key: str,
    audit_map: dict[tuple[str, str], ContentAuditRecord],
    catalog_lookup: dict[tuple[str, str], dict],
) -> ContentAuditRecord:
    key = (module_id, item_key)
    if key in audit_map:
        return audit_map[key]

    catalog_item = catalog_lookup.get(key)
    if not catalog_item:
        raise ValueError(f"Unknown audit item: {module_id}/{item_key}")

    record = ContentAuditRecord(
        module_id=module_id,
        item_key=item_key,
        item_type=catalog_item["item_type"],
        title=catalog_item["title"],
        status="unreviewed",
    )
    session.add(record)
    await session.flush()
    audit_map[key] = record
    return record


def _catalog_lookup() -> dict[tuple[str, str], dict]:
    return {(i["module_id"], i["item_key"]): i for i in build_content_catalog()}


async def verify_item(
    session: AsyncSession,
    module_id: str,
    item_key: str,
    verified_date: Optional[str] = None,
    source_note: Optional[str] = None,
) -> dict:
    audit_map = await _load_audit_map(session)
    record = await _get_or_create_record(
        session, module_id, item_key, audit_map, _catalog_lookup()
    )
    record.status = "verified"
    record.verified_date = verified_date or "2026-06"
    record.source_note = source_note
    record.review_note = None
    await session.flush()
    await session.refresh(record)
    catalog_item = _catalog_lookup()[(module_id, item_key)]
    return _merge_item(catalog_item, record)


async def flag_item(
    session: AsyncSession,
    module_id: str,
    item_key: str,
    review_note: str,
) -> dict:
    audit_map = await _load_audit_map(session)
    record = await _get_or_create_record(
        session, module_id, item_key, audit_map, _catalog_lookup()
    )
    record.status = "needs_review"
    record.review_note = review_note
    await session.flush()
    await session.refresh(record)
    catalog_item = _catalog_lookup()[(module_id, item_key)]
    return _merge_item(catalog_item, record)


async def clear_item_audit(
    session: AsyncSession,
    module_id: str,
    item_key: str,
) -> dict:
    audit_map = await _load_audit_map(session)
    key = (module_id, item_key)
    catalog_item = _catalog_lookup().get(key)
    if not catalog_item:
        raise ValueError(f"Unknown audit item: {module_id}/{item_key}")

    record = audit_map.get(key)
    if record:
        await session.delete(record)
        await session.flush()

    return _merge_item(catalog_item, None)