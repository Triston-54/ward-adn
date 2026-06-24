"""Health Assessment module (NURS 146) — head-to-toe, systems, red flags, practice."""
import random
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FlashcardState, SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "assessment"
ITEMS_TOTAL = 132


def _data() -> dict:
    return load_content("assessment.json")


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("assessment", {})
    return SourceRef(
        title=s.get("title", "Open RN — Nursing Skills (Health Assessment)"),
        url=s.get("url", "https://openrn.org/nursingskills/"),
        citation=s.get("citation", "Open RN Nursing OER Textbook"),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_module_content() -> dict:
    """Full content payload for the module."""
    return _data()


def get_head_to_toe_sequence() -> list[dict]:
    return sorted(_data().get("head_to_toe_sequence", []), key=lambda x: x.get("order", 0))


def get_body_systems() -> list[dict]:
    return _data().get("body_systems", [])


def get_body_system(system_id: str) -> Optional[dict]:
    return next((s for s in get_body_systems() if s["id"] == system_id), None)


def get_red_flags() -> list[dict]:
    return _data().get("red_flags_master", [])


def _red_flags_with_ids() -> list[dict]:
    """Attach stable ids to red flag master entries."""
    flags = get_red_flags()
    return [
        {**f, "id": f.get("id") or f"rf-{i:03d}"}
        for i, f in enumerate(flags)
    ]


def _find_red_flag(flag_id: str) -> Optional[dict]:
    return next((f for f in _red_flags_with_ids() if f["id"] == flag_id), None)


def _red_flag_distractors(correct: dict, pool: list[dict], count: int = 3) -> list[str]:
    """Pick plausible wrong actions from other red flags."""
    others = [f for f in pool if f["id"] != correct["id"]]
    random.shuffle(others)
    distractors: list[str] = []
    for f in others:
        action = f["action"]
        if action != correct["action"] and action not in distractors:
            distractors.append(action)
        if len(distractors) >= count:
            break
    fallbacks = [
        "Continue routine assessment and reassess at end of shift",
        "Document finding and notify provider at next scheduled visit",
        "Apply comfort measures and recheck in 4 hours",
    ]
    for fb in fallbacks:
        if len(distractors) >= count:
            break
        if fb not in distractors and fb != correct["action"]:
            distractors.append(fb)
    return distractors[:count]


def _red_flag_explanation(flag: dict) -> str:
    priority = flag.get("priority", "immediate")
    system = flag.get("system", "clinical")
    return (
        f"**{flag['finding']}** is a {priority} red flag ({system}). "
        f"Immediate nursing action: {flag['action']}"
    )


def _red_flag_clinical_why(flag: dict) -> str:
    priority = flag.get("priority", "immediate")
    if priority == "immediate":
        return (
            "Clinical why: Immediate escalation protects patient safety — delays recognizing "
            "critical findings are a leading cause of preventable harm. Stop routine tasks and act."
        )
    return (
        "Clinical why: Urgent findings require timely nursing intervention and provider "
        "notification. Document objectively and monitor closely while escalating per protocol."
    )


def _red_flag_escalation_path(flag: dict) -> str:
    return f"Escalation path: {flag['action']}"


def get_red_flag_drill_questions(
    count: int = 5,
    system: Optional[str] = None,
) -> list[dict]:
    """Red flag triage drill — given a finding, choose the correct immediate action."""
    pool = _red_flags_with_ids()
    if system:
        filtered = [f for f in pool if f.get("system") == system]
        if len(filtered) >= 4:
            pool = filtered

    all_flags = _red_flags_with_ids()
    selected = safe_sample(pool, count)
    output = []
    for flag in selected:
        options = [flag["action"]] + _red_flag_distractors(flag, all_flags, 3)
        indexed = list(enumerate(options))
        random.shuffle(indexed)
        shuffled_options = [opt for _, opt in indexed]
        correct_index = next(
            i for i, (orig, _) in enumerate(indexed) if orig == 0
        )
        output.append({
            "id": flag["id"],
            "finding": flag["finding"],
            "system": flag.get("system"),
            "priority": flag.get("priority"),
            "options": shuffled_options,
            "correct_index": correct_index,
        })
    return output


def check_red_flag_drill_answer(
    flag_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict:
    """Validate red flag drill answer with teaching feedback."""
    flag = _find_red_flag(flag_id)
    if not flag:
        return {
            "correct": False,
            "feedback": "Red flag not found.",
            "explanation": "",
            "clinical_why": "",
            "escalation_path": "",
        }

    correct_answer = flag["action"]
    if selected_option is not None:
        correct = selected_option.strip() == correct_answer.strip()
    else:
        correct = False

    return {
        "correct": correct,
        "feedback": (
            "Correct — appropriate immediate nursing action!"
            if correct
            else f"Incorrect. Immediate action required: {correct_answer}"
        ),
        "explanation": _red_flag_explanation(flag),
        "clinical_why": _red_flag_clinical_why(flag),
        "correct_answer": correct_answer,
        "escalation_path": _red_flag_escalation_path(flag),
        "finding": flag["finding"],
        "system": flag.get("system"),
        "priority": flag.get("priority"),
    }


def get_vital_signs() -> dict:
    return _data().get("vital_signs", {})


def get_pain_assessment() -> dict:
    return _data().get("pain_assessment", {})


def get_interview_techniques() -> list[dict]:
    return _data().get("interview_techniques", [])


def get_skills() -> list[dict]:
    return _data().get("skills", [])


def get_skill(skill_id: str) -> Optional[dict]:
    return next((s for s in get_skills() if s["id"] == skill_id), None)


def get_practice_questions(
    count: int = 10,
    mode: str = "mixed",
    system: Optional[str] = None,
) -> list[dict]:
    """NCLEX-style practice questions with shuffled options."""
    pool = list(_data().get("practice_questions", []))

    if system:
        pool = [q for q in pool if q.get("system") == system]

    if mode == "priority":
        pool = [q for q in pool if "priority" in q.get("question", "").lower()
                or "first" in q.get("question", "").lower()
                or "immediate" in q.get("question", "").lower()]
        if not pool:
            pool = list(_data().get("practice_questions", []))
    elif mode == "red_flags":
        pool = [q for q in pool if q.get("system") in (
            "neurological", "cardiovascular", "respiratory", "gastrointestinal"
        )]

    selected = safe_sample(pool, count)
    output = []
    for q in selected:
        item = dict(q)
        # Shuffle options per question; track new correct_index for practice/check API
        if "options" in item and "correct_index" in item:
            indexed = list(enumerate(item["options"]))
            random.shuffle(indexed)
            item["options"] = [opt for _, opt in indexed]
            item["correct_index"] = next(
                i for i, (orig, _) in enumerate(indexed) if orig == q["correct_index"]
            )
        output.append(item)
    return output


def _find_question(question_id: str) -> Optional[dict]:
    """Look up question in practice pool or shuffled session by id."""
    return next((x for x in _data().get("practice_questions", []) if x["id"] == question_id), None)


def check_practice_answer(
    question_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict:
    """Validate a practice answer and return teaching feedback."""
    q = _find_question(question_id)
    if not q:
        return {
            "correct": False,
            "feedback": "Question not found.",
            "explanation": "",
            "clinical_why": "",
        }

    correct_answer = q["options"][q["correct_index"]]
    if selected_option is not None:
        correct = selected_option.strip() == correct_answer.strip()
    else:
        correct = selected_index == q["correct_index"]

    return {
        "correct": correct,
        "feedback": "Correct!" if correct else f"Incorrect. The best answer is: {correct_answer}",
        "explanation": q.get("explanation", ""),
        "clinical_why": q.get("clinical_why", ""),
        "correct_answer": correct_answer,
        "nclex_category": q.get("nclex_category"),
        "system": q.get("system"),
    }


def get_special_populations() -> list[dict]:
    return _data().get("special_populations", [])


def get_special_population(pop_id: str) -> Optional[dict]:
    return next((p for p in get_special_populations() if p["id"] == pop_id), None)


def get_assessment_checklists() -> list[dict]:
    return _data().get("assessment_checklists", [])


def get_assessment_checklist(checklist_id: str) -> Optional[dict]:
    return next((c for c in get_assessment_checklists() if c["id"] == checklist_id), None)


def get_soap_exercises() -> list[dict]:
    return _data().get("soap_exercises", [])


def get_soap_exercise(exercise_id: str) -> Optional[dict]:
    return next((e for e in get_soap_exercises() if e["id"] == exercise_id), None)


def get_sbar_exercises() -> list[dict]:
    return _data().get("sbar_exercises", [])


def get_sbar_exercise(exercise_id: str) -> Optional[dict]:
    return next((e for e in get_sbar_exercises() if e["id"] == exercise_id), None)


# ── SOAP validation rubric ────────────────────────────────────────────────────

_MIN_SECTION_CHARS = 40
_PASS_SCORE = 70

_SUBJECTIVE_MARKERS = re.compile(
    r"\b(patient reports?|states?|denies?|complains?|feels?|says?|history of|"
    r"describes?|rates?|admits?)\b",
    re.I,
)
_OBJECTIVE_MARKERS = re.compile(
    r"\b(vitals?|bp\b|hr\b|rr\b|spo2|temp|temperature|observed|auscult|palp|"
    r"inspected|alert|oriented|mmhg|bpm|°f|/10)\b",
    re.I,
)
_ASSESSMENT_MARKERS = re.compile(
    r"\b(related to|r/t|secondary to|risk for|impaired|ineffective|acute|"
    r"exacerbation|concern|suspect|likely|diagnosis|overload|infection|"
    r"distress|deficit)\b",
    re.I,
)
_PLAN_MARKERS = re.compile(
    r"\b(notify|monitor|administer|assess|reassess|escalat|order|implement|"
    r"prepare|maintain|document|educate|apply|elevate|restrict|protocol|"
    r"per order|q\d+|continuous)\b",
    re.I,
)
_NUMBER_PATTERN = re.compile(r"\d+(?:\.\d+)?(?:\s*%|/\d+|×\d+)?|\d+/\d+")


def _finding_tokens(findings: dict) -> set[str]:
    """Extract measurable tokens from clinical findings for coverage checks."""
    tokens: set[str] = set()
    for value in findings.values():
        text = str(value).lower()
        for match in _NUMBER_PATTERN.findall(text):
            tokens.add(match.replace(" ", ""))
        for word in re.findall(r"[a-z]{4,}", text):
            if word not in {"patient", "with", "bilateral", "approximately"}:
                tokens.add(word)
    return tokens


def _keyword_coverage(text: str, tokens: set[str]) -> float:
    if not tokens:
        return 1.0
    lower = text.lower()
    hits = sum(1 for t in tokens if t in lower.replace(" ", ""))
    return min(1.0, hits / max(3, len(tokens) * 0.35))


def _length_score(text: str) -> float:
    n = len(text.strip())
    if n < 15:
        return 0.0
    if n < _MIN_SECTION_CHARS:
        return 40.0 + (n / _MIN_SECTION_CHARS) * 30.0
    if n < 120:
        return 70.0 + min(30.0, (n - _MIN_SECTION_CHARS) / 2)
    return 100.0


def _score_soap_section(
    text: str,
    section: str,
    findings_tokens: set[str],
) -> tuple[float, list[str], list[str]]:
    """Return score, feedback items, and strengths for one SOAP section."""
    feedback: list[str] = []
    strengths: list[str] = []
    stripped = text.strip()
    score = _length_score(stripped)

    if not stripped:
        return 0.0, [f"{section.title()}: section is empty — add content before submitting."], strengths

    if section == "subjective":
        if not _SUBJECTIVE_MARKERS.search(stripped):
            feedback.append(
                "Subjective: include patient-reported data (e.g., 'patient reports', 'states', 'denies')."
            )
            score -= 15
        else:
            strengths.append("Subjective uses appropriate patient-reported language.")
        if _OBJECTIVE_MARKERS.search(stripped) and not _SUBJECTIVE_MARKERS.search(stripped):
            feedback.append(
                "Subjective: vitals and exam findings belong in Objective, not Subjective."
            )
            score -= 20

    elif section == "objective":
        coverage = _keyword_coverage(stripped, findings_tokens)
        score = score * 0.5 + coverage * 50
        if coverage < 0.4:
            feedback.append(
                "Objective: incorporate more measurable findings from the case (vitals, exam data)."
            )
        else:
            strengths.append("Objective documents key findings from the case.")
        if _SUBJECTIVE_MARKERS.search(stripped) and not _OBJECTIVE_MARKERS.search(stripped):
            feedback.append(
                "Objective: use measurable, observable data — move patient quotes to Subjective."
            )
            score -= 15
        elif _SUBJECTIVE_MARKERS.search(stripped):
            feedback.append(
                "Objective: minimize interpretive or patient-reported language; document what you measure/observe."
            )
            score -= 10

    elif section == "assessment":
        if not _ASSESSMENT_MARKERS.search(stripped):
            feedback.append(
                "Assessment: link data to a nursing diagnosis or clinical impression (e.g., 'acute pain r/t…')."
            )
            score -= 20
        else:
            strengths.append("Assessment synthesizes findings into a clinical impression.")

    elif section == "plan":
        if not _PLAN_MARKERS.search(stripped):
            feedback.append(
                "Plan: include actionable nursing interventions, monitoring, and provider notification."
            )
            score -= 25
        else:
            strengths.append("Plan includes concrete nursing actions.")

    return max(0.0, min(100.0, round(score, 1))), feedback, strengths


def validate_soap_submission(
    exercise_id: str,
    subjective: str,
    objective: str,
    assessment: str,
    plan: str,
) -> dict:
    """Rubric-based SOAP feedback — checks section separation, coverage, and completeness."""
    exercise = get_soap_exercise(exercise_id)
    if not exercise:
        return {
            "valid": False,
            "error": "Exercise not found",
            "exercise_id": exercise_id,
        }

    findings = exercise.get("findings", {})
    tokens = _finding_tokens(findings)
    sections = {
        "subjective": subjective,
        "objective": objective,
        "assessment": assessment,
        "plan": plan,
    }

    section_scores: dict[str, float] = {}
    all_feedback: list[str] = []
    all_strengths: list[str] = []
    rubric: list[dict] = []

    for name, text in sections.items():
        sc, fb, st = _score_soap_section(text, name, tokens)
        section_scores[name] = sc
        all_feedback.extend(fb)
        all_strengths.extend(st)
        rubric.append({
            "section": name,
            "score": sc,
            "criteria": _rubric_criteria_for_section(name),
        })

    overall = round(sum(section_scores.values()) / len(section_scores), 1)
    passed = overall >= _PASS_SCORE

    if passed and not all_strengths:
        all_strengths.append("All SOAP sections meet minimum documentation standards.")

    return {
        "valid": True,
        "exercise_id": exercise_id,
        "exercise_title": exercise.get("title"),
        "overall_score": overall,
        "passed": passed,
        "pass_threshold": _PASS_SCORE,
        "section_scores": section_scores,
        "feedback": all_feedback,
        "strengths": all_strengths,
        "rubric": rubric,
        "documentation_tips": exercise.get("documentation_tips", []),
        "model_soap": exercise.get("model_soap") if passed else None,
    }


def _rubric_criteria_for_section(section: str) -> list[str]:
    criteria = {
        "subjective": [
            "Patient-reported symptoms, history, and quotes",
            "No vitals or exam measurements",
            "Adequate detail for the chief concern",
        ],
        "objective": [
            "Measurable vitals and exam findings from the case",
            "Factual, observable language only",
            "Coverage of key findings provided",
        ],
        "assessment": [
            "Nursing diagnosis or clinical impression",
            "Links subjective + objective data",
            "Identifies priority problems",
        ],
        "plan": [
            "Independent nursing interventions",
            "Provider notification when indicated",
            "Monitoring and reassessment",
        ],
    }
    return criteria.get(section, [])


# ── Flashcards (normal vs abnormal) + SRS ─────────────────────────────────────

SRS_INTERVALS = [1, 3, 7, 14, 30, 60]


def get_flashcards() -> list[dict]:
    return _data().get("flashcards", [])


def get_flashcard(card_id: str) -> Optional[dict]:
    return next((c for c in get_flashcards() if c["id"] == card_id), None)


def _public_flashcard(card: dict, state: Optional[FlashcardState] = None, due: bool = True) -> dict:
    today = date.today()
    reps = state.repetitions if state else 0
    next_review = state.next_review if state else None
    is_due = next_review is None or next_review <= today
    return {
        "id": card["id"],
        "front": card.get("front", ""),
        "system": card.get("system", ""),
        "system_name": card.get("system_name", ""),
        "type": card.get("type", "normal_vs_abnormal"),
        "normal": card.get("normal", ""),
        "abnormal": card.get("abnormal", ""),
        "abnormal_action": card.get("abnormal_action", ""),
        "clinical_why": card.get("clinical_why", ""),
        "due": is_due if state else True,
        "repetitions": reps,
        "interval_days": state.interval_days if state else 0,
        "next_review": next_review.isoformat() if next_review else None,
    }


async def _load_fc_state_map(session: AsyncSession) -> dict[str, FlashcardState]:
    result = await session.execute(
        select(FlashcardState).where(FlashcardState.module_id == MODULE_ID)
    )
    return {s.card_key: s for s in result.scalars().all()}


async def _get_or_create_fc_state(
    session: AsyncSession, card_id: str, state_map: Optional[dict[str, FlashcardState]] = None
) -> FlashcardState:
    if state_map and card_id in state_map:
        return state_map[card_id]
    result = await session.execute(
        select(FlashcardState).where(
            FlashcardState.module_id == MODULE_ID,
            FlashcardState.card_key == card_id,
        )
    )
    state = result.scalar_one_or_none()
    if not state:
        state = FlashcardState(
            module_id=MODULE_ID,
            card_key=card_id,
            ease_factor=2.5,
            interval_days=0,
            repetitions=0,
            next_review=date.today(),
        )
        session.add(state)
        await session.flush()
        if state_map is not None:
            state_map[card_id] = state
    return state


async def get_due_flashcards(
    session: AsyncSession,
    count: int = 20,
    system: Optional[str] = None,
    due_only: bool = False,
) -> list[dict]:
    """SRS deck — due cards first, then new cards."""
    pool = list(get_flashcards())
    if system:
        pool = [c for c in pool if c.get("system") == system]
    random.shuffle(pool)

    state_map = await _load_fc_state_map(session)
    today = date.today()
    enriched: list[dict] = []
    for card in pool:
        state = state_map.get(card["id"])
        is_due = state is None or state.next_review is None or state.next_review <= today
        if due_only and not is_due:
            continue
        enriched.append(_public_flashcard(card, state, is_due))

    enriched.sort(key=lambda c: (0 if c["due"] else 1, -c["repetitions"]))
    selected = enriched[:count]
    for item in selected:
        if item["id"] not in state_map:
            await _get_or_create_fc_state(session, item["id"], state_map)
    return selected


async def record_flashcard_review(
    session: AsyncSession, card_id: str, quality: int
) -> dict:
    """
    Record SRS review. quality: 0=again, 1=hard, 2=good, 3=easy
    (Need Review → 0, Know It → 2 in UI)
    """
    card = get_flashcard(card_id)
    if not card:
        return {"error": "Card not found", "card_id": card_id}

    state = await _get_or_create_fc_state(session, card_id)
    today = date.today()

    if quality == 0:
        state.repetitions = 0
        state.interval_days = 1
        state.incorrect_count += 1
        state.ease_factor = max(1.3, state.ease_factor - 0.2)
    else:
        state.correct_count += 1
        state.repetitions += 1
        idx = min(state.repetitions - 1, len(SRS_INTERVALS) - 1)
        state.interval_days = SRS_INTERVALS[idx]
        if quality == 3:
            state.interval_days = int(state.interval_days * 1.5)
            state.ease_factor = min(3.0, state.ease_factor + 0.1)
        elif quality == 1:
            state.interval_days = max(1, state.interval_days // 2)

    state.next_review = today + timedelta(days=state.interval_days)
    state.last_reviewed = datetime.utcnow()
    await session.flush()

    return {
        "card_id": card_id,
        "repetitions": state.repetitions,
        "interval_days": state.interval_days,
        "next_review": state.next_review.isoformat(),
        "ease_factor": round(state.ease_factor, 2),
    }


async def get_flashcard_stats(session: AsyncSession) -> dict:
    """SRS statistics for assessment flashcards."""
    cards = get_flashcards()
    state_map = await _load_fc_state_map(session)
    today = date.today()
    due_count = 0
    mastered = 0

    for card in cards:
        state = state_map.get(card["id"])
        if not state:
            due_count += 1
            continue
        if state.next_review is None or state.next_review <= today:
            due_count += 1
        if state.repetitions >= 4:
            mastered += 1

    return {
        "total": len(cards),
        "due_today": due_count,
        "mastered": mastered,
        "new": max(0, len(cards) - len(state_map)),
    }


def build_flashcards_markdown(system: Optional[str] = None) -> str:
    """Markdown export for normal vs abnormal flashcard deck."""
    cards = get_flashcards()
    if system:
        cards = [c for c in cards if c.get("system") == system]
    lines = ["# The Ward — Health Assessment Flashcards\n", "Normal vs. abnormal findings by body system.\n"]
    for i, c in enumerate(cards, 1):
        lines += [
            f"## Card {i} — {c.get('system_name', c.get('system', ''))} (`{c.get('id', '')}`)",
            f"**Front:** {c.get('front', '')}",
            f"**Normal:** {c.get('normal', '')}",
            f"**Abnormal:** {c.get('abnormal', '')}",
            f"**Action:** {c.get('abnormal_action', '')}",
            f"**Clinical:** {c.get('clinical_why', '')}",
            "",
        ]
    return "\n".join(lines)


def get_assess_next_scenarios(count: int = 4) -> list[dict]:
    """Scenario-based 'What would you assess next?' exercises."""
    pool = list(_data().get("assess_next_scenarios", []))
    selected = safe_sample(pool, count)
    output = []
    for s in selected:
        item = dict(s)
        if "options" in item and "correct_index" in item:
            indexed = list(enumerate(item["options"]))
            random.shuffle(indexed)
            item["options"] = [opt for _, opt in indexed]
            item["correct_index"] = next(
                i for i, (orig, _) in enumerate(indexed) if orig == s["correct_index"]
            )
        output.append(item)
    return output


def _find_scenario(scenario_id: str) -> Optional[dict]:
    return next(
        (x for x in _data().get("assess_next_scenarios", []) if x["id"] == scenario_id),
        None,
    )


def check_assess_next_answer(
    scenario_id: str,
    selected_index: int,
    selected_option: Optional[str] = None,
) -> dict:
    """Validate assess-next scenario answer with teaching feedback."""
    s = _find_scenario(scenario_id)
    if not s:
        return {
            "correct": False,
            "feedback": "Scenario not found.",
            "explanation": "",
            "clinical_why": "",
        }

    correct_answer = s["options"][s["correct_index"]]
    if selected_option is not None:
        correct = selected_option.strip() == correct_answer.strip()
    else:
        correct = selected_index == s["correct_index"]

    return {
        "correct": correct,
        "feedback": "Correct!" if correct else f"Not the best next step. Priority: {correct_answer}",
        "explanation": s.get("explanation", ""),
        "clinical_why": s.get("clinical_why", ""),
        "correct_answer": correct_answer,
        "scenario_title": s.get("title"),
    }


def get_module_summary() -> dict[str, Any]:
    d = _data()
    systems = d.get("body_systems", [])
    return {
        "sequence_steps": len(d.get("head_to_toe_sequence", [])),
        "body_systems": len(systems),
        "red_flags": len(d.get("red_flags_master", [])),
        "skills": len(d.get("skills", [])),
        "practice_total": len(d.get("practice_questions", [])),
        "interview_techniques": len(d.get("interview_techniques", [])),
        "special_populations": len(d.get("special_populations", [])),
        "checklists": len(d.get("assessment_checklists", [])),
        "soap_exercises": len(d.get("soap_exercises", [])),
        "sbar_exercises": len(d.get("sbar_exercises", [])),
        "flashcards": len(d.get("flashcards", [])),
        "assess_next_scenarios": len(d.get("assess_next_scenarios", [])),
        "items_total": ITEMS_TOTAL,
    }