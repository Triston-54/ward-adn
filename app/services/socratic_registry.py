"""Central Socratic tutor registry — modules, tracks, intents, and topic categories."""
from __future__ import annotations

from typing import Any, Optional

from app.services.content_loader import load_content

VALID_INTENTS = (
    "explore",
    "explain_further",
    "explain_mechanism",
    "clinical_why",
    "professional_considerations",
)

TOPIC_CATEGORIES = (
    "general",
    "pathophysiology",
    "drug_mechanism",
    "assessment_finding",
    "calculation",
    "psychosocial",
    "compounding",
)

TRACKS = {
    "nursing": {
        "label": "Nursing Track",
        "learner": "ADN nursing student preparing for NCLEX",
        "exam_frame": "NCLEX-RN clinical judgment and patient safety",
        "professional_role": "nurse",
        "considerations_label": "nursing considerations",
    },
    "pharmacy": {
        "label": "Pharmacy Track",
        "learner": "certified pharmacy technician advancing toward PharmD and licensure",
        "exam_frame": "NAPLEX/MPJE competencies and verification workflows",
        "professional_role": "pharmacist",
        "considerations_label": "pharmacist considerations",
    },
}

# JSON content keys searched for Socratic context (per module schema)
MODULE_CONTENT_KEYS: dict[str, tuple[str, ...]] = {
    "pathophysiology": ("core_concepts", "disease_processes"),
    "maternal_child": (
        "pregnancy_stages",
        "labor_delivery",
        "postpartum_newborn",
        "pediatric_essentials",
        "safety_red_flags",
    ),
}

MODULE_PLACEHOLDERS: dict[str, str] = {
    "nursing": "Ask about pathophysiology, drug mechanisms, assessment findings, or calculations…",
    "pharmacy": "Ask about mechanisms, compounding math, verification workflows, or NAPLEX-style problems…",
    "pathophysiology": "Ask about disease cascades, compensatory mechanisms, or what breaks down first…",
    "maternal_child": "Ask about maternal assessment, fetal monitoring, newborn care, or OB red flags…",
}

SOCRATIC_MODULES: dict[str, dict[str, Any]] = {
    "terminology": {
        "track": "nursing",
        "label": "Medical Terminology",
        "hint": "medical word parts (prefixes, roots, suffixes) and clinical documentation",
        "default_topic": "general",
        "topic_bias": "general",
        "topics": ["general", "assessment_finding"],
    },
    "microbiology": {
        "track": "nursing",
        "label": "Microbiology",
        "hint": "pathogens, infection control, chain of infection, and immune response",
        "default_topic": "pathophysiology",
        "topic_bias": "pathophysiology",
        "topics": ["general", "pathophysiology", "assessment_finding"],
    },
    "dosage": {
        "track": "nursing",
        "label": "NURS 145 — Dosage",
        "hint": "safe medication calculations, dimensional analysis, and IV drip rates",
        "default_topic": "calculation",
        "topic_bias": "calculation",
        "topics": ["general", "calculation", "drug_mechanism"],
    },
    "assessment": {
        "track": "nursing",
        "label": "Health Assessment",
        "hint": "systematic health assessment, vital signs, and abnormal findings",
        "default_topic": "assessment_finding",
        "topic_bias": "assessment_finding",
        "topics": ["general", "assessment_finding", "pathophysiology"],
    },
    "mental_health": {
        "track": "nursing",
        "label": "Mental Health",
        "hint": "therapeutic communication, suicide risk screening, and behavioral health safety",
        "default_topic": "psychosocial",
        "topic_bias": "psychosocial",
        "topics": ["general", "psychosocial", "assessment_finding", "drug_mechanism"],
    },
    "pathophysiology": {
        "track": "nursing",
        "label": "Pathophysiology",
        "hint": "cellular injury, inflammation, fluid/electrolytes, disease cascades, and shock",
        "default_topic": "pathophysiology",
        "topic_bias": "pathophysiology",
        "topics": ["general", "pathophysiology", "assessment_finding", "drug_mechanism"],
        "content_file": "pathophysiology.json",
        "status": "active",
    },
    "maternal_child": {
        "track": "nursing",
        "label": "Maternal-Child Nursing",
        "hint": "pregnancy stages, labor and delivery, postpartum care, newborn assessment, and pediatric milestones",
        "default_topic": "assessment_finding",
        "topic_bias": "assessment_finding",
        "topics": ["general", "assessment_finding", "pathophysiology", "psychosocial"],
        "content_file": "maternal_child.json",
        "status": "stub",
    },
    "pharmacy": {
        "track": "pharmacy",
        "label": "Pharmacy Track",
        "hint": "PharmD sciences, calculations, therapeutics, and licensure preparation",
        "default_topic": "general",
        "topic_bias": "general",
        "topics": ["general", "drug_mechanism", "calculation", "compounding"],
    },
    "pharmacy_calculations": {
        "track": "pharmacy",
        "label": "Pharmacy Calculations",
        "hint": "pharmacist-depth calculations — alligation, isotonicity, mEq, compounding, and verification",
        "default_topic": "calculation",
        "topic_bias": "calculation",
        "topics": ["general", "calculation", "compounding", "drug_mechanism"],
    },
    "general": {
        "track": "nursing",
        "label": "General",
        "hint": "nursing fundamentals and patient safety",
        "default_topic": "general",
        "topic_bias": "general",
        "topics": ["general", "pathophysiology", "drug_mechanism", "assessment_finding", "calculation"],
    },
}


def resolve_module(module_id: str) -> dict[str, Any]:
    return SOCRATIC_MODULES.get(module_id, SOCRATIC_MODULES["general"])


def resolve_track(module_id: str) -> str:
    return resolve_module(module_id).get("track", "nursing")


def module_hint(module_id: str) -> str:
    return resolve_module(module_id).get("hint", SOCRATIC_MODULES["general"]["hint"])


# URL path prefixes → module_id (longest match wins on the client; same order here)
PATH_MODULE_MAP: dict[str, str] = {
    "/modules/terminology": "terminology",
    "/modules/microbiology": "microbiology",
    "/modules/dosage": "dosage",
    "/modules/assessment": "assessment",
    "/modules/mental-health": "mental_health",
    "/modules/pathophysiology": "pathophysiology",
    "/modules/maternal-child": "maternal_child",
    "/pharmacy/modules/calculations": "pharmacy_calculations",
    "/pharmacy": "pharmacy",
}


def detect_module_from_path(path: str) -> str:
    """Resolve module_id from a request path or page URL."""
    if not path:
        return "general"
    normalized = path.split("?")[0].rstrip("/") or "/"
    for prefix in sorted(PATH_MODULE_MAP, key=len, reverse=True):
        if normalized.startswith(prefix):
            return PATH_MODULE_MAP[prefix]
    return "general"


def module_placeholder(module_id: str) -> str:
    """Input placeholder tuned to module + track."""
    if module_id in MODULE_PLACEHOLDERS:
        return MODULE_PLACEHOLDERS[module_id]
    track_id = resolve_track(module_id)
    return MODULE_PLACEHOLDERS.get(track_id, MODULE_PLACEHOLDERS["nursing"])


def get_socratic_palette_commands(module_id: Optional[str] = None) -> list[dict[str, str]]:
    """Command-palette entries derived from registry (current + future modules)."""
    mid = module_id or "general"
    mod = resolve_module(mid)
    topic = mod.get("default_topic", "general")
    label = mod.get("label", "General")
    return [
        {
            "id": "socratic-open",
            "name": "Socratic Tutor",
            "section": "Socratic",
            "keywords": "ask ai explain help tutor socratic teaching partner preceptor guide",
        },
        {
            "id": "socratic-explore",
            "name": "Ask Guiding Questions",
            "section": "Socratic",
            "keywords": "socratic explore guide think first questions",
            "intent": "explore",
        },
        {
            "id": "socratic-mechanism",
            "name": "Explain the Mechanism",
            "section": "Socratic",
            "keywords": "mechanism drug pathophysiology how works moa socratic",
            "intent": "explain_mechanism",
        },
        {
            "id": "socratic-clinical",
            "name": "Why Clinically?",
            "section": "Socratic",
            "keywords": "clinical why bedside nursing safety nclex naplex socratic",
            "intent": "clinical_why",
        },
        {
            "id": "socratic-further",
            "name": "Explain Further",
            "section": "Socratic",
            "keywords": "deeper layer teach more socratic explain further",
            "intent": "explain_further",
        },
        {
            "id": "socratic-considerations",
            "name": "Professional Considerations",
            "section": "Socratic",
            "keywords": "nursing pharmacist considerations monitoring counseling safety socratic",
            "intent": "professional_considerations",
        },
        {
            "id": f"socratic-{mid}",
            "name": f"Socratic — {label}",
            "section": "Socratic",
            "keywords": f"socratic tutor {mid.replace('_', ' ')} {mod.get('hint', '')}",
            "module_id": mid,
            "topic": topic,
        },
    ]


def get_client_config(module_id: Optional[str] = None) -> dict[str, Any]:
    """Config payload for the front-end Socratic component."""
    mod = resolve_module(module_id or "general")
    track_id = mod.get("track", "nursing")
    track = TRACKS[track_id]
    mid = module_id or "general"
    return {
        "module_id": mid,
        "track": track_id,
        "track_label": track["label"],
        "module_label": mod.get("label", "General"),
        "default_topic": mod.get("default_topic", "general"),
        "topics": mod.get("topics", ["general"]),
        "considerations_label": track["considerations_label"],
        "intents": list(VALID_INTENTS),
        "explore_turns_before_teach": 2,
        "path_module_map": PATH_MODULE_MAP,
        "placeholder": module_placeholder(mid),
        "palette_commands": get_socratic_palette_commands(mid),
        "modules": {
            m_id: {
                "track": m["track"],
                "label": m["label"],
                "hint": m.get("hint", ""),
                "default_topic": m["default_topic"],
                "topics": m["topics"],
                "status": m.get("status", "active"),
                "placeholder": module_placeholder(m_id),
            }
            for m_id, m in SOCRATIC_MODULES.items()
            if m_id != "general"
        },
    }