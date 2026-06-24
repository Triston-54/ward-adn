"""Medical terminology business logic — terms, SRS, practice, export."""
import random
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FlashcardState, SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "terminology"
DEFAULT_SOURCE = {
    "title": "Medical Terminology for Health Professions",
    "citation": "Ehrlich & Schroeder, 8th Ed.",
    "verified_date": "2026-06",
}


def _default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("terminology", DEFAULT_SOURCE)
    return SourceRef(
        title=s.get("title", DEFAULT_SOURCE["title"]),
        url=s.get("url"),
        citation=s.get("citation", DEFAULT_SOURCE["citation"]),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_all_terms() -> list[dict[str, Any]]:
    """Merge base terminology.json terms with generated terminology_terms.json."""
    base = load_content("terminology.json")
    extra = load_content("terminology_terms.json")
    seen: set[str] = set()
    merged: list[dict] = []
    for t in base.get("terms", []) + extra.get("terms", []):
        key = t["term"].lower()
        if key not in seen:
            seen.add(key)
            merged.append(t)
    return sorted(merged, key=lambda x: x["term"].lower())


def get_components() -> dict:
    data = load_content("terminology.json")
    return {
        "prefixes": data.get("prefixes", []),
        "roots": data.get("roots", []),
        "suffixes": data.get("suffixes", []),
    }


def search_terms(
    q: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> tuple[list[dict], int]:
    terms = get_all_terms()
    if q:
        ql = q.lower()
        terms = [
            t for t in terms
            if ql in t["term"].lower()
            or ql in t["definition"].lower()
            or ql in (t.get("breakdown") or "").lower()
            or ql in (t.get("category") or "").lower()
        ]
    if category:
        terms = [t for t in terms if t.get("category") == category]
    total = len(terms)
    return terms[:limit], total


def generate_mc_questions(count: int) -> list[dict]:
    """Multiple-choice questions from term database."""
    terms = get_all_terms()
    pool = safe_sample(terms, count)
    questions = []
    all_terms = [t["term"] for t in terms]

    for i, t in enumerate(pool):
        distractors = safe_sample(
            [x for x in all_terms if x.lower() != t["term"].lower()],
            min(3, len(all_terms) - 1),
        )
        options = [t["term"]] + distractors
        random.shuffle(options)
        correct = options.index(t["term"])
        questions.append({
            "id": f"mc-{t['term']}-{i}",
            "type": "multiple_choice",
            "question": f"What medical term means: \"{t['definition']}\"?",
            "options": options,
            "correct_index": correct,
            "correct_answer": t["term"],
            "explanation": (
                f"**{t['term']}** — {t.get('breakdown', '')}. "
                f"{t.get('clinical_relevance', '')}"
            ),
            "source": t.get("source", DEFAULT_SOURCE),
            "nclex_category": "Reduction of Risk Potential",
        })
    return questions


def generate_type_questions(count: int) -> list[dict]:
    """Type-the-term questions from definitions."""
    terms = get_all_terms()
    pool = safe_sample(terms, count)
    questions = []
    for i, t in enumerate(pool):
        questions.append({
            "id": f"type-{t['term']}-{i}",
            "type": "type_term",
            "question": f"Type the medical term for: \"{t['definition']}\"",
            "hint": t.get("breakdown", ""),
            "correct_answer": t["term"],
            "acceptable_answers": [t["term"].lower(), t["term"].replace("-", "")],
            "explanation": (
                f"**{t['term']}** — {t.get('breakdown', '')}. "
                f"{t.get('clinical_relevance', '')}"
            ),
            "source": t.get("source", DEFAULT_SOURCE),
        })
    return questions


def generate_mixed_practice(mc_count: int = 5, type_count: int = 5) -> list[dict]:
    """Mix of MC and type-the-term questions."""
    questions = generate_mc_questions(mc_count) + generate_type_questions(type_count)
    random.shuffle(questions)
    return questions


# ── Spaced Repetition (simplified SM-2) ───────────────────────────────────────

INTERVALS = [1, 3, 7, 14, 30, 60]  # days per repetition level


async def get_or_create_flashcard_state(
    session: AsyncSession, card_key: str
) -> FlashcardState:
    result = await session.execute(
        select(FlashcardState).where(
            FlashcardState.module_id == MODULE_ID,
            FlashcardState.card_key == card_key,
        )
    )
    state = result.scalar_one_or_none()
    if not state:
        state = FlashcardState(
            module_id=MODULE_ID,
            card_key=card_key,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
            next_review=date.today(),
        )
        session.add(state)
        await session.flush()
    return state


async def get_due_flashcards(
    session: AsyncSession, count: int = 20
) -> list[dict]:
    """Return flashcards due for review, prioritizing overdue cards."""
    terms = get_all_terms()
    today = date.today()
    cards = []

    for t in terms:
        state = await get_or_create_flashcard_state(session, t["term"].lower())
        due = state.next_review is None or state.next_review <= today
        cards.append({
            "key": t["term"].lower(),
            "front": t["term"],
            "back": t["definition"],
            "breakdown": t.get("breakdown", ""),
            "clinical": t.get("clinical_relevance", ""),
            "source": t.get("source", DEFAULT_SOURCE),
            "due": due,
            "repetitions": state.repetitions,
            "interval_days": state.interval_days,
            "next_review": state.next_review.isoformat() if state.next_review else None,
        })

    # Due first, then new (0 reps), then rest
    cards.sort(key=lambda c: (0 if c["due"] else 1, -c["repetitions"]))
    return cards[:count]


async def record_flashcard_review(
    session: AsyncSession, card_key: str, quality: int
) -> dict:
    """
    Record flashcard review. quality: 0=again, 1=hard, 2=good, 3=easy
    """
    state = await get_or_create_flashcard_state(session, card_key.lower())
    today = date.today()

    if quality == 0:
        state.repetitions = 0
        state.interval_days = 1
        state.incorrect_count += 1
        state.ease_factor = max(1.3, state.ease_factor - 0.2)
    else:
        state.correct_count += 1
        state.repetitions += 1
        idx = min(state.repetitions - 1, len(INTERVALS) - 1)
        state.interval_days = INTERVALS[idx]
        if quality == 3:
            state.interval_days = int(state.interval_days * 1.5)
            state.ease_factor = min(3.0, state.ease_factor + 0.1)
        elif quality == 1:
            state.interval_days = max(1, state.interval_days // 2)

    state.next_review = today + timedelta(days=state.interval_days)
    state.last_reviewed = datetime.utcnow()
    await session.flush()

    return {
        "card_key": card_key,
        "repetitions": state.repetitions,
        "interval_days": state.interval_days,
        "next_review": state.next_review.isoformat(),
        "ease_factor": round(state.ease_factor, 2),
    }


async def get_flashcard_stats(session: AsyncSession) -> dict:
    """SRS statistics for the module."""
    terms = get_all_terms()
    today = date.today()
    due_count = 0
    mastered = 0

    for t in terms:
        result = await session.execute(
            select(FlashcardState).where(
                FlashcardState.module_id == MODULE_ID,
                FlashcardState.card_key == t["term"].lower(),
            )
        )
        state = result.scalar_one_or_none()
        if state:
            if state.next_review and state.next_review <= today:
                due_count += 1
            if state.repetitions >= 4:
                mastered += 1
        else:
            due_count += 1

    return {
        "total_cards": len(terms),
        "due_today": due_count,
        "mastered": mastered,
        "progress_pct": round((mastered / len(terms)) * 100, 1) if terms else 0,
    }


def build_study_sheet_html(terms: Optional[list[dict]] = None, title: str = "Study Sheet") -> str:
    """Generate printable HTML study sheet."""
    if terms is None:
        terms = get_all_terms()[:50]
    rows = ""
    for i, t in enumerate(terms, 1):
        rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{t['term']}</strong></td>
            <td>{t['definition']}</td>
            <td class="clinical">{t.get('clinical_relevance', '')}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>The Ward — {title}</title>
<style>
  body {{ font-family: Georgia, serif; margin: 2cm; color: #111; }}
  h1 {{ color: #0f172a; border-bottom: 2px solid #38bdf8; padding-bottom: 8px; }}
  .meta {{ color: #666; font-size: 12px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
  th {{ background: #0f172a; color: white; padding: 8px; text-align: left; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) {{ background: #f8fafc; }}
  .clinical {{ color: #475569; font-size: 10px; }}
  @media print {{ body {{ margin: 1cm; }} }}
</style>
</head><body>
<h1>The Ward — Medical Terminology</h1>
<p class="meta">{title} · {len(terms)} terms · Source: Ehrlich &amp; Schroeder, 8th Ed. · New River CTC ADN</p>
<table>
  <thead><tr><th>#</th><th>Term</th><th>Definition</th><th>Clinical Relevance</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
<p class="meta">Generated by The Ward — local-first nursing study suite</p>
</body></html>"""


def build_clipboard_text(terms: Optional[list[dict]] = None) -> str:
    """Plain-text study sheet for clipboard."""
    if terms is None:
        terms = get_all_terms()[:30]
    lines = ["THE WARD — MEDICAL TERMINOLOGY STUDY SHEET", "=" * 50, ""]
    for i, t in enumerate(terms, 1):
        lines.append(f"{i}. {t['term']}")
        lines.append(f"   Definition: {t['definition']}")
        if t.get("breakdown"):
            lines.append(f"   Breakdown: {t['breakdown']}")
        if t.get("clinical_relevance"):
            lines.append(f"   Clinical: {t['clinical_relevance']}")
        lines.append("")
    lines.append("Source: Ehrlich & Schroeder, 8th Ed.")
    return "\n".join(lines)