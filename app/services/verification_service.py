"""Central source verification registry — citations from verified content."""
from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content

REFERENCE_TYPE_STYLES: dict[str, str] = {
    "Textbook": "textbook",
    "OER Textbook": "oer",
    "Exam Blueprint": "nclex",
    "Clinical Guideline": "guideline",
    "Program Curriculum": "curriculum",
}

MODULE_SOURCE_KEYS: dict[str, list[str]] = {
    "terminology": ["terminology", "nclex", "new_river_ctc"],
    "microbiology": ["microbiology", "cdc_infection", "nclex"],
    "dosage": ["dosage", "nclex", "new_river_ctc"],
    "assessment": ["assessment", "nclex", "new_river_ctc"],
    "mental_health": ["mental_health", "nclex", "new_river_ctc"],
    "maternal_child": ["maternal_child", "nclex", "new_river_ctc"],
    "pharmacy": ["pharmacy", "nclex"],
    "pharmacy_calculations": ["pharmacy", "dosage"],
    "pathophysiology": ["assessment", "nclex", "new_river_ctc"],
    "maternal_child": ["assessment", "nclex", "new_river_ctc"],
    "general": ["nclex", "new_river_ctc"],
}

MODULE_VERIFY_CONTEXT: dict[str, dict[str, str]] = {
    "terminology": {
        "summary": "Terms are built from verified prefix/root/suffix components with clinical relevance notes.",
        "why_verify": "Accurate terminology prevents medication and documentation errors at the bedside.",
        "primary_type": "Textbook",
    },
    "microbiology": {
        "summary": "Pathogen profiles, chain of infection, and interventions sourced from Open RN OER and CDC guidelines.",
        "why_verify": "Infection control content must match current isolation and hand-hygiene standards.",
        "primary_type": "OER Textbook",
    },
    "dosage": {
        "summary": "Calculation formulas, error traps, and pharmacology safety align with Ogden & Fluharty and NCLEX competencies.",
        "why_verify": "Dosage errors are a leading cause of preventable harm — formulas are cross-checked against the standard text.",
        "primary_type": "Textbook",
    },
    "assessment": {
        "summary": "Head-to-toe sequence, system findings, and red flags from Open RN Nursing Skills and NCLEX test plan.",
        "why_verify": "Assessment findings drive clinical judgment — normal vs abnormal must match evidence-based references.",
        "primary_type": "OER Textbook",
    },
    "mental_health": {
        "summary": "Therapeutic communication, suicide screening, and behavioral health safety from Open RN OER and NCSBN Psychosocial Integrity.",
        "why_verify": "Mental health nursing content must reflect current suicide screening standards and trauma-informed practice.",
        "primary_type": "OER Textbook",
    },
    "maternal_child": {
        "summary": "Antepartum through pediatric content from Open RN Maternal-Newborn OER and NCLEX Health Promotion & Physiological Integrity.",
        "why_verify": "OB and pediatric nursing requires evidence-based FHR interpretation, hemorrhage protocols, and age-specific assessment standards.",
        "primary_type": "OER Textbook",
    },
    "pharmacy": {
        "summary": "Pharmacy Track content aligned with ACPE standards, Remington, and NABP NAPLEX/MPJE competency statements.",
        "why_verify": "Pharmacist-level calculations and clinical judgment require traceable pharmacy references.",
        "primary_type": "Curriculum Framework",
    },
    "pharmacy_calculations": {
        "summary": "Pharmacist-depth calculations — alligation, isotonicity, mEq — cross-checked against Remington and NAPLEX competencies.",
        "why_verify": "Compounding and verification math errors are high-risk — formulas must match standard pharmacy references.",
        "primary_type": "Textbook",
    },
    "pathophysiology": {
        "summary": "Disease processes and clinical manifestations aligned with Open RN and NCLEX Physiological Integrity.",
        "why_verify": "Pathophysiology teaching must connect cellular disruption to bedside assessment and priority actions.",
        "primary_type": "OER Textbook",
    },
    "maternal_child": {
        "summary": "Maternal-newborn and pediatric content aligned with Open RN OER and NCLEX Safe and Effective Care.",
        "why_verify": "Maternal-child safety content must reflect current assessment standards and escalation criteria.",
        "primary_type": "OER Textbook",
    },
    "general": {
        "summary": "All Ward content is verified against nursing education standards and program outcomes.",
        "why_verify": "Teaching-first content requires traceable, peer-reviewed sources.",
        "primary_type": "Exam Blueprint",
    },
}

NCLEX_RELEVANCE: dict[str, str] = {
    "terminology": (
        "Medical terminology supports NCLEX categories including Safe and Effective Care "
        "Environment and Health Promotion — accurate term use is tested in clinical "
        "reasoning and documentation items."
    ),
    "microbiology": (
        "Infection control and asepsis align with NCLEX Patient Safety and Infection "
        "Control subcategories — chain of infection and standard precautions appear "
        "frequently in prioritization questions."
    ),
    "dosage": (
        "Dosage calculation is a high-stakes NCLEX competency — dimensional analysis, "
        "IV rates, and pediatric weight-based dosing are commonly tested with "
        "patient-safety distractors."
    ),
    "assessment": (
        "Health assessment maps to NCLEX Physiological Integrity — systematic data "
        "collection, abnormal findings, and clinical judgment are core test plan areas."
    ),
    "mental_health": (
        "Mental health nursing aligns with NCLEX Psychosocial Integrity — therapeutic "
        "communication, crisis intervention, suicide risk, and safe behavioral health "
        "practice are high-frequency test areas."
    ),
    "maternal_child": (
        "Maternal-child nursing aligns with NCLEX Health Promotion and Physiological "
        "Integrity — prenatal education, labor stages, FHR patterns, postpartum "
        "hemorrhage, newborn assessment, and pediatric milestones are high-frequency areas."
    ),
    "general": (
        "All Ward modules align with the NCLEX-RN Test Plan (NCSBN) — content is "
        "verified against peer-reviewed nursing references and program outcomes."
    ),
    "nclex": (
        "Primary reference for NCLEX category alignment across all Ward study modules."
    ),
    "cdc_infection": (
        "CDC guidelines underpin NCLEX infection control and isolation precaution items."
    ),
    "new_river_ctc": (
        "Curriculum outcomes for New River CTC ADN program — local competency alignment."
    ),
}


def _load_registry() -> dict[str, Any]:
    return load_content("sources.json")


def format_citation(source: dict[str, Any]) -> str:
    citation = source.get("citation", "").strip()
    title = source.get("title", "").strip()
    verified = source.get("verified_date", "2026-06")
    if citation:
        return f"{citation} (verified {verified})"
    if title:
        return f"{title} (verified {verified})"
    return f"Verified source ({verified})"


def _enrich_source(source_key: str, raw: dict[str, Any]) -> dict[str, Any]:
    ref_type = raw.get("reference_type", "Reference")
    return {
        "id": source_key,
        "title": raw.get("title", "Unknown"),
        "url": raw.get("url"),
        "citation": raw.get("citation", ""),
        "verified_date": raw.get("verified_date", "2026-06"),
        "reference_type": ref_type,
        "reference_type_style": REFERENCE_TYPE_STYLES.get(ref_type, "reference"),
        "rationale": raw.get("rationale", ""),
        "formatted_citation": format_citation(raw),
        "nclex_relevance": NCLEX_RELEVANCE.get(
            source_key,
            NCLEX_RELEVANCE.get("general", ""),
        ),
    }


def get_all_sources() -> dict[str, Any]:
    registry = _load_registry()
    sources = [_enrich_source(key, entry) for key, entry in registry.items()]
    return {
        "sources": sources,
        "count": len(sources),
        "module_map": MODULE_SOURCE_KEYS,
        "reference_types": list(REFERENCE_TYPE_STYLES.keys()),
    }


def get_module_sources(module_id: str) -> dict[str, Any]:
    registry = _load_registry()
    keys = MODULE_SOURCE_KEYS.get(module_id, MODULE_SOURCE_KEYS["general"])
    sources = []
    for key in keys:
        if key in registry:
            sources.append(_enrich_source(key, registry[key]))
    ctx = MODULE_VERIFY_CONTEXT.get(module_id, MODULE_VERIFY_CONTEXT["general"])
    return {
        "module_id": module_id,
        "sources": sources,
        "nclex_relevance": NCLEX_RELEVANCE.get(
            module_id,
            NCLEX_RELEVANCE["general"],
        ),
        "verify_context": ctx,
        "count": len(sources),
    }


def sources_for_module(module_id: str) -> list[SourceRef]:
    data = get_module_sources(module_id)
    return [
        SourceRef(
            title=s["title"],
            url=s.get("url"),
            citation=s.get("citation", s.get("formatted_citation", "")),
            verified_date=s.get("verified_date", "2026-06"),
        )
        for s in data["sources"]
    ]


def lookup_source(source_id: str) -> Optional[dict[str, Any]]:
    registry = _load_registry()
    if source_id not in registry:
        return None
    return _enrich_source(source_id, registry[source_id])


def enrich_inline_source(source: dict[str, Any], module_id: str = "general") -> dict[str, Any]:
    """Enrich a partial source object passed from module JS (e.g. term.source)."""
    enriched = {
        "title": source.get("title", "Unknown"),
        "url": source.get("url"),
        "citation": source.get("citation", ""),
        "verified_date": source.get("verified_date", "2026-06"),
        "reference_type": source.get("reference_type", "Module Content"),
        "reference_type_style": REFERENCE_TYPE_STYLES.get(
            source.get("reference_type", ""), "reference"
        ),
        "rationale": source.get(
            "rationale",
            MODULE_VERIFY_CONTEXT.get(module_id, {}).get("why_verify", ""),
        ),
        "formatted_citation": format_citation(source),
        "nclex_relevance": NCLEX_RELEVANCE.get(
            module_id,
            NCLEX_RELEVANCE["general"],
        ),
    }
    return enriched