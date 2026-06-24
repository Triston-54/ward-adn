#!/usr/bin/env python3
"""
Build static HTML pages for The Ward ADN nursing study site.

Reads Jinja templates from app/templates/, renders with static context,
and outputs to project root: index.html, modules/*.html, nclex-prep.html
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "app" / "templates"
CONTENT_DIR = ROOT / "data" / "content"
OUTPUT_DIR = ROOT


def load_json(filename: str) -> dict[str, Any]:
    path = CONTENT_DIR / filename
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def count_items(*values: int) -> int:
    return sum(values)


# ── Module summaries from JSON ───────────────────────────────────────────────

def count_terminology_terms() -> int:
    """Merge terminology.json + terminology_terms.json (same logic as data-api.js)."""
    base = load_json("terminology.json")
    extra = load_json("terminology_terms.json")
    seen: set[str] = set()
    count = 0
    for t in base.get("terms", []) + extra.get("terms", []):
        key = str(t.get("term", "")).lower()
        if key and key not in seen:
            seen.add(key)
            count += 1
    return count


def summary_terminology() -> dict[str, Any]:
    d = load_json("terminology.json")
    term_count = count_terminology_terms()
    return {
        "term_count": term_count,
        "prefix_count": len(d.get("prefixes", [])),
        "suffix_count": len(d.get("suffixes", [])),
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": term_count + len(d.get("flashcards", [])),
    }


def summary_microbiology() -> dict[str, Any]:
    d = load_json("microbiology.json")
    return {
        "chain_links": len(d.get("infection_chain", [])),
        "pathogens": len(d.get("healthcare_pathogens", [])),
        "concepts": len(d.get("concepts", [])),
        "practice_count": len(d.get("practice_questions", [])) + len(d.get("application_questions", [])),
        "items_total": 47,
    }


def summary_dosage() -> dict[str, Any]:
    d = load_json("dosage.json")
    pharm = load_json("dosage_drug_classes.json")
    classes = pharm.get("drug_classes", pharm) if isinstance(pharm, dict) else []
    if isinstance(classes, dict):
        classes = list(classes.values())
    return {
        "calculator_count": len(d.get("calculators", d.get("calculation_types", []))),
        "drug_class_count": len(classes) if isinstance(classes, list) else 0,
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": 53,
    }


def summary_assessment() -> dict[str, Any]:
    d = load_json("assessment.json")
    return {
        "system_count": len(d.get("body_systems", d.get("head_to_toe_systems", d.get("systems", [])))),
        "red_flag_count": len(d.get("red_flags_master", d.get("red_flags", []))),
        "checklist_count": len(d.get("assessment_checklists", d.get("checklists", []))),
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": 132,
    }


def summary_mental_health() -> dict[str, Any]:
    d = load_json("mental_health.json")
    return {
        "communication_count": len(d.get("therapeutic_communication", [])),
        "safety_flag_count": len(d.get("safety_risk_flags", [])),
        "drill_count": len(d.get("safety_priority_drill", [])),
        "items_total": 55,
    }


def summary_pathophysiology() -> dict[str, Any]:
    d = load_json("pathophysiology.json")
    return {
        "concepts_count": len(d.get("core_concepts", [])),
        "disease_count": len(d.get("disease_processes", [])),
        "compare_count": len(d.get("compare_contrast_pairs", [])),
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": 76,
    }


def summary_maternal_child() -> dict[str, Any]:
    d = load_json("maternal_child.json")
    return {
        "pregnancy_count": len(d.get("pregnancy_stages", [])),
        "labor_count": len(d.get("labor_delivery", [])),
        "postpartum_count": len(d.get("postpartum_newborn", [])),
        "pediatric_count": len(d.get("pediatric_essentials", [])),
        "safety_flag_count": len(d.get("safety_red_flags", [])),
        "practice_count": len(d.get("practice_questions", [])),
        "flashcard_count": len(d.get("flashcards", [])),
        "items_total": count_items(
            len(d.get("pregnancy_stages", [])),
            len(d.get("labor_delivery", [])),
            len(d.get("postpartum_newborn", [])),
            len(d.get("pediatric_essentials", [])),
            len(d.get("safety_red_flags", [])),
            len(d.get("complications_drill", [])),
            len(d.get("flashcards", [])),
            len(d.get("practice_questions", [])),
        ),
    }


def summary_maternal_newborn() -> dict[str, Any]:
    d = load_json("maternal_child.json")
    return {
        "antepartum_count": len(d.get("pregnancy_stages", [])),
        "intrapartum_count": len(d.get("labor_delivery", [])),
        "postpartum_count": len(d.get("postpartum_newborn", [])),
        "safety_count": len([f for f in d.get("safety_red_flags", []) if "fetal" in str(f).lower() or "maternal" in str(f).lower() or "ob" in str(f).lower()]) or len(d.get("safety_red_flags", [])),
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": count_items(
            len(d.get("pregnancy_stages", [])),
            len(d.get("labor_delivery", [])),
            len(d.get("postpartum_newborn", [])),
        ),
    }


def summary_pediatrics() -> dict[str, Any]:
    d = load_json("maternal_child.json")
    peds = d.get("pediatric_essentials", [])
    return {
        "milestone_count": len([p for p in peds if "milestone" in str(p.get("title", "")).lower() or "development" in str(p.get("category", "")).lower()]) or len(peds),
        "growth_count": len([p for p in peds if "growth" in str(p.get("title", "")).lower()]) or max(1, len(peds) // 3),
        "immunization_count": len(d.get("immunization_schedule", d.get("immunizations", []))) or 12,
        "safety_count": len([p for p in peds if "safety" in str(p.get("title", "")).lower()]),
        "practice_count": len([q for q in d.get("practice_questions", []) if "ped" in str(q).lower() or "child" in str(q).lower()]) or len(d.get("practice_questions", [])),
        "items_total": len(peds),
    }


def summary_med_surg() -> dict[str, Any]:
    d = load_json("med_surg.json")
    return {
        "body_system_count": len(d.get("body_systems", [])),
        "procedure_count": len(d.get("procedures", [])),
        "priority_count": len(d.get("priority_drill", [])),
        "flashcard_count": len(d.get("flashcards", [])),
        "practice_count": len(d.get("practice_questions", [])),
        "items_total": count_items(
            len(d.get("core_concepts", [])),
            len(d.get("body_systems", [])),
            len(d.get("procedures", [])),
            len(d.get("flashcards", [])),
            len(d.get("practice_questions", [])),
        ),
    }


DEFAULT_FLASHCARD_STATS = {"due_today": 0, "mastered": 0, "learning": 0, "total": 0}


def build_module_context(module_id: str) -> dict[str, Any]:
    """Minimal static context for legacy module templates (no database)."""
    builder = SUMMARY_BUILDERS.get(module_id)
    summary = builder() if builder else {}
    ctx: dict[str, Any] = {
        "stats": build_static_stats(),
        "module_progress": None,
        "summary": summary,
        "flashcard_stats": DEFAULT_FLASHCARD_STATS,
    }

    if module_id == "terminology":
        d = load_json("terminology.json")
        ctx.update({
            "prefixes": d.get("prefixes", []),
            "roots": d.get("roots", []),
            "suffixes": d.get("suffixes", []),
            "term_count": count_terminology_terms(),
        })
    elif module_id == "assessment":
        d = load_json("assessment.json")
        ctx.update({
            "head_to_toe": d.get("head_to_toe_sequence", d.get("head_to_toe", [])),
            "body_systems": d.get("body_systems", d.get("head_to_toe_systems", d.get("systems", []))),
            "red_flag_count": len(d.get("red_flags_master", d.get("red_flags", []))),
        })
    elif module_id == "mental_health":
        manifest = load_json("mental_health_manifest.json")
        ctx["tabs"] = [t for t in manifest.get("tabs", []) if t.get("status") == "implemented"]
    elif module_id == "pathophysiology":
        manifest = load_json("pathophysiology_manifest.json")
        ctx["tabs"] = [t for t in manifest.get("tabs", []) if t.get("status") == "implemented"]
    elif module_id == "maternal_child":
        manifest = load_json("maternal_child_manifest.json")
        ctx["manifest"] = manifest
        ctx["tabs"] = [t for t in manifest.get("tabs", []) if t.get("status") == "implemented"]

    return ctx


SUMMARY_BUILDERS = {
    "terminology": summary_terminology,
    "microbiology": summary_microbiology,
    "dosage": summary_dosage,
    "assessment": summary_assessment,
    "mental_health": summary_mental_health,
    "pathophysiology": summary_pathophysiology,
    "maternal_child": summary_maternal_child,
    "maternal_newborn": summary_maternal_newborn,
    "pediatrics": summary_pediatrics,
    "med_surg": summary_med_surg,
}


MODULE_LAUNCHERS = [
    {
        "module_id": "terminology",
        "name": "Medical Terminology",
        "description": "Word builder, flashcards, NCLEX practice",
        "url": "/modules/terminology.html",
        "accent": "border-l-ward-accent",
        "badge": "mvp",
    },
    {
        "module_id": "microbiology",
        "name": "Microbiology",
        "description": "Chain builder, break-chain scenarios, NCLEX practice",
        "url": "/modules/microbiology.html",
        "accent": "border-l-ward-success",
        "badge": "starter",
    },
    {
        "module_id": "dosage",
        "name": "Dosage & Pharmacology",
        "description": "Step-by-step calculators with derivations",
        "url": "/modules/dosage.html",
        "accent": "border-l-ward-warning",
        "badge": "starter",
    },
    {
        "module_id": "assessment",
        "name": "Health Assessment",
        "description": "Checklists, SOAP notes, special populations",
        "url": "/modules/assessment.html",
        "accent": "border-l-ward-purple",
        "badge": "mvp",
    },
    {
        "module_id": "pathophysiology",
        "name": "Pathophysiology",
        "description": "Disease cascades, compare/contrast, NCLEX practice",
        "url": "/modules/pathophysiology.html",
        "accent": "border-l-rose-400",
        "badge": "new",
    },
    {
        "module_id": "med_surg",
        "name": "Medical-Surgical Nursing",
        "description": "8 body systems, procedures, priority actions, NCLEX practice",
        "url": "/modules/med_surg.html",
        "accent": "border-l-sky-400",
        "badge": "new",
    },
    {
        "module_id": "maternal_newborn",
        "name": "Maternal-Newborn",
        "description": "Antepartum, intrapartum, postpartum, newborn care",
        "url": "/modules/maternal_newborn.html",
        "accent": "border-l-pink-400",
        "badge": "new",
    },
    {
        "module_id": "pediatrics",
        "name": "Pediatric Nursing",
        "description": "Milestones, growth, immunizations, safety",
        "url": "/modules/pediatrics.html",
        "accent": "border-l-emerald-400",
        "badge": "new",
    },
    {
        "module_id": "mental_health",
        "name": "Mental Health",
        "description": "Therapeutic communication, safety screening",
        "url": "/modules/mental-health.html",
        "accent": "border-l-ward-purple",
        "badge": "new",
    },
    {
        "module_id": "maternal_child",
        "name": "Maternal-Child (Legacy)",
        "description": "Combined OB and pediatrics module",
        "url": "/modules/maternal-child.html",
        "accent": "border-l-pink-300",
        "badge": None,
    },
]


def build_static_stats() -> dict[str, Any]:
    modules = []
    total_items = 0
    for launcher in MODULE_LAUNCHERS:
        if launcher["module_id"] == "maternal_child":
            continue  # legacy — don't double-count on dashboard
        builder = SUMMARY_BUILDERS.get(launcher["module_id"])
        summary = builder() if builder else {}
        items = summary.get("items_total", 0)
        total_items += items
        modules.append({**launcher, "summary": summary})

    return {
        "user": {"display_name": "ADN Student", "program": "ADN Nursing Program"},
        "modules": modules,
        "total_items": total_items,
        "overall_percentage": 0,
        "total_completed": 0,
    }


def build_nclex_stats() -> dict[str, Any]:
    d = load_json("nclex_prep.json")
    return {
        "total_questions": d.get("total_questions", 0),
        "categories": len(d.get("categories", [])),
        "ncj_steps": len(d.get("ncj_steps", [])),
    }


def make_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def prepare_template_source(template_name: str) -> str:
    """Swap base.html for base_static.html and strip server-only elements."""
    path = TEMPLATES_DIR / template_name
    source = path.read_text(encoding="utf-8")
    source = source.replace('{% extends "base.html" %}', '{% extends "base_static.html" %}')
    source = re.sub(r'\{% block topbar_actions %\}.*?<a href="/"', '{% block topbar_actions %}\n<a href="/index.html"', source, flags=re.DOTALL)
    source = source.replace('parent_url=\'/\'', "parent_url='/index.html'")
    source = source.replace('href="/"', 'href="/index.html"')
    # Remove socratic buttons
    source = re.sub(r'<button[^>]*openSocraticMode[^>]*>.*?</button>', '', source, flags=re.DOTALL)
    # Remove progress strips (static mode)
    source = re.sub(r'<div class="module-progress-strip[^"]*"[^>]*>.*?</div>\s*', '', source, flags=re.DOTALL)
    return source


def postprocess_html(html: str) -> str:
    """Fix URLs and remove socratic/pharmacy artifacts for static deployment."""
    replacements = [
        (r'href="/"', 'href="/index.html"'),
        (r"href='/", "href='/"),  # no-op anchor
        (r'href="/modules/terminology"', 'href="/modules/terminology.html"'),
        (r'href="/modules/microbiology"', 'href="/modules/microbiology.html"'),
        (r'href="/modules/dosage"', 'href="/modules/dosage.html"'),
        (r'href="/modules/assessment"', 'href="/modules/assessment.html"'),
        (r'href="/modules/mental-health"', 'href="/modules/mental-health.html"'),
        (r'href="/modules/pathophysiology"', 'href="/modules/pathophysiology.html"'),
        (r'href="/modules/maternal-child"', 'href="/modules/maternal-child.html"'),
        (r'href="/modules/med_surg"', 'href="/modules/med_surg.html"'),
        (r'href="/modules/maternal_newborn"', 'href="/modules/maternal_newborn.html"'),
        (r'href="/modules/pediatrics"', 'href="/modules/pediatrics.html"'),
        (r'href="/nclex-prep"', 'href="/nclex-prep.html"'),
        (r'href="/how-to-use"', 'href="/how-to-use.html"'),
        (r"location\.href='/modules/terminology", "location.href='/modules/terminology.html"),
        (r"location\.href='/modules/microbiology", "location.href='/modules/microbiology.html"),
        (r"location\.href='/modules/dosage", "location.href='/modules/dosage.html"),
        (r"location\.href='/modules/assessment", "location.href='/modules/assessment.html"),
        (r"location\.href='/modules/mental-health", "location.href='/modules/mental-health.html"),
        (r"location\.href='/modules/pathophysiology", "location.href='/modules/pathophysiology.html"),
        (r"location\.href='/modules/maternal-child", "location.href='/modules/maternal-child.html"),
        (r"location\.href='/modules/med_surg", "location.href='/modules/med_surg.html"),
        (r"location\.href='/nclex-prep", "location.href='/nclex-prep.html"),
    ]
    for pattern, repl in replacements:
        html = html.replace(pattern, repl) if not pattern.startswith("href='/") else html

    # Remove socratic script and FAB if present
    html = re.sub(r'<script[^>]*socratic\.js[^>]*></script>', '', html)
    html = re.sub(r'<button[^>]*socratic-fab[^>]*>.*?</button>', '', html, flags=re.DOTALL)
    html = re.sub(r'<button[^>]*btn-socratic[^>]*>.*?</button>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script src="https://unpkg.com/htmx[^"]*"></script>', '', html)

    # Ensure data-api.js is present (base_static already includes it)
    if 'data-api.js' not in html and 'ward.js' in html:
        html = html.replace(
            '<script src="/static/js/ward.js"></script>',
            '<script src="/static/js/data-api.js"></script>\n    <script src="/static/js/ward.js"></script>',
        )

    return html


def render_page(env: Environment, template_name: str, context: dict[str, Any], use_static_base: bool = False) -> str:
    if use_static_base:
        source = prepare_template_source(template_name)
        template = env.from_string(source)
    else:
        template = env.get_template(template_name)
    html = template.render(**context)
    return postprocess_html(html)


def write_output(rel_path: str, content: str) -> Path:
    out = OUTPUT_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out


# Page definitions: (output_path, template, module_id or None)
PAGES: list[tuple[str, str, str | None]] = [
    ("index.html", "dashboard_static.html", None),
    ("how-to-use.html", "how_to_use.html", None),
    ("nclex-prep.html", "nclex_prep.html", None),
    ("modules/terminology.html", "modules/terminology.html", "terminology"),
    ("modules/microbiology.html", "modules/microbiology.html", "microbiology"),
    ("modules/dosage.html", "modules/dosage.html", "dosage"),
    ("modules/assessment.html", "modules/assessment.html", "assessment"),
    ("modules/mental-health.html", "modules/mental_health.html", "mental_health"),
    ("modules/pathophysiology.html", "modules/pathophysiology.html", "pathophysiology"),
    ("modules/maternal-child.html", "modules/maternal_child.html", "maternal_child"),
    ("modules/med_surg.html", "modules/med_surg.html", "med_surg"),
    ("modules/maternal_newborn.html", "modules/maternal_newborn.html", "maternal_newborn"),
    ("modules/pediatrics.html", "modules/pediatrics.html", "pediatrics"),
]


def copy_data_content() -> None:
    """Ensure data/content is available at /data/content/ for static serving.

    Source and deploy path are the same directory (project root/data/content),
    so we only verify it exists — never rmtree the source tree.
    """
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    if not any(CONTENT_DIR.iterdir()):
        print(f"  Warning: {CONTENT_DIR.relative_to(ROOT)} is empty — run generate_static_content.py")
    else:
        count = len(list(CONTENT_DIR.glob("*.json")))
        print(f"  data/content ready ({count} JSON files at /data/content/)")


def build() -> list[Path]:
    env = make_env()
    stats = build_static_stats()
    curriculum = load_json("curriculum.json")
    nclex_stats = build_nclex_stats()

    written: list[Path] = []

    for out_path, template, module_id in PAGES:
        context: dict[str, Any] = {
            "stats": stats,
            "curriculum": curriculum,
            "nclex_stats": nclex_stats,
        }

        if module_id:
            context.update(build_module_context(module_id))

        use_static = module_id is not None  # existing modules need base swap
        if template in ("dashboard_static.html", "how_to_use.html", "nclex_prep.html") or template.startswith("modules/med_surg") or template.startswith("modules/maternal_newborn") or template.startswith("modules/pediatrics"):
            use_static = False  # already extend base_static

        if template == "nclex_prep.html":
            context["stats"] = nclex_stats

        html = render_page(env, template, context, use_static_base=use_static)
        path = write_output(out_path, html)
        written.append(path)
        print(f"  Built {out_path}")

    copy_data_content()
    return written


def main() -> None:
    print("Building static HTML for The Ward ADN...")
    paths = build()
    print(f"\nDone — {len(paths)} HTML files written to {OUTPUT_DIR}")
    print("Deploy with: vercel.json or netlify.toml (static + /data/content/)")


if __name__ == "__main__":
    main()