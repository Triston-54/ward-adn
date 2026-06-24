"""Microbiology module — infection control, pathogens, scenarios, practice."""
import random
from typing import Any, Optional

from app.models import SourceRef
from app.services.content_loader import load_content, safe_sample

MODULE_ID = "microbiology"
ITEMS_TOTAL = 47


def _data() -> dict:
    return load_content("microbiology.json")


def default_source() -> SourceRef:
    sources = load_content("sources.json")
    s = sources.get("microbiology", {})
    return SourceRef(
        title=s.get("title", "Open RN — Microbiology"),
        url=s.get("url", "https://openrn.org/"),
        citation=s.get("citation", "Open RN OER Textbook"),
        verified_date=s.get("verified_date", "2026-06"),
    )


def get_infection_chain() -> list[dict]:
    return _data().get("infection_chain", [])


def get_microbe_classification() -> list[dict]:
    return _data().get("microbe_classification", [])


def get_pathogens() -> list[dict]:
    return _data().get("healthcare_pathogens", [])


def get_concepts() -> list[dict]:
    return _data().get("concepts", [])


def get_gram_stain() -> dict:
    d = _data()
    return {
        "procedure": d.get("gram_stain_procedure", []),
        "interpretation": d.get("gram_stain_interpretation", {}),
    }


def get_ppe_guide() -> dict:
    return _data().get("ppe_guide", {})


def get_hand_hygiene() -> dict:
    return _data().get("hand_hygiene", {})


def get_hai_types() -> list[dict]:
    return _data().get("hai_types", [])


def get_chain_interventions() -> dict[str, list[dict]]:
    """Interventions keyed by chain link id for the visual builder."""
    return _data().get("chain_interventions", {})


def evaluate_chain_break(link_id: str, intervention_id: str) -> dict:
    """Check if selected intervention correctly breaks the chosen chain link."""
    interventions = get_chain_interventions().get(link_id, [])
    chosen = next((i for i in interventions if i["id"] == intervention_id), None)
    if not chosen:
        return {
            "correct": False,
            "feedback": "Invalid selection. Choose a chain link and intervention.",
            "clinical_why": "",
        }
    chain = {c["id"]: c for c in get_infection_chain()}
    link_name = chain.get(link_id, {}).get("name", link_id)
    if chosen.get("correct"):
        return {
            "correct": True,
            "feedback": chosen["explanation"],
            "clinical_why": chosen.get(
                "clinical_why",
                f"Breaking the {link_name} link prevents pathogen spread — core RN practice.",
            ),
            "link": link_name,
            "intervention": chosen["label"],
        }
    return {
        "correct": False,
        "feedback": chosen["explanation"],
        "clinical_why": chosen.get(
            "clinical_why",
            f"This action does not primarily break the {link_name} link. Review the chain of infection.",
        ),
        "link": link_name,
        "intervention": chosen["label"],
    }


def get_break_chain_scenarios(count: int = 5) -> list[dict]:
    scenarios = _data().get("break_chain_scenarios", [])
    return safe_sample(scenarios, count)


def get_what_if_scenarios(count: int = 3) -> list[dict]:
    scenarios = _data().get("what_if_scenarios", [])
    return safe_sample(scenarios, count)


def get_practice_questions(
    count: int = 10,
    mode: str = "mixed",
) -> list[dict]:
    """NCLEX-style + application-based questions."""
    d = _data()
    nclex = d.get("practice_questions", [])
    application = d.get("application_questions", [])

    if mode == "nclex":
        pool = nclex
    elif mode == "application":
        pool = application
    else:
        pool = nclex + application

    selected = safe_sample(pool, count)
    output = []
    for q in selected:
        item = dict(q)
        item["type"] = "application" if q in application else "nclex"
        # Shuffle MC options
        if "options" in item and "correct_index" in item:
            indexed = list(enumerate(item["options"]))
            random.shuffle(indexed)
            item["options"] = [opt for _, opt in indexed]
            item["correct_index"] = next(
                i for i, (orig, _) in enumerate(indexed) if orig == q["correct_index"]
            )
        output.append(item)
    return output


def get_break_points() -> list[str]:
    return _data().get("break_points", [])


def get_pathogen_flashcards(count: Optional[int] = None) -> list[dict]:
    """Simple flip-card data from healthcare pathogens — no SRS backend."""
    pathogens = list(get_pathogens())
    random.shuffle(pathogens)
    if count is not None:
        pathogens = pathogens[: min(count, len(pathogens))]
    cards = []
    for p in pathogens:
        cards.append({
            "id": p["name"].lower().replace(" ", "-"),
            "front": p["name"],
            "back": p.get("full_name", ""),
            "precautions": p.get("precautions", ""),
            "nursing_action": p.get("nursing_action", ""),
            "clinical_why": p.get("clinical_why", ""),
            "type": p.get("type", ""),
            "source": p.get("source"),
        })
    return cards


def build_clipboard_text() -> str:
    """Plain-text study sheet: infection chain, break points, and key pathogens."""
    d = _data()
    src = default_source()
    lines = [
        "THE WARD — MICROBIOLOGY STUDY SHEET",
        "=" * 50,
        "",
        "CHAIN OF INFECTION",
        "-" * 30,
    ]
    for i, link in enumerate(d.get("infection_chain", []), 1):
        lines += [
            f"{i}. {link['name']}",
            f"   {link['description']}",
            f"   Break it: {link['intervention']}",
            "",
        ]

    lines += ["KEY BREAK POINTS", "-" * 30]
    for bp in d.get("break_points", []):
        lines.append(f"• {bp}")
    lines.append("")

    lines += ["HEALTHCARE PATHOGENS", "-" * 30]
    for i, p in enumerate(d.get("healthcare_pathogens", []), 1):
        lines += [
            f"{i}. {p['name']} ({p.get('type', '')})",
            f"   Precautions: {p.get('precautions', '')}",
            f"   Nursing: {p.get('nursing_action', '')}",
            f"   Clinical: {p.get('clinical_why', '')}",
            "",
        ]

    lines.append(f"Source: {src.citation} · {src.verified_date}")
    return "\n".join(lines)


def build_study_sheet_html(title: str = "Microbiology Study Sheet") -> str:
    """Printable HTML study sheet — infection chain, break points, pathogens."""
    d = _data()
    src = default_source()

    chain_rows = ""
    for i, link in enumerate(d.get("infection_chain", []), 1):
        chain_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{link['name']}</strong></td>
            <td>{link['description']}</td>
            <td class="intervention">{link['intervention']}</td>
        </tr>"""

    break_items = "".join(
        f"<li>{bp}</li>" for bp in d.get("break_points", [])
    )

    pathogen_rows = ""
    for i, p in enumerate(d.get("healthcare_pathogens", []), 1):
        pathogen_rows += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{p['name']}</strong><br><span class="sub">{p.get('full_name', '')}</span></td>
            <td>{p.get('type', '')}</td>
            <td>{p.get('precautions', '')}</td>
            <td class="clinical">{p.get('nursing_action', '')}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>The Ward — {title}</title>
<style>
  body {{ font-family: Georgia, serif; margin: 2cm; color: #111; }}
  h1 {{ color: #0f172a; border-bottom: 2px solid #34d399; padding-bottom: 8px; }}
  h2 {{ color: #065f46; font-size: 14px; margin-top: 28px; border-bottom: 1px solid #a7f3d0; padding-bottom: 4px; }}
  .meta {{ color: #666; font-size: 12px; margin-bottom: 24px; }}
  .break-points {{ background: #ecfdf5; border-left: 3px solid #34d399; padding: 12px 16px; margin: 16px 0; font-size: 12px; }}
  .break-points ul {{ margin: 8px 0 0; padding-left: 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 16px; }}
  th {{ background: #064e3b; color: white; padding: 8px; text-align: left; }}
  td {{ padding: 6px 8px; border-bottom: 1px solid #ddd; vertical-align: top; }}
  tr:nth-child(even) {{ background: #f0fdf4; }}
  .clinical {{ color: #475569; font-size: 10px; }}
  .intervention {{ color: #047857; font-size: 10px; }}
  .sub {{ color: #64748b; font-size: 9px; }}
  @media print {{ body {{ margin: 1cm; }} }}
</style>
</head><body>
<h1>The Ward — Microbiology</h1>
<p class="meta">{title} · {len(d.get('infection_chain', []))} chain links · {len(d.get('healthcare_pathogens', []))} pathogens · Source: {src.citation} · New River CTC ADN</p>

<h2>Chain of Infection</h2>
<table>
  <thead><tr><th>#</th><th>Link</th><th>Description</th><th>Break It</th></tr></thead>
  <tbody>{chain_rows}</tbody>
</table>

<h2>Key Break Points</h2>
<div class="break-points"><ul>{break_items}</ul></div>

<h2>Healthcare Pathogens</h2>
<table>
  <thead><tr><th>#</th><th>Pathogen</th><th>Type</th><th>Precautions</th><th>Nursing Action</th></tr></thead>
  <tbody>{pathogen_rows}</tbody>
</table>

<p class="meta">Generated by The Ward — local-first nursing study suite</p>
</body></html>"""


def build_flashcards_markdown() -> str:
    """Markdown flashcard export for pathogens."""
    lines = ["# The Ward — Microbiology Pathogen Flashcards\n"]
    for i, p in enumerate(get_pathogens(), 1):
        lines += [
            f"## Card {i}",
            f"**Front:** {p['name']}",
            f"**Back:** {p.get('full_name', '')}",
            f"**Precautions:** {p.get('precautions', '')}",
            f"**Nursing:** {p.get('nursing_action', '')}",
            f"**Clinical:** {p.get('clinical_why', '')}",
            "",
        ]
    return "\n".join(lines)


def get_module_summary() -> dict[str, Any]:
    d = _data()
    return {
        "chain_links": len(d.get("infection_chain", [])),
        "pathogens": len(d.get("healthcare_pathogens", [])),
        "concepts": len(d.get("concepts", [])),
        "practice_total": len(d.get("practice_questions", []))
        + len(d.get("application_questions", [])),
        "scenarios": len(d.get("break_chain_scenarios", []))
        + len(d.get("what_if_scenarios", [])),
        "break_points": len(d.get("break_points", [])),
        "items_total": ITEMS_TOTAL,
    }