"""Final comprehensive content verification and audit pass — all Ward modules."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.assessment_service import get_module_summary as assessment_summary
from app.services.audit_service import build_content_catalog
from app.services.content_loader import load_content
from app.services.mental_health_service import get_module_summary as mh_summary
from app.services.microbiology_service import get_module_summary as micro_summary
from app.services.pharmacy_calculations_service import get_module_summary as pharm_summary
from app.services.progress_service import MODULES
from app.services.terminology_service import get_all_terms

VERIFIED_DATE = "2026-06"
CONTENT_DIR = ROOT / "data" / "content"
REPORT_PATH = ROOT / "data" / "final_audit_report.json"

CONTENT_FILES = [
    "terminology.json",
    "terminology_terms.json",
    "microbiology.json",
    "dosage.json",
    "dosage_drug_classes.json",
    "assessment.json",
    "assessment_manifest.json",
    "assessment_scaffold.json",
    "assessment_phase2_clinical.json",
    "assessment_phase2_interactive.json",
    "mental_health.json",
    "mental_health_manifest.json",
    "pharmacy_calculations.json",
    "pharmacy_manifest.json",
    "sources.json",
]

MODULE_SOURCE_KEYS = {
    "terminology",
    "microbiology",
    "dosage",
    "assessment",
    "mental_health",
    "pharmacy",
    "nclex",
    "cdc_infection",
    "new_river_ctc",
}

URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _check_url(url: str, timeout: int = 8) -> tuple[bool, str]:
    if not url or url == "null":
        return True, "null_allowed"
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "Ward-Audit/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            code = resp.status
            if code >= 400:
                return False, f"HTTP {code}"
            return True, f"HTTP {code}"
    except URLError as exc:
        # Some sites block HEAD — try GET with range
        try:
            req = Request(url, headers={"User-Agent": "Ward-Audit/1.0"})
            with urlopen(req, timeout=timeout) as resp:
                return True, f"GET HTTP {resp.status}"
        except URLError as exc2:
            return False, str(exc2.reason if hasattr(exc2, "reason") else exc2)
    except Exception as exc:
        return False, str(exc)


def _collect_ids(data: Any, path: str, id_field: str, bucket: dict[str, list[str]]) -> None:
    if isinstance(data, dict):
        if id_field in data and isinstance(data[id_field], (str, int)):
            key = str(data[id_field])
            bucket.setdefault(key, []).append(path)
        for k, v in data.items():
            _collect_ids(v, f"{path}.{k}" if path else k, id_field, bucket)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            _collect_ids(item, f"{path}[{i}]", id_field, bucket)


def _find_duplicate_ids(items: list[dict], id_key: str = "id") -> list[str]:
    seen: dict[str, int] = {}
    dups: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        iid = item.get(id_key)
        if iid is None:
            continue
        key = str(iid)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 2:
            dups.append(key)
    return dups


def _count_progress_items() -> dict[str, dict[str, Any]]:
    """Live progress-tracked item counts (distinct from audit catalog)."""
    terms = get_all_terms()
    micro = load_content("microbiology.json")
    dosage = load_content("dosage.json")
    assess = load_content("assessment.json")
    mh = load_content("mental_health.json")
    pharm = load_content("pharmacy_calculations.json")

    micro_count = (
        len(micro.get("healthcare_pathogens", micro.get("pathogens", [])))
        + len(micro.get("concepts", []))
        + len(micro.get("infection_chain", []))
        + len(micro.get("practice_questions", []))
        + len(micro.get("application_questions", []))
        + len(micro.get("break_chain_scenarios", []))
        + len(micro.get("what_if_scenarios", []))
    )
    dosage_count = (
        len(dosage.get("calc_types", []))
        + len(dosage.get("error_traps", []))
        + len(dosage.get("practice_problems", []))
        + len(dosage.get("pharmacology_safety", []))
        + len(dosage.get("drug_classes", []))
    )
    assess_count = (
        len(assess.get("head_to_toe_sequence", []))
        + len(assess.get("body_systems", []))
        + len(assess.get("red_flags_master", []))
        + len(assess.get("skills", []))
        + len(assess.get("practice_questions", []))
        + len(assess.get("special_populations", []))
        + len(assess.get("assessment_checklists", []))
        + len(assess.get("soap_exercises", []))
        + len(assess.get("assess_next_scenarios", []))
    )
    mh_count = (
        len(mh.get("therapeutic_communication", []))
        + len(mh.get("communication_barriers", []))
        + len(mh.get("communication_scenarios", []))
        + len(mh.get("safety_risk_flags", []))
        + len(mh.get("screening_tools", []))
        + len(mh.get("safety_drill", []))
        + len(mh.get("disorders", []))
        + len(mh.get("de_escalation", []))
        + len(mh.get("practice_questions", []))
    )

    catalog_by_module: dict[str, int] = {}
    for item in build_content_catalog():
        catalog_by_module[item["module_id"]] = catalog_by_module.get(item["module_id"], 0) + 1

    return {
        "terminology": {
            "live_count": len(terms),
            "catalog_count": catalog_by_module.get("terminology", 0),
            "modules_total": MODULES["terminology"]["total"],
            "formula": "merged terms from terminology.json + terminology_terms.json",
        },
        "microbiology": {
            "live_count": micro_count,
            "catalog_count": catalog_by_module.get("microbiology", 0),
            "modules_total": MODULES["microbiology"]["total"],
            "formula": "pathogens + concepts + chain + practice + scenarios",
            "summary": micro_summary(),
        },
        "dosage": {
            "live_count": dosage_count,
            "catalog_count": catalog_by_module.get("dosage", 0),
            "modules_total": MODULES["dosage"]["total"],
            "formula": "calc_types + error_traps + practice + pharm_safety + drug_classes",
        },
        "assessment": {
            "live_count": assess_count,
            "catalog_count": catalog_by_module.get("assessment", 0),
            "modules_total": MODULES["assessment"]["total"],
            "formula": "sequence + systems + red_flags + skills + practice + populations + checklists + soap + assess_next (excludes sbar, flashcards, interview_techniques)",
            "summary": assessment_summary(),
        },
        "mental_health": {
            "live_count": mh_count,
            "catalog_count": catalog_by_module.get("mental_health", 0),
            "modules_total": MODULES["mental_health"]["total"],
            "formula": "communication + barriers + scenarios + safety_flags + screening_tools + safety_drill + disorders + de_escalation + practice",
            "summary": mh_summary(),
        },
        "pharmacy_calculations": {
            "live_count": len(pharm.get("topic_outline", [])) + len(pharm.get("calc_types", [])),
            "catalog_count": 0,
            "modules_total": MODULES["pharmacy_calculations"]["total"],
            "formula": "scaffold target (48); live scaffold = topic_outline + calc_types",
            "summary": pharm_summary(),
            "note": "Pharmacy module is scaffold — progress total is build target, not live content count",
        },
    }


def _module_content_checks() -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    # Terminology — terms need definition + source.verified_date
    for term in get_all_terms():
        if not term.get("definition"):
            issues.append({"severity": "error", "module": "terminology", "item": term.get("term"), "issue": "missing definition"})
        src = term.get("source") or {}
        if not src.get("verified_date"):
            issues.append({"severity": "warn", "module": "terminology", "item": term.get("term"), "issue": "missing source.verified_date"})

    # Duplicate term names
    term_names = [t["term"].lower() for t in get_all_terms()]
    if len(term_names) != len(set(term_names)):
        issues.append({"severity": "error", "module": "terminology", "issue": "duplicate term names in merged list"})

    micro = load_content("microbiology.json")
    for section, id_key in [
        ("healthcare_pathogens", "name"),
        ("concepts", "id"),
        ("infection_chain", "id"),
        ("practice_questions", "id"),
        ("application_questions", "id"),
        ("break_chain_scenarios", "id"),
        ("what_if_scenarios", "id"),
    ]:
        items = micro.get(section, [])
        if section == "healthcare_pathogens" and not items:
            items = micro.get("pathogens", [])
        dups = _find_duplicate_ids(items, id_key if id_key != "name" else "id")
        for d in dups:
            issues.append({"severity": "error", "module": "microbiology", "section": section, "issue": f"duplicate id: {d}"})

    dosage = load_content("dosage.json")
    for section in ("calc_types", "error_traps", "practice_problems", "pharmacology_safety", "drug_classes"):
        dups = _find_duplicate_ids(dosage.get(section, []))
        for d in dups:
            issues.append({"severity": "error", "module": "dosage", "section": section, "issue": f"duplicate id: {d}"})

    assess = load_content("assessment.json")
    for section in (
        "body_systems", "red_flags_master", "skills", "practice_questions",
        "special_populations", "assessment_checklists", "soap_exercises",
        "sbar_exercises", "assess_next_scenarios", "flashcards",
    ):
        dups = _find_duplicate_ids(assess.get(section, []))
        for d in dups:
            issues.append({"severity": "error", "module": "assessment", "section": section, "issue": f"duplicate id: {d}"})

    mh = load_content("mental_health.json")
    for section in ("therapeutic_communication", "communication_barriers", "safety_risk_flags", "screening_tools", "safety_drill"):
        dups = _find_duplicate_ids(mh.get(section, []))
        for d in dups:
            issues.append({"severity": "error", "module": "mental_health", "section": section, "issue": f"duplicate id: {d}"})

    return issues


def run_audit(check_urls: bool = True) -> dict[str, Any]:
    report: dict[str, Any] = {
        "agent": "Final Content Verification & Audit Pass — Sub-Agent 1 — 2026-06",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verified_date": VERIFIED_DATE,
        "json_parse": {"passed": [], "failed": []},
        "sources_registry": {"issues": [], "modules_covered": []},
        "url_checks": {"checked": 0, "ok": 0, "failed": []},
        "item_counts": {},
        "count_discrepancies": [],
        "content_issues": [],
        "fixes_applied_this_pass": [],
        "remaining_human_review": [],
        "catalog_stats": {},
    }

    # 1. JSON parse all content files
    parsed: dict[str, Any] = {}
    for fname in CONTENT_FILES:
        fpath = CONTENT_DIR / fname
        if not fpath.exists():
            report["json_parse"]["failed"].append({"file": fname, "error": "file not found"})
            continue
        try:
            parsed[fname] = json.loads(fpath.read_text(encoding="utf-8"))
            report["json_parse"]["passed"].append(fname)
        except json.JSONDecodeError as exc:
            report["json_parse"]["failed"].append({"file": fname, "error": str(exc)})

    # 2. sources.json module coverage
    sources = parsed.get("sources.json", load_content("sources.json"))
    for key in sources:
        entry = sources[key]
        report["sources_registry"]["modules_covered"].append(key)
        if not entry.get("citation"):
            report["sources_registry"]["issues"].append({"key": key, "issue": "missing citation"})
        if not entry.get("verified_date"):
            report["sources_registry"]["issues"].append({"key": key, "issue": "missing verified_date"})
        elif entry.get("verified_date") != VERIFIED_DATE:
            report["sources_registry"]["issues"].append({
                "key": key,
                "issue": f"verified_date is {entry.get('verified_date')}, expected {VERIFIED_DATE}",
            })
        if key in MODULE_SOURCE_KEYS and not entry.get("title"):
            report["sources_registry"]["issues"].append({"key": key, "issue": "missing title"})

    missing_modules = MODULE_SOURCE_KEYS - set(sources.keys())
    for mid in sorted(missing_modules):
        report["sources_registry"]["issues"].append({"key": mid, "issue": "module missing from sources.json"})

    # 3. URL checks
    urls_seen: set[str] = set()
    for key, entry in sources.items():
        url = entry.get("url")
        if url and url not in urls_seen:
            urls_seen.add(url)
            if check_urls:
                ok, detail = _check_url(url)
                report["url_checks"]["checked"] += 1
                if ok:
                    report["url_checks"]["ok"] += 1
                else:
                    report["url_checks"]["failed"].append({"source_key": key, "url": url, "detail": detail})

    # Internal source URLs in content
    for fname, data in parsed.items():
        if fname == "sources.json":
            continue
        text = json.dumps(data)
        for match in URL_PATTERN.findall(text):
            if match in urls_seen:
                continue
            urls_seen.add(match)
            if check_urls and "localhost" not in match:
                ok, detail = _check_url(match)
                report["url_checks"]["checked"] += 1
                if ok:
                    report["url_checks"]["ok"] += 1
                else:
                    report["url_checks"]["failed"].append({"file": fname, "url": match, "detail": detail})

    # 4. Item counts vs MODULES
    counts = _count_progress_items()
    report["item_counts"] = counts
    for mod_id, info in counts.items():
        live = info["live_count"]
        expected = info["modules_total"]
        if mod_id == "pharmacy_calculations":
            report["count_discrepancies"].append({
                "module": mod_id,
                "live_count": live,
                "modules_total": expected,
                "status": "expected_scaffold_gap",
                "note": info.get("note"),
            })
        elif live != expected:
            report["count_discrepancies"].append({
                "module": mod_id,
                "live_count": live,
                "modules_total": expected,
                "catalog_count": info.get("catalog_count"),
                "status": "mismatch",
            })
        else:
            report["count_discrepancies"].append({
                "module": mod_id,
                "live_count": live,
                "modules_total": expected,
                "catalog_count": info.get("catalog_count"),
                "status": "ok",
            })

    # 5. Catalog stats
    catalog = build_content_catalog()
    by_mod: dict[str, int] = {}
    catalog_dups: dict[str, list[str]] = {}
    for item in catalog:
        by_mod[item["module_id"]] = by_mod.get(item["module_id"], 0) + 1
        key = f"{item['module_id']}:{item['item_key']}"
        catalog_dups.setdefault(key, []).append(item["title"])

    dup_keys = [k for k, v in catalog_dups.items() if len(v) > 1]
    report["catalog_stats"] = {
        "total": len(catalog),
        "by_module": by_mod,
        "duplicate_catalog_keys": dup_keys,
    }

    # 6. Module content checks
    report["content_issues"] = _module_content_checks()

    # 7. Document fixes applied in this pass
    report["fixes_applied_this_pass"] = [
        {"file": "data/content/assessment.json", "items": [
            "sequence:9 — rectal exam indication and consent added",
            "system:heent — split exophthalmos vs thyroid storm red flags",
            "system:respiratory — COPD-specific SpO₂ target caveat",
            "skill:orthostatic_vitals — OR criterion for orthostatic hypotension",
            "skill:fast_stroke — inpatient stroke code vs community 911",
            "redflag:temperature — immediate escalation and monitoring",
            "redflag:stridor — epiglottitis oropharynx exam contraindication",
            "redflag:epigastric — upgraded to immediate priority",
            "population:mental-health — CIWA-Ar severity bands corrected",
            "population:newborn — axillary vs rectal temperature harmonized",
            "scenario:an-12 — priority action with stop infusion + epinephrine IM",
            "soap:soap-06 — orientation documentation aligned",
            "flashcard:fc-card-02 — removed unsafe leg elevation in CHF",
        ]},
        {"file": "app/services/progress_service.py", "items": [
            "terminology total 153 → 220 (matches live term count)",
            "microbiology total 46 → 47 (matches live content count)",
        ]},
        {"file": "app/services/audit_service.py", "items": [
            "Removed duplicate sbar_exercises catalog loop (6 duplicate keys)",
        ]},
        {"file": "data/content/sources.json", "items": [
            "nclex URL → ncsbn.org/exams/testplans.page",
            "new_river_ctc URL → newriver.edu/courses/associate-degree-nursing/",
            "dosage URL → us.elsevierhealth.com product page",
            "terminology URL → cengage 8e product slug",
        ]},
    ]

    # 8. Remaining human review items
    report["remaining_human_review"] = [
        {
            "module": "pharmacy_calculations",
            "issue": "Scaffold module — 14 live items vs 48 progress target; full content build pending",
            "priority": "P2",
        },
        {
            "module": "assessment",
            "issue": "Audit catalog (204 items) exceeds progress total (132) by design — flashcards, sbar, interview_techniques tracked in catalog but not progress denominator",
            "priority": "info",
        },
        {
            "module": "sources",
            "issue": "pharmacy source url is null (Remington has no public URL) — acceptable",
            "priority": "info",
        },
    ]

    if dup_keys:
        report["remaining_human_review"].append({
            "module": "audit_catalog",
            "issue": f"Duplicate catalog keys detected: {dup_keys}",
            "priority": "P1",
        })

    # Summary
    errors = (
        len(report["json_parse"]["failed"])
        + len([i for i in report["content_issues"] if i.get("severity") == "error"])
        + len([d for d in report["count_discrepancies"] if d.get("status") == "mismatch"])
        + len(dup_keys)
    )
    report["summary"] = {
        "json_files_ok": len(report["json_parse"]["passed"]),
        "json_files_failed": len(report["json_parse"]["failed"]),
        "content_errors": len([i for i in report["content_issues"] if i.get("severity") == "error"]),
        "content_warnings": len([i for i in report["content_issues"] if i.get("severity") == "warn"]),
        "count_mismatches": len([d for d in report["count_discrepancies"] if d.get("status") == "mismatch"]),
        "url_failures": len(report["url_checks"]["failed"]),
        "catalog_duplicate_keys": len(dup_keys),
        "overall_pass": errors == 0 and len(report["json_parse"]["failed"]) == 0,
    }

    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Ward final content audit pass")
    parser.add_argument("--no-url-check", action="store_true", help="Skip HTTP URL validation")
    args = parser.parse_args()

    report = run_audit(check_urls=not args.no_url_check)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"\nReport written to {REPORT_PATH}")
    if not report["summary"]["overall_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()