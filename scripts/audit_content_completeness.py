#!/usr/bin/env python3
"""Audit JSON content fields used by static module frontends."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data" / "content"


def load(name: str) -> dict:
    with open(CONTENT / name, encoding="utf-8") as f:
        return json.load(f)


def check(label: str, issues: list[str], ok: list[str]) -> None:
    if issues:
        print(f"  FAIL {label}: {len(issues)} issue(s)")
        for i in issues[:5]:
            print(f"    - {i}")
        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more")
    else:
        ok.append(label)
        print(f"  OK   {label}")


def main() -> int:
    ok: list[str] = []
    fails = 0

    print("THE WARD — Content Completeness Audit\n")

    # Terminology
    terms = load("terminology_terms.json").get("terms", [])
    check("Terminology terms", [] if len(terms) >= 200 else [f"only {len(terms)} terms"], ok)

    # Microbiology
    micro = load("microbiology.json")
    mc_issues = []
    for t in micro.get("microbe_classification", []):
        for f in ("structure", "treatment", "examples", "clinical_why"):
            if not t.get(f):
                mc_issues.append(f"{t.get('type')}: missing {f}")
    for s in micro.get("break_chain_scenarios", []):
        if not s.get("options") or s.get("correct_index") is None:
            mc_issues.append(f"break-chain {s.get('id')}: bad options shape")
    for h in micro.get("hai_types", []):
        if not h.get("clinical_why"):
            mc_issues.append(f"HAI {h.get('id')}: missing clinical_why")
    check("Microbiology", mc_issues, ok)

    # Dosage
    dosage = load("dosage.json")
    trap_issues = [t["id"] for t in dosage.get("error_traps", []) if not (t.get("fix") or t.get("avoid"))]
    dc_issues = [d["id"] for d in dosage.get("drug_classes", []) if not d.get("mechanism_of_action")]
    check("Dosage traps & drug classes", trap_issues + dc_issues, ok)

    # Assessment
    assess = load("assessment.json")
    ht_issues = []
    for step in assess.get("head_to_toe_sequence", []):
        if not (step.get("rationale") or step.get("tips") or step.get("technique")):
            ht_issues.append(f"step {step.get('order')}: no rationale/tips")
    pop_issues = []
    for p in assess.get("special_populations", []):
        if not (p.get("overview") or p.get("considerations")):
            pop_issues.append(f"{p.get('id')}: no overview/considerations")
    check("Assessment", ht_issues + pop_issues, ok)

    # Pathophysiology
    patho = load("pathophysiology.json")
    p_issues = []
    for c in patho.get("core_concepts", []):
        if not (c.get("nursing_focus") or c.get("nursing_implications")):
            p_issues.append(f"concept {c.get('id')}: no nursing focus")
    for d in patho.get("disease_processes", []):
        if not (d.get("pathophysiology") or d.get("etiology")):
            p_issues.append(f"disease {d.get('id')}: no pathophysiology")
    for pair in patho.get("compare_contrast_pairs", []):
        if not pair.get("key_differences"):
            p_issues.append(f"compare {pair.get('id')}: no key_differences")
    pq_issues = [q["id"] for q in patho.get("practice_questions", []) if not (q.get("explanation") or q.get("rationale"))]
    check("Pathophysiology", p_issues + pq_issues, ok)

    # Maternal-child
    mc = load("maternal_child.json")
    ref_issues = []
    for section, key in [
        ("pregnancy_stages", "antepartum"),
        ("labor_delivery", "intrapartum"),
        ("postpartum_newborn", "postpartum"),
        ("pediatric_essentials", "pediatrics"),
    ]:
        for item in mc.get(section, []):
            if not (item.get("summary") or item.get("content")):
                ref_issues.append(f"{key}/{item.get('id')}: no content")
    check("Maternal-child reference cards", ref_issues, ok)

    # Mental health
    mh = load("mental_health.json")
    mh_issues = []
    for b in mh.get("communication_barriers", []):
        if not (b.get("instead") or b.get("therapeutic_alternative")):
            mh_issues.append(f"barrier {b.get('id')}: no alternative")
    check("Mental health", mh_issues, ok)

    # NCLEX
    nclex = load("nclex_prep.json")
    qs = nclex.get("all_questions") or nclex.get("questions", [])
    n_issues = [q.get("id", "?") for q in qs if not q.get("rationale")]
    check("NCLEX prep", n_issues if len(n_issues) > len(qs) * 0.1 else [], ok)

    # Med-surg
    ms = load("med_surg.json")
    ms_issues = [q.get("id", "?") for q in ms.get("practice_questions", []) if not (q.get("rationale") or q.get("explanation"))]
    check("Med-surg", ms_issues, ok)

    print(f"\n{'=' * 50}")
    print(f"PASSED: {len(ok)}  |  MODULES WITH ISSUES: {10 - len(ok)}")
    print("=" * 50)
    return 0 if len(ok) >= 9 else 1


if __name__ == "__main__":
    sys.exit(main())