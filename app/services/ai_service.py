"""AI layer — Socratic tutor with Ollama integration and rich placeholder fallback."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.config import settings
from app.models import SocraticRequest, SocraticResponse, SourceRef
from app.services.content_loader import load_content
from app.services.socratic_registry import (
    MODULE_CONTENT_KEYS,
    SOCRATIC_MODULES,
    TRACKS,
    VALID_INTENTS,
    resolve_module,
    resolve_track,
    module_hint,
)

TEACHING_INTENTS = tuple(i for i in VALID_INTENTS if i != "explore")
from app.services.verification_service import sources_for_module

EXPLORE_TURNS_BEFORE_TEACH = 2

logger = logging.getLogger(__name__)

TOPIC_CATEGORIES = (
    "general",
    "pathophysiology",
    "drug_mechanism",
    "assessment_finding",
    "calculation",
    "psychosocial",
    "compounding",
)

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "pathophysiology": [
        "patho", "pathophys", "disease", "etiology", "manifestation", "why does",
        "mechanism of disease", "cellular", "inflammation", "immune response",
        "infection spread", "transmission", "virulence", "compensatory",
        "ischemia", "hypoxia", "heart failure", "copd", "diabetes", "preeclampsia",
    ],
    "drug_mechanism": [
        "drug", "medication", "pharmacology", "receptor", "mechanism of action",
        "therapeutic", "adverse", "side effect", "contraindication", "antibiotic",
        "analgesic", "antihypertensive", "insulin", "heparin", "opioid",
    ],
    "assessment_finding": [
        "assessment", "finding", "vital", "symptom", "sign", "abnormal", "inspect",
        "palpate", "auscult", "percuss", "lung sound", "heart sound", "edema",
        "cyanosis", "pulse", "blood pressure", "red flag", "head to toe",
        "fetal", "newborn", "apgar", "fundus", "lochia", "postpartum", "labor",
        "contractions", "pediatric", "growth", "developmental",
    ],
    "calculation": [
        "calculate", "dosage", "dose", "mg", "ml", "mcg", "tablet", "drip",
        "gtt", "infusion", "weight-based", "dimensional", "ratio",
        "alligation", "isotonic", "meq", "osmolarity", "naplex",
    ],
    "psychosocial": [
        "therapeutic", "communication", "suicide", "psychosocial", "mental health",
        "depression", "anxiety", "trauma", "crisis", "boundary",
    ],
    "compounding": [
        "compound", "alligation", "isotonic", "percentage strength", "w/w", "w/v",
        "qs", "stock solution", "beyond-use", "admixture",
    ],
}

DOMAIN_SOCRATIC_RULES: dict[str, str] = {
    "pathophysiology": (
        "PATHOPHYSIOLOGY MODE: Do NOT explain the disease process directly on the first turn. "
        "Ask what the student knows about normal anatomy/physiology first. "
        "Guide them to connect agent/stressor → cellular or organ disruption → compensatory response → clinical signs. "
        "Use 'what would you expect to see if…' and 'what breaks down when…' questions. "
        "On teach turns, link manifestations to priority nursing assessments and escalation."
    ),
    "drug_mechanism": (
        "DRUG MECHANISM MODE: Do NOT name the drug class action immediately. "
        "Ask what the patient problem is and what the desired therapeutic outcome would be. "
        "Guide toward receptor/target, onset, and nursing implications (monitoring, teaching). "
        "Always connect mechanism to a safety consideration."
    ),
    "assessment_finding": (
        "ASSESSMENT FINDING MODE: Do NOT list the finding's meaning outright. "
        "Ask whether the data is subjective or objective. "
        "Guide through IPPA sequence and 'what would you assess next?' "
        "Connect abnormal findings to priority nursing actions and escalation criteria."
    ),
    "calculation": (
        "CALCULATION MODE: Do NOT give the numeric answer first. "
        "Ask the student to identify Desired, Have, and units before setting up the equation. "
        "Guide dimensional analysis step-by-step. "
        "End with a patient-safety check question."
    ),
    "general": (
        "GENERAL MODE: Use classic Socratic questioning — build on prior knowledge, "
        "challenge assumptions gently, and tie every concept to patient safety."
    ),
    "psychosocial": (
        "PSYCHOSOCIAL MODE: Do NOT lecture on disorders immediately. "
        "Ask about therapeutic responses, safety screening, and patient rapport first. "
        "Guide toward priority nursing actions and least-restrictive interventions."
    ),
    "compounding": (
        "COMPOUNDING MODE: Do NOT give the final quantity or strength first. "
        "Ask the student to identify given strengths, desired strength, and method "
        "(alligation, dilution, or QS). Guide verification and beyond-use dating reasoning."
    ),
}

FOLLOW_UP_MARKER = "FOLLOW_UP_QUESTIONS:"

INTENT_RULES: dict[str, str] = {
    "explore": (
        "EXPLORE INTENT: Ask 2-3 guiding questions before revealing answers. "
        "Build on what the student already knows. Do not lecture."
    ),
    "explain_further": (
        "EXPLAIN FURTHER INTENT: The student wants deeper teaching on the current topic. "
        "Briefly acknowledge their question, add one layer of detail with a clinical example, "
        "then ask what still feels unclear. Still Socratic — do not dump an entire textbook section."
    ),
    "explain_mechanism": (
        "EXPLAIN MECHANISM INTENT: The student wants the mechanism explained. "
        "Start with ONE guiding question about the target or process, then teach "
        "target → effect → monitoring in concise layers. Connect mechanism to safety."
    ),
    "clinical_why": (
        "CLINICAL WHY INTENT: Connect this concept to real clinical practice. "
        "Explain patient safety implications, what you'd monitor, and exam relevance (NCLEX or NAPLEX). "
        "Start with one guiding question about real-world application, then teach the 'why.'"
    ),
    "professional_considerations": (
        "PROFESSIONAL CONSIDERATIONS INTENT: Focus on role-specific practice — "
        "monitoring, counseling, documentation, verification, and escalation. "
        "Use nursing or pharmacist framing based on track. End with a prioritization question."
    ),
}

def _content_item_text(item: dict) -> tuple[str, str]:
    """Extract (title, body) from a module content record."""
    title = (
        item.get("title")
        or item.get("name")
        or item.get("condition")
        or item.get("finding")
        or ""
    )
    body = (
        item.get("summary")
        or item.get("content")
        or item.get("manifestations")
        or item.get("description")
        or item.get("clinical_why")
        or item.get("nursing_action")
        or item.get("nursing_focus")
        or ""
    )
    if not body and item.get("key_points"):
        body = "; ".join(str(p) for p in item["key_points"][:3])
    return title, body


def _iter_module_records(module_id: str, data: dict) -> list[dict]:
    """Walk module JSON using registry content keys or generic fallbacks."""
    records: list[dict] = []
    keys = MODULE_CONTENT_KEYS.get(
        module_id,
        ("topics", "conditions", "concepts", "systems", "chapters"),
    )
    for key in keys:
        for item in data.get(key, []):
            if isinstance(item, dict):
                records.append(item)
    return records


MODULE_STARTER_QUESTIONS: dict[str, list[str]] = {
    "terminology": [
        "How would you break this term into word parts?",
        "What could go wrong if you misread this prefix in a chart?",
        "Where would you see this term at the bedside?",
    ],
    "microbiology": [
        "Which chain-of-infection link is easiest for nurses to break?",
        "What precautions would you expect for this pathogen?",
        "How does this organism cause harm in the body?",
    ],
    "dosage": [
        "What are Desired and Have in this problem?",
        "What units need to convert before you calculate?",
        "What safety check prevents a medication error here?",
    ],
    "assessment": [
        "Is this finding subjective or objective?",
        "What would you assess next, and why?",
        "When would you escalate this finding to the provider?",
    ],
    "mental_health": [
        "What therapeutic response would build trust here?",
        "What safety screening questions should you ask next?",
        "What is the priority nursing action for this risk level?",
    ],
    "pharmacy_calculations": [
        "What method applies — alligation, dilution, or dimensional analysis?",
        "How would you verify this result independently?",
        "What patient-safety check prevents a compounding error here?",
    ],
    "pharmacy": [
        "What NAPLEX competency area does this fall under?",
        "What would a pharmacist verify before dispensing?",
        "How does this connect to your technician foundation?",
    ],
    "pathophysiology": [
        "What is normal function before this disease process begins?",
        "What compensatory mechanisms might the body use?",
        "Which assessment findings would confirm your hypothesis?",
    ],
    "maternal_child": [
        "What is the priority assessment for this maternal or newborn finding?",
        "What red-flag symptoms would make you escalate immediately?",
        "How does this connect to patient teaching and safety?",
    ],
    "general": [
        "What do you already know about this topic?",
        "How would this show up in a clinical scenario?",
        "What NCLEX priority framework applies here?",
    ],
}


def detect_topic_category(question: str, module_id: str, override: Optional[str] = None) -> str:
    if override and override in TOPIC_CATEGORIES:
        return override
    q = question.lower()
    scores = {cat: 0 for cat in TOPIC_CATEGORIES}
    for cat, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in q:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        bias = resolve_module(module_id).get("topic_bias")
        if bias in TOPIC_CATEGORIES:
            return bias
        return "general"
    return best


_SEARCH_STOP_WORDS = frozenset({
    "the", "and", "for", "what", "how", "why", "does", "this", "that", "with",
    "from", "about", "when", "where", "would", "could", "should", "have", "your",
    "are", "was", "were", "been", "being", "into", "than", "then", "them", "they",
})


@dataclass
class OllamaResult:
    content: Optional[str] = None
    error: Optional[str] = None  # timeout | unavailable | http_error | empty_response


def _parse_context_history(context: Optional[str]) -> list[dict[str, Any]]:
    if not context:
        return []
    try:
        history = json.loads(context)
        if isinstance(history, list):
            return [t for t in history if isinstance(t, dict)]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def _count_assistant_turns(context: Optional[str]) -> int:
    return sum(1 for t in _parse_context_history(context) if t.get("role") == "assistant")


def _last_user_turns(context: Optional[str], limit: int = 2) -> list[str]:
    turns = [
        str(t.get("content", "")).strip()
        for t in _parse_context_history(context)
        if t.get("role") == "user" and t.get("content")
    ]
    return turns[-limit:]


def _conversation_acknowledgment(context: Optional[str]) -> str:
    """Reference prior student thinking for multi-turn placeholder/Ollama fallback."""
    prior = _last_user_turns(context, 1)
    if not prior:
        return ""
    excerpt = prior[-1]
    if len(excerpt) > 140:
        excerpt = excerpt[:137] + "…"
    return (
        f"You shared: \"{excerpt}\" — let's build on that.\n\n"
    )


def _search_terms(question: str) -> list[str]:
    terms = re.findall(r"[a-z0-9]{3,}", question.lower())
    return [t for t in terms if t not in _SEARCH_STOP_WORDS]


def _score_text(text: str, terms: list[str]) -> int:
    hay = text.lower()
    return sum(1 for term in terms if term in hay)


def _rank_snippets(candidates: list[tuple[int, str]], limit: int = 4) -> list[str]:
    seen: set[str] = set()
    ranked: list[str] = []
    for score, snippet in sorted(candidates, key=lambda x: (-x[0], x[1])):
        key = snippet[:80].lower()
        if score <= 0 or key in seen:
            continue
        seen.add(key)
        ranked.append(snippet)
        if len(ranked) >= limit:
            break
    return ranked


def _search_module_content(
    module_id: str, question: str, topic_category: str
) -> list[str]:
    """Pull question-relevant lines from module JSON when available."""
    terms = _search_terms(question)
    if not terms:
        return []
    candidates: list[tuple[int, str]] = []

    def add(text: str, base: int = 0) -> None:
        if not text or len(text) < 12:
            return
        score = _score_text(text, terms) + base
        if score > 0:
            candidates.append((score, text[:220]))

    if module_id == "terminology":
        data = load_content("terminology.json")
        for p in data.get("prefixes", []):
            add(f"Prefix {p.get('element', '')}: {p.get('meaning', '')}")
        for r in data.get("roots", []):
            add(f"Root {r.get('element', '')}: {r.get('meaning', '')}")
        for t in load_content("terminology_terms.json").get("terms", []):
            add(f"{t.get('term')}: {t.get('definition', '')}")

    elif module_id == "microbiology":
        data = load_content("microbiology.json")
        for link in data.get("infection_chain", []):
            add(f"{link.get('name', '')}: {link.get('description', '')}")
        for p in data.get("healthcare_pathogens", []):
            add(
                f"{p.get('name', '')}: {p.get('clinical_why', p.get('transmission', ''))}",
                base=1 if topic_category == "pathophysiology" else 0,
            )
        for c in data.get("concepts", []):
            add(f"{c.get('title', '')}: {c.get('content', '')}")

    elif module_id == "dosage":
        data = load_content("dosage.json")
        for rule in data.get("pharmacology_safety", []):
            if isinstance(rule, dict):
                add(f"{rule.get('title', '')}: {rule.get('concept', '')}")
        for dc in data.get("drug_classes", []):
            add(
                f"{dc.get('name', '')}: {dc.get('mechanism', '')}",
                base=1 if topic_category == "drug_mechanism" else 0,
            )
        fp = data.get("first_principles", {})
        for ct in data.get("calc_types", []):
            cid = ct.get("id", "")
            if cid in fp:
                add(f"{ct.get('name', '')}: {fp[cid].get('core_idea', '')}")

    elif module_id == "assessment":
        data = load_content("assessment.json")
        for flag in data.get("red_flags_master", []):
            add(f"Red flag — {flag.get('finding', '')}: {flag.get('action', '')}")
        for step in data.get("head_to_toe_sequence", []):
            desc = step.get("description") or step.get("rationale") or ""
            add(f"{step.get('step', '')}: {desc}")

    elif module_id == "mental_health":
        data = load_content("mental_health.json")
        for tech in data.get("therapeutic_communication", []):
            add(f"{tech.get('technique', '')}: {tech.get('description', '')}")
        for flag in data.get("safety_risk_flags", []):
            add(f"Safety — {flag.get('finding', '')}: {flag.get('action', '')}")

    elif module_id in ("pharmacy_calculations", "pharmacy"):
        data = load_content("pharmacy_calculations.json")
        for topic in data.get("topic_outline", []):
            add(f"{topic.get('title', '')}: {', '.join(topic.get('subtopics', []))}")
        for ct in data.get("calc_types", []):
            add(f"{ct.get('name', '')}: {ct.get('description', '')}")

    elif module_id in MODULE_CONTENT_KEYS:
        cfg = resolve_module(module_id)
        filename = cfg.get("content_file", f"{module_id}.json")
        data = load_content(filename)
        if not data:
            return []
        for item in _iter_module_records(module_id, data):
            title, body = _content_item_text(item)
            add(f"{title}: {body}")

    return _rank_snippets(candidates, limit=4)


def _resolve_intent(request: SocraticRequest) -> str:
    intent = (request.intent or "explore").lower()
    return intent if intent in VALID_INTENTS else "explore"


def _parse_page_context(raw: Optional[str]) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def _is_explore_phase(request: SocraticRequest) -> bool:
    """Guiding-questions phase: first N turns unless student requests deeper teaching."""
    if not request.socratic_mode:
        return False
    intent = _resolve_intent(request)
    if intent in VALID_INTENTS and intent != "explore":
        return False
    return _count_assistant_turns(request.context) < EXPLORE_TURNS_BEFORE_TEACH


def _build_system_prompt(
    module_id: str,
    topic: str,
    context_snippet: str,
    topic_category: str,
    explore_only: bool,
    intent: str = "explore",
    page_ctx: Optional[dict] = None,
    track_id: str = "nursing",
) -> str:
    sources = sources_for_module(module_id)
    source_lines = "\n".join(
        f"- {s.title}: {s.citation}" + (f" ({s.url})" if s.url else "")
        for s in sources[:4]
    )
    domain_rules = DOMAIN_SOCRATIC_RULES.get(
        topic_category, DOMAIN_SOCRATIC_RULES["general"]
    )
    intent_rules = INTENT_RULES.get(intent, INTENT_RULES["explore"])
    page_lines = ""
    if page_ctx:
        subj = page_ctx.get("subject") or page_ctx.get("tab") or ""
        snippet = page_ctx.get("snippet") or ""
        if subj or snippet:
            page_lines = (
                f"\nPAGE CONTEXT (student is viewing this now):\n"
                f"- Subject: {subj}\n"
                f"- Snippet: {snippet[:400]}\n"
                "Tie your questions and teaching directly to this context.\n"
            )
    phase_rule = (
        "PHASE: EXPLORE — You MUST NOT give direct answers, definitions, or numeric results. "
        "Respond ONLY with 2-3 guiding questions and brief encouragement. "
        "Do not reveal the answer yet — the student must think first."
        if explore_only
        else "PHASE: TEACH — The student has explored the question. You may now provide a concise "
        "clinical explanation AFTER briefly acknowledging their thinking. "
        "Still use Socratic follow-ups and connect to patient safety."
    )
    track = TRACKS.get(track_id, TRACKS["nursing"])
    mod_cfg = resolve_module(module_id)
    module_focus = (
        f"MODULE FOCUS: {mod_cfg.get('label', module_id)} — {mod_cfg.get('hint', topic)}. "
        "Frame every question and example for what the student is studying in this module."
    )
    return f"""You are a Socratic teaching partner for The Ward at New River CTC.

LEARNER: {track['learner']}
TRACK: {track['label']} — frame examples for {track['professional_role']} practice and {track['exam_frame']}.

TEACHING RULES (strict):
1. {phase_rule}
2. {intent_rules}
3. {domain_rules}
4. {module_focus}
5. Always tie concepts to clinical relevance — every concept has a real practice "why."
6. Cite verified sources when making factual claims:
{source_lines}
7. Use clear, encouraging language — preceptor tone, not answer-bot tone.
8. Keep responses concise (2-4 short paragraphs max unless depth is requested).
9. End EVERY response with exactly this block (3 follow-up questions):
{page_lines}

{FOLLOW_UP_MARKER}
- [guiding question 1]
- [guiding question 2]
- [guiding question 3]

MODULE: {module_id} — {topic}
TOPIC CATEGORY: {topic_category}
VERIFIED CONTENT SNIPPET:
{context_snippet}
"""


def _get_module_context_snippet(module_id: str, topic_category: str) -> str:
    snippets: list[str] = []

    if module_id == "terminology":
        data = load_content("terminology.json")
        for p in data.get("prefixes", [])[:3]:
            snippets.append(f"Prefix {p.get('element', '')}: {p.get('meaning', '')}")
        terms = load_content("terminology_terms.json").get("terms", [])[:2]
        for t in terms:
            snippets.append(f"Term {t.get('term')}: {t.get('definition', '')[:120]}")

    elif module_id == "microbiology":
        data = load_content("microbiology.json")
        for link in data.get("infection_chain", [])[:4]:
            snippets.append(f"{link.get('name', '')}: {link.get('description', '')[:120]}")
        if topic_category == "pathophysiology":
            for p in data.get("healthcare_pathogens", [])[:2]:
                snippets.append(
                    f"{p.get('name', '')}: {p.get('clinical_why', '')[:100]}"
                )

    elif module_id == "dosage":
        data = load_content("dosage.json")
        for rule in data.get("pharmacology_safety", [])[:3]:
            if isinstance(rule, dict):
                snippets.append(
                    f"{rule.get('title', '')}: {rule.get('concept', '')[:100]}"
                )
        if topic_category in ("pharmacology", "drug_class", "medication"):
            for dc in data.get("drug_classes", [])[:3]:
                snippets.append(
                    f"{dc.get('name', '')} ({dc.get('category_label', '')}): "
                    f"{dc.get('mechanism', '')[:90]}"
                )
        if topic_category == "calculation":
            fp = data.get("first_principles", {})
            for ct in data.get("calc_types", [])[:2]:
                cid = ct.get("id", "")
                if cid in fp:
                    snippets.append(f"First principle ({ct.get('name')}): {fp[cid].get('core_idea', '')[:100]}")

    elif module_id == "assessment":
        data = load_content("assessment.json")
        for flag in data.get("red_flags_master", [])[:2]:
            snippets.append(
                f"Red flag — {flag.get('finding', '')}: {flag.get('action', '')[:80]}"
            )
        for step in data.get("head_to_toe_sequence", [])[:2]:
            desc = step.get("description") or step.get("rationale") or ""
            snippets.append(f"Assessment step: {step.get('step', '')} — {desc[:80]}")

    elif module_id == "mental_health":
        data = load_content("mental_health.json")
        for tech in data.get("therapeutic_communication", [])[:2]:
            snippets.append(
                f"{tech.get('technique', '')}: {tech.get('description', '')[:90]}"
            )
        if topic_category in ("psychosocial", "safety", "mental_health"):
            for flag in data.get("safety_risk_flags", [])[:2]:
                snippets.append(
                    f"Safety — {flag.get('finding', '')[:60]}: {flag.get('action', '')[:70]}"
                )

    elif module_id in ("pharmacy_calculations", "pharmacy"):
        data = load_content("pharmacy_calculations.json")
        for topic in data.get("topic_outline", [])[:3]:
            snippets.append(f"{topic.get('title', '')}: {', '.join(topic.get('subtopics', [])[:2])}")
        for ct in data.get("calc_types", [])[:2]:
            snippets.append(
                f"{ct.get('name', '')}: {ct.get('description', '')[:90]}"
            )

    elif module_id in MODULE_CONTENT_KEYS:
        cfg = resolve_module(module_id)
        data = load_content(cfg.get("content_file", f"{module_id}.json"))
        if data:
            for item in _iter_module_records(module_id, data)[:4]:
                title, body = _content_item_text(item)
                snippets.append(f"{title}: {body[:100]}")
        if not snippets:
            fallbacks = {
                "pathophysiology": (
                    "Pathophysiology links cellular disruption → compensatory response → clinical manifestations."
                ),
                "maternal_child": (
                    "Maternal-child nursing prioritizes two-patient safety, fetal monitoring, and escalation criteria."
                ),
            }
            snippets.append(fallbacks.get(module_id, "Connect mechanism to monitoring and patient safety."))

    else:
        snippets.append(
            "Nursing practice prioritizes patient safety, evidence-based care, and NCLEX-aligned clinical judgment."
        )

    return "\n".join(snippets[:6]) or "General nursing fundamentals and patient safety."


def _enrich_context_snippet(
    module_id: str,
    topic_category: str,
    page_ctx: dict,
    question: str = "",
) -> str:
    base = _get_module_context_snippet(module_id, topic_category)
    matched = _search_module_content(module_id, question, topic_category) if question else []
    extra: list[str] = []
    if page_ctx.get("subject"):
        extra.append(f"Current focus: {page_ctx['subject']}")
    if page_ctx.get("snippet"):
        extra.append(f"On-screen content: {page_ctx['snippet'][:300]}")
    if page_ctx.get("tab"):
        extra.append(f"Active tab: {page_ctx['tab']}")
    merged = extra + matched + ([base] if base else [])
    return "\n".join(merged[:8])


def _default_quick_actions(
    intent: str, has_history: bool, track_id: str = "nursing"
) -> list[str]:
    role = TRACKS.get(track_id, TRACKS["nursing"])["considerations_label"]
    considerations = f"What are the key {role}?"
    if intent == "explore" and not has_history:
        return ["Explain the mechanism", "Why does this matter clinically?", considerations]
    if intent == "explain_mechanism":
        return ["Why does this matter clinically?", considerations]
    if intent == "explain_further":
        exam = "NAPLEX-style scenario" if track_id == "pharmacy" else "NCLEX-style scenario"
        return ["Why does this matter clinically?", f"Give me an {exam}"]
    if intent == "clinical_why":
        return ["Explain the mechanism", considerations]
    if intent == "professional_considerations":
        return ["Explain the mechanism", "Why does this matter clinically?"]
    return ["Explain the mechanism", "Why does this matter clinically?", considerations]


def _parse_ollama_response(text: str) -> tuple[str, list[str]]:
    if FOLLOW_UP_MARKER in text:
        parts = text.split(FOLLOW_UP_MARKER, 1)
        main = parts[0].strip()
        follow_block = parts[1].strip()
    else:
        main = text.strip()
        follow_block = ""

    follow_ups: list[str] = []
    for line in follow_block.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[-•*]\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        if line and len(line) > 5:
            follow_ups.append(line)

    if not follow_ups:
        follow_ups = [
            "What part of this concept feels unclear to you?",
            "How would you apply this in a clinical scenario?",
            "What related concepts might connect to this?",
        ]

    return main, follow_ups[:3]


def _build_messages(request: SocraticRequest, system_prompt: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    for turn in _parse_context_history(request.context)[-8:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)})

    messages.append({"role": "user", "content": request.question})
    return messages


async def check_ollama_health() -> dict[str, Any]:
    """Lightweight Ollama availability probe for health endpoints."""
    if not settings.ai_enabled or settings.ai_provider != "ollama":
        return {
            "available": False,
            "reason": "disabled",
            "provider": settings.ai_provider,
            "model": settings.ai_model,
        }
    base = settings.ai_base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(4.0, connect=2.0)) as client:
            resp = await client.get(f"{base}/api/tags")
            resp.raise_for_status()
            tags = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in tags]
            model_ready = any(settings.ai_model in name for name in model_names)
            return {
                "available": True,
                "model_ready": model_ready,
                "provider": "ollama",
                "base_url": base,
                "model": settings.ai_model,
                "models_found": len(model_names),
            }
    except httpx.TimeoutException:
        return {"available": False, "reason": "timeout", "base_url": base, "model": settings.ai_model}
    except httpx.ConnectError:
        return {"available": False, "reason": "unavailable", "base_url": base, "model": settings.ai_model}
    except httpx.HTTPError as exc:
        return {
            "available": False,
            "reason": "http_error",
            "detail": str(exc),
            "base_url": base,
            "model": settings.ai_model,
        }


async def _call_ollama(messages: list[dict[str, str]]) -> OllamaResult:
    url = f"{settings.ai_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ai_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 1024},
    }
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=5.0, read=85.0)
        ) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "").strip()
            if not content:
                logger.warning("Ollama returned empty content for model %s", settings.ai_model)
                return OllamaResult(error="empty_response")
            return OllamaResult(content=content)
    except httpx.TimeoutException as exc:
        logger.warning("Ollama request timed out: %s", exc)
        return OllamaResult(error="timeout")
    except httpx.ConnectError as exc:
        logger.warning("Ollama unavailable at %s: %s", settings.ai_base_url, exc)
        return OllamaResult(error="unavailable")
    except httpx.HTTPStatusError as exc:
        logger.warning("Ollama HTTP error %s: %s", exc.response.status_code, exc)
        return OllamaResult(error="http_error")
    except httpx.HTTPError as exc:
        logger.warning("Ollama request failed: %s", exc)
        return OllamaResult(error="http_error")
    except Exception as exc:
        logger.warning("Ollama unexpected error: %s", exc)
        return OllamaResult(error="unavailable")


def _degraded_status_note(ai_status: str, reason: Optional[str] = None) -> str:
    if ai_status != "error":
        return {
            "placeholder": "_Socratic teaching partner · enable Ollama for live dialogue._",
        }.get(ai_status, "")
    notes = {
        "timeout": f"_Ollama timed out — structured teaching shown. Check `{settings.ai_model}` at {settings.ai_base_url}._",
        "unavailable": f"_Ollama unreachable at {settings.ai_base_url} — guided prompts shown._",
        "http_error": f"_Ollama returned an error — structured teaching shown._",
        "empty_response": f"_Ollama returned no content for `{settings.ai_model}` — structured teaching shown._",
    }
    return notes.get(reason or "unavailable", notes["unavailable"])


def _subject_from_request(request: SocraticRequest, page_ctx: dict) -> str:
    if page_ctx.get("subject"):
        return str(page_ctx["subject"])
    q = request.question.strip()
    if len(q) > 80:
        return q[:77] + "…"
    return q or "this topic"


def _intent_response(
    request: SocraticRequest,
    module_id: str,
    topic: str,
    topic_category: str,
    sources: list[SourceRef],
    ai_status: str,
    intent: str,
    page_ctx: dict,
    context_snippet: str,
    track_id: str = "nursing",
    degraded_reason: Optional[str] = None,
) -> SocraticResponse:
    """Placeholder for explicit teaching intents."""
    subject = _subject_from_request(request, page_ctx)
    has_history = _count_assistant_turns(request.context) > 0
    track = TRACKS.get(track_id, TRACKS["nursing"])
    role = track["professional_role"]
    ack = _conversation_acknowledgment(request.context)

    if intent == "explain_mechanism":
        body = (
            f"{ack}Let's unpack the **mechanism** behind **{subject}**.\n\n"
            f"**First — what do you think is being targeted?** "
            f"(receptor, pathway, or calculation method)\n\n"
            f"**Mechanism layers ({track['label']}):**\n"
        )
        deepen: dict[str, str] = {
            "drug_mechanism": "Target → desired effect → onset/duration → monitoring for toxicity.",
            "pathophysiology": "Normal function → disruption → compensatory response → clinical signs.",
            "calculation": "Given → method (dimensional analysis/alligation) → result → independent verification.",
            "compounding": "Strength conversion → quantity needed → isotonicity/stability check → beyond-use dating.",
        }
        body += deepen.get(
            topic_category,
            "Process → clinical effect → what the professional verifies before acting.",
        )
        follow_ups = [
            "What would you monitor if this mechanism is exaggerated?",
            f"What {role} teaching connects to this mechanism?",
            "What error trap do students miss here?",
        ]
        phase = "teach"
        guiding = False
    elif intent == "professional_considerations":
        body = (
            f"**Key {track['considerations_label']}** for **{subject}**:\n\n"
            f"Before I list them — **what risk** worries you most if this is mishandled?\n\n"
        )
        if track_id == "pharmacy":
            body += (
                "**Pharmacist practice:** independent verification, patient counseling points, "
                "drug interaction screening, documentation, and NAPLEX-style prioritization.\n\n"
            )
        else:
            body += (
                "**Nursing practice:** assessment before action, monitoring parameters, "
                "patient teaching, scope/escalation, and NCLEX priority frameworks.\n\n"
            )
        body += f"**From verified content:**\n{context_snippet[:350]}"
        follow_ups = [
            f"What would you document as the {role}?",
            "When would you escalate or consult?",
            track["exam_frame"].split(" and ")[0] + " — how might this be tested?",
        ]
        phase = "teach"
        guiding = False
    elif intent == "explain_further":
        body = (
            f"Let's go **deeper** on **{subject}** — I'll teach in layers, not lectures.\n\n"
            f"**Building on what you're studying:**\n{context_snippet.splitlines()[0] if context_snippet else topic}\n\n"
            "**One layer deeper:**\n"
        )
        deepen_map: dict[str, str] = {
            "pathophysiology": (
                "Think agent → host response → signs/symptoms. "
                "The disease process is a chain — which link would you assess first at the bedside?"
            ),
            "drug_mechanism": (
                "Every drug connects target → effect → nursing monitoring. "
                "What adverse effect would you watch for if the mechanism is exaggerated?"
            ),
            "assessment_finding": (
                "A finding is only meaningful in context — baseline, trend, and associated symptoms. "
                "What additional data would confirm this is urgent vs. chronic?"
            ),
            "calculation": (
                "Dimensional analysis is a safety tool, not just math. "
                "Walk through Desired/Have again — where do most students cancel the wrong unit?"
            ),
        }
        body += deepen_map.get(topic_category, "Connect mechanism to monitoring and patient teaching.")
        exam_label = "NAPLEX" if track_id == "pharmacy" else "NCLEX"
        follow_ups = [
            "What part of this still feels fuzzy?",
            "Can you teach this back in one sentence?",
            f"What {exam_label} distractor might trick a student here?",
        ]
        phase = "teach"
        guiding = False
    else:  # clinical_why
        module_why: dict[str, str] = {
            "terminology": "Misreading word parts causes medication and documentation errors — clarity saves lives.",
            "microbiology": "Breaking the chain of infection is a core nursing responsibility; hand hygiene is your #1 tool.",
            "dosage": "Calculation errors are a leading cause of preventable harm — always verify with a second nurse.",
            "assessment": "Missed abnormal findings delay life-saving interventions — systematic assessment is patient safety.",
            "pharmacy_calculations": "Compounding and verification errors reach patients directly — independent double-check is mandatory.",
            "pharmacy": "Pharmacist judgment affects every dispensed dose — accuracy and counseling are patient safety.",
            "pathophysiology": "Understanding disease chains prevents missed deterioration — connect mechanism to assessment priorities.",
            "maternal_child": "Maternal-child errors affect two patients — systematic assessment and escalation protect both.",
        }
        why = module_why.get(module_id, "Every concept connects to safe, evidence-based patient care.")
        exam = track["exam_frame"]
        body = (
            f"**Why does {subject} matter clinically?**\n\n"
            f"Before I connect the dots — **what patient outcome** worries you most if a {role} misunderstands this?\n\n"
            f"**Clinical relevance ({module_hint(module_id)}):**\n{why}\n\n"
            f"**From verified content:**\n{context_snippet[:400]}\n\n"
            f"Share your answer above, and I'll link it to priority {role} actions and {exam}."
        )
        exam_q = "NAPLEX-style" if track_id == "pharmacy" else "NCLEX-style"
        follow_ups = [
            "What would you monitor at the bedside or in verification?",
            "When would you escalate or consult?",
            f"How might this appear on an {exam_q} question?",
        ]
        phase = "teach"
        guiding = False

    status_note = _degraded_status_note(ai_status, degraded_reason)

    return SocraticResponse(
        response=f"{body}\n\n{status_note}".strip(),
        follow_up_questions=follow_ups,
        sources=sources,
        ai_status=ai_status,
        phase=phase,
        topic_category=topic_category,
        module_id=module_id,
        guiding_only=guiding,
        intent=intent,
        quick_actions=_default_quick_actions(intent, has_history, track_id),
        degraded_reason=degraded_reason,
    )


MODULE_EXPLORE_PROMPTS: dict[str, tuple[str, list[str]]] = {
    "pathophysiology": (
        "Let's trace the **disease cascade** together — I won't explain the process yet.\n\n"
        "Regarding: \"{question}\"\n\n"
        "**Build the chain in your own words:**\n"
        "1. What is *normal* function in the affected system?\n"
        "2. What disrupts that normal state (agent, stressor, or deficit)?\n"
        "3. What compensatory response might you see — and what signs would break through?\n\n"
        "Answer any one link in the chain, then ask again — we'll connect it to priority assessments.",
        [
            "What is normal anatomy/physiology before this disease process begins?",
            "Where does compensation fail and decompensation begin?",
            "Which assessment findings would confirm your hypothesis at the bedside?",
        ],
    ),
    "maternal_child": (
        "Let's think through this **maternal-child** scenario — guiding questions first.\n\n"
        "Regarding: \"{question}\"\n\n"
        "**Two-patient safety lens:**\n"
        "1. Who is your priority patient right now — mother, fetus/newborn, or both?\n"
        "2. What assessment data do you need *before* acting?\n"
        "3. What red-flag finding would make you escalate immediately?\n\n"
        "Share your reasoning on one point, then we'll deepen with NCLEX-style prioritization.",
        [
            "What is the priority assessment for this maternal or newborn finding?",
            "What red-flag symptoms would make you escalate immediately?",
            "How does this connect to patient teaching and two-patient safety?",
        ],
    ),
}


def _explore_content_nudge(
    module_id: str, page_ctx: dict, matched_count: int
) -> str:
    """Explore phase: encourage thinking without revealing verified answers."""
    subject = page_ctx.get("subject") or module_hint(module_id)
    if matched_count > 0:
        return (
            f"**Verified module content** on **{subject}** is loaded — "
            "try answering a guiding question first; I'll connect it to sources on your next turn."
        )
    return (
        f"**Studying:** {subject} — share your initial thinking; "
        "I'll build on it without giving away the answer yet."
    )


def _explore_response(
    request: SocraticRequest,
    module_id: str,
    topic: str,
    topic_category: str,
    sources: list[SourceRef],
    ai_status: str,
    page_ctx: Optional[dict] = None,
    degraded_reason: Optional[str] = None,
) -> SocraticResponse:
    """Explore-phase placeholder: guiding questions only."""
    page_ctx = page_ctx or {}
    ack = _conversation_acknowledgment(request.context)
    turn_num = _count_assistant_turns(request.context) + 1
    category_prompts: dict[str, tuple[str, list[str]]] = {
        "pathophysiology": (
            "Let's think through the **pathophysiology** together — I won't give you the answer yet.\n\n"
            f"Regarding: \"{request.question}\"\n\n"
            "**Before we go further, consider:**\n"
            "1. What is the *normal* structure or function involved here?\n"
            "2. What agent or process disrupts that normal state?\n"
            "3. What clinical signs would you expect as the body responds?\n\n"
            "Take a moment to answer one of these in your own words, then ask me again — "
            "I'll help you build the full clinical picture.",
            [
                "What is normal anatomy/physiology for this system?",
                "What is the infectious agent or disease process doing at the cellular level?",
                "Which assessment findings would confirm your hypothesis?",
            ],
        ),
        "drug_mechanism": (
            "Let's explore the **drug mechanism** — guiding questions first.\n\n"
            f"You asked: \"{request.question}\"\n\n"
            "**Think through:**\n"
            "1. What is the patient's underlying problem this drug addresses?\n"
            "2. What is the *desired therapeutic outcome*?\n"
            "3. What would you monitor to know the drug is working — or causing harm?\n\n"
            "Reply with your thinking on any one point, and we'll connect it to the mechanism of action.",
            [
                "What receptor or body system does this drug target?",
                "What is the most important nursing implication of this mechanism?",
                "What patient teaching relates to how this drug works?",
            ],
        ),
        "assessment_finding": (
            "Let's work through this **assessment finding** step by step.\n\n"
            f"Finding in question: \"{request.question}\"\n\n"
            "**Ask yourself:**\n"
            "1. Is this subjective or objective data?\n"
            "2. Where does this fit in your head-to-toe or focused assessment?\n"
            "3. What priority action does this finding suggest?\n\n"
            "Share your reasoning, then I'll help you connect it to clinical significance.",
            [
                "What additional assessments would you perform next?",
                "Is this finding within normal limits for your patient?",
                "When would you escalate to the provider?",
            ],
        ),
        "calculation": (
            "Let's set up this **dosage calculation** from first principles — no answer yet.\n\n"
            f"Problem: \"{request.question}\"\n\n"
            "**Identify before you calculate:**\n"
            "1. What is **Desired** (ordered)?\n"
            "2. What is **Have** (available)?\n"
            "3. Do the units match — or do you need to convert?\n\n"
            "Write out what you have for D and H, then ask again — I'll guide your setup.",
            [
                "What units are ordered vs. available?",
                "What is your first step in dimensional analysis?",
                "What safety check would you perform before administering?",
            ],
        ),
        "compounding": (
            "Let's work through this **compounding problem** — no final quantity yet.\n\n"
            f"Problem: \"{request.question}\"\n\n"
            "**Identify before you compound:**\n"
            "1. What strengths are you mixing or diluting?\n"
            "2. Which method applies — alligation, dilution, or QS?\n"
            "3. How would you independently verify the result?\n\n"
            "Share your setup, then I'll guide the next step.",
            [
                "What is the desired final strength or isotonicity?",
                "What beyond-use dating or stability factor applies?",
                "What pharmacist verification step prevents patient harm?",
            ],
        ),
        "psychosocial": (
            "Let's explore this **psychosocial** scenario with guiding questions first.\n\n"
            f"Situation: \"{request.question}\"\n\n"
            "**Consider:**\n"
            "1. What therapeutic response builds trust here?\n"
            "2. What safety screening is needed before anything else?\n"
            "3. What is the priority nursing action?\n\n"
            "Share your thinking on one point, then we'll go deeper.",
            [
                "What communication technique fits this moment?",
                "What risk level does this suggest?",
                "When would you initiate 1:1 observation or escalation?",
            ],
        ),
    }

    default = (
        f"Let's explore **{topic}** together — I'll ask before I tell.\n\n"
        f"You asked: \"{request.question}\"\n\n"
        "What do you already know about this topic? What assumptions are you making?\n\n"
        "Share your initial thinking, then I'll guide you deeper with clinical connections.",
        [
            "What part of this concept feels unclear to you?",
            "How would you apply this in a clinical scenario?",
            "What related concepts might connect to this?",
        ],
    )

    module_template = MODULE_EXPLORE_PROMPTS.get(module_id)
    if module_template:
        body, follow_ups = module_template[0], list(module_template[1])
        body = body.format(question=request.question)
    else:
        body, follow_ups = category_prompts.get(topic_category, default)

    matched = _search_module_content(module_id, request.question, topic_category)
    subject = page_ctx.get("subject")
    if subject:
        body = body.replace(
            f"\"{request.question}\"",
            f"**{subject}** (from your current study screen)",
            1,
        ).replace(
            "Regarding: \"{question}\"",
            f"Regarding: **{subject}** (from your current study screen)",
            1,
        )
    if ack:
        body = f"{ack}{body}"
    elif turn_num > 1:
        body = (
            f"**Turn {turn_num} — still exploring.** Let's keep building your clinical reasoning.\n\n"
            f"{body}"
        )
    starters = MODULE_STARTER_QUESTIONS.get(module_id, MODULE_STARTER_QUESTIONS["general"])
    starter_block = "\n".join(f"• {s}" for s in starters[:3])
    status_note = _degraded_status_note(ai_status, degraded_reason)
    content_nudge = _explore_content_nudge(module_id, page_ctx, len(matched))

    return SocraticResponse(
        response=(
            f"{body}\n\n**Try thinking about:**\n{starter_block}\n\n"
            f"{content_nudge}\n\n"
            f"{status_note}"
        ).strip(),
        follow_up_questions=follow_ups,
        sources=sources,
        ai_status=ai_status,
        phase="explore",
        topic_category=topic_category,
        module_id=module_id,
        guiding_only=True,
        intent="explore",
        quick_actions=_default_quick_actions(
            "explore", turn_num > 1, resolve_track(module_id)
        ),
        degraded_reason=degraded_reason,
    )


def _teach_response(
    request: SocraticRequest,
    module_id: str,
    topic: str,
    topic_category: str,
    sources: list[SourceRef],
    ai_status: str,
    page_ctx: Optional[dict] = None,
    context_snippet: str = "",
    track_id: str = "nursing",
    degraded_reason: Optional[str] = None,
) -> SocraticResponse:
    """Post-explore turn: concise teaching with clinical connections and memory."""
    page_ctx = page_ctx or {}
    snippet = context_snippet or _enrich_context_snippet(
        module_id, topic_category, page_ctx, request.question
    )
    ack = _conversation_acknowledgment(request.context)
    track = TRACKS.get(track_id, TRACKS["nursing"])
    exam_label = "NAPLEX" if track_id == "pharmacy" else "NCLEX"
    module_guidance: dict[str, str] = {
        "terminology": "Breaking terms into word parts prevents documentation and medication errors.",
        "microbiology": "Breaking any chain link prevents transmission — hand hygiene is the #1 intervention.",
        "dosage": "Dimensional analysis ensures units cancel correctly — always verify with a second nurse.",
        "assessment": "Systematic assessment (IPPA) ensures no critical finding is missed.",
        "mental_health": "Therapeutic presence and safety screening come before problem-solving.",
        "pathophysiology": "Disease is a chain — identify where normal function breaks down, then what you'd assess first.",
        "maternal_child": "Two patients, one plan — prioritize maternal stability, fetal well-being, and escalation criteria.",
        "pharmacy_calculations": "Independent verification and dimensional analysis prevent compounding errors.",
    }
    category_bridge: dict[str, str] = {
        "pathophysiology": "Link normal → disruption → compensatory response → priority assessment.",
        "drug_mechanism": "Connect target → effect → monitoring and patient teaching.",
        "assessment_finding": "Subjective vs objective → trend → priority action → escalation.",
        "calculation": "Desired/Have → setup → result → independent safety check.",
        "psychosocial": "Rapport → safety screen → least-restrictive intervention.",
        "compounding": "Strength → method → verification → beyond-use dating.",
    }
    guidance = module_guidance.get(module_id, "Connect every concept to patient safety.")
    bridge = category_bridge.get(
        topic_category, "Tie mechanism to monitoring and patient safety."
    )
    subject = _subject_from_request(request, page_ctx)
    status_note = _degraded_status_note(ai_status, degraded_reason)

    return SocraticResponse(
        response=(
            f"{ack}Good — you've explored **{topic_category.replace('_', ' ')}**. "
            f"Let's build on your thinking about **{subject}**.\n\n"
            f"**Clinical connection ({module_hint(module_id)}):** {guidance}\n\n"
            f"**Teaching bridge:** {bridge}\n\n"
            f"**From verified content:**\n{snippet}\n\n"
            f"Keep asking follow-up questions — the goal is {track['exam_frame']}, not memorization.\n\n"
            f"{status_note}"
        ).strip(),
        follow_up_questions=[
            "Can you teach this concept back to me in one sentence?",
            f"What {exam_label}-style distractor might trick a student here?",
            "What would you do differently at the bedside based on this?",
        ],
        sources=sources,
        ai_status=ai_status,
        phase="teach",
        topic_category=topic_category,
        module_id=module_id,
        guiding_only=False,
        intent="explore",
        quick_actions=_default_quick_actions("explore", True, track_id),
        degraded_reason=degraded_reason,
    )


async def socratic_tutor(request: SocraticRequest) -> SocraticResponse:
    module_id = request.module_id if request.module_id in SOCRATIC_MODULES else "general"
    topic = module_hint(module_id)
    intent = _resolve_intent(request)
    page_ctx = _parse_page_context(request.page_context)
    track_id = page_ctx.get("track") or resolve_track(module_id)
    topic_category = detect_topic_category(
        request.question, module_id, request.topic_category
    )
    context_snippet = _enrich_context_snippet(
        module_id, topic_category, page_ctx, request.question
    )
    sources = sources_for_module(module_id)
    explore_only = _is_explore_phase(request)
    has_history = _count_assistant_turns(request.context) > 0

    if settings.ai_enabled and settings.ai_provider == "ollama":
        system_prompt = _build_system_prompt(
            module_id, topic, context_snippet, topic_category, explore_only,
            intent, page_ctx, track_id,
        )
        messages = _build_messages(request, system_prompt)
        ollama = await _call_ollama(messages)

        if ollama.content:
            main, follow_ups = _parse_ollama_response(ollama.content)
            return SocraticResponse(
                response=main,
                follow_up_questions=follow_ups,
                sources=sources,
                ai_status="live",
                phase="explore" if explore_only else "teach",
                topic_category=topic_category,
                module_id=module_id,
                guiding_only=explore_only,
                intent=intent,
                quick_actions=_default_quick_actions(intent, has_history, track_id),
            )
        degrade = ollama.error or "unavailable"
        if intent in TEACHING_INTENTS:
            return _intent_response(
                request, module_id, topic, topic_category, sources, "error",
                intent, page_ctx, context_snippet, track_id, degrade,
            )
        if explore_only:
            return _explore_response(
                request, module_id, topic, topic_category, sources, "error",
                page_ctx, degrade,
            )
        return _teach_response(
            request, module_id, topic, topic_category, sources, "error",
            page_ctx, context_snippet, track_id, degrade,
        )

    if intent in TEACHING_INTENTS:
        return _intent_response(
            request, module_id, topic, topic_category, sources, "placeholder",
            intent, page_ctx, context_snippet, track_id,
        )
    if explore_only:
        return _explore_response(
            request, module_id, topic, topic_category, sources, "placeholder", page_ctx
        )
    return _teach_response(
        request, module_id, topic, topic_category, sources, "placeholder",
        page_ctx, context_snippet, track_id,
    )