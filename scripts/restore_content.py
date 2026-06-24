#!/usr/bin/env python3
"""Regenerate missing WARD content JSON files with textbook-quality nursing education content."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.restore_content_payload.assessment import build as build_assessment
from scripts.restore_content_payload.dosage import build_dosage, build_drug_classes
from scripts.restore_content_payload.manifests import (
    build_maternal_child_manifest,
    build_mental_health_manifest,
    build_pathophysiology_manifest,
)
from scripts.restore_content_payload.maternal_child import build as build_maternal_child
from scripts.restore_content_payload.mental_health import build as build_mental_health
from scripts.restore_content_payload.microbiology import build as build_microbiology
from scripts.restore_content_payload.pathophysiology import build as build_pathophysiology
from scripts.restore_content_payload.terminology import build as build_terminology
from scripts.restore_content_payload.common import CONTENT_DIR, count_sections, write_json

REQUIRED_FILES = [
    "terminology.json",
    "microbiology.json",
    "dosage.json",
    "dosage_drug_classes.json",
    "assessment.json",
    "pathophysiology.json",
    "pathophysiology_manifest.json",
    "mental_health.json",
    "mental_health_manifest.json",
    "maternal_child.json",
    "maternal_child_manifest.json",
]


def _count_file(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    name = path.name
    if name == "terminology.json":
        return count_sections(data, ["prefixes", "roots", "suffixes", "practice_questions", "flashcards"])
    if name == "microbiology.json":
        return {
            "infection_chain": len(data.get("infection_chain", [])),
            "chain_interventions": len(data.get("chain_interventions", {})),
            "healthcare_pathogens": len(data.get("healthcare_pathogens", [])),
            "concepts": len(data.get("concepts", [])),
            "gram_stain_procedure": len(data.get("gram_stain_procedure", [])),
            "hand_hygiene": 1 if data.get("hand_hygiene") else 0,
            "ppe_guide": 1 if data.get("ppe_guide") else 0,
            "hai_types": len(data.get("hai_types", [])),
            "break_chain_scenarios": len(data.get("break_chain_scenarios", [])),
            "what_if_scenarios": len(data.get("what_if_scenarios", [])),
            "practice_questions": len(data.get("practice_questions", [])),
            "application_questions": len(data.get("application_questions", [])),
            "break_points": len(data.get("break_points", [])),
        }
    if name == "dosage.json":
        return count_sections(data, ["calc_types", "first_principles", "practice_problems", "error_traps", "pharmacology_safety", "drug_classes"])
    if name == "dosage_drug_classes.json":
        return count_sections(data, ["drug_classes", "pharm_categories"])
    if name == "assessment.json":
        return {
            "head_to_toe_sequence": len(data.get("head_to_toe_sequence", [])),
            "body_systems": len(data.get("body_systems", [])),
            "red_flags_master": len(data.get("red_flags_master", [])),
            "skills": len(data.get("skills", [])),
            "practice_questions": len(data.get("practice_questions", [])),
            "special_populations": len(data.get("special_populations", [])),
            "assessment_checklists": len(data.get("assessment_checklists", [])),
            "soap_exercises": len(data.get("soap_exercises", [])),
            "sbar_exercises": len(data.get("sbar_exercises", [])),
            "assess_next_scenarios": len(data.get("assess_next_scenarios", [])),
            "flashcards": len(data.get("flashcards", [])),
            "interview_techniques": len(data.get("interview_techniques", [])),
        }
    if name == "pathophysiology.json":
        return count_sections(data, ["core_concepts", "disease_processes", "compare_contrast_pairs", "what_breaks_down_scenarios", "flashcards", "practice_questions"])
    if name == "mental_health.json":
        return count_sections(data, ["therapeutic_communication", "communication_barriers", "communication_scenarios", "safety_risk_flags", "screening_tools", "disorders", "de_escalation", "safety_drill", "practice_questions"])
    if name == "maternal_child.json":
        return count_sections(data, ["pregnancy_stages", "labor_delivery", "postpartum_newborn", "pediatric_essentials", "safety_red_flags", "complications_drill", "flashcards", "practice_questions"])
    if name.endswith("_manifest.json"):
        inv = data.get("content_inventory", {})
        return {"content_inventory_sections": len(inv), "tabs": len(data.get("tabs", []))}
    return {"top_level_keys": len(data)}


def restore_all() -> dict[str, Path]:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    drug_classes_payload = build_drug_classes()
    dosage_payload = build_dosage()

    writers = {
        "terminology.json": build_terminology(),
        "microbiology.json": build_microbiology(),
        "dosage_drug_classes.json": drug_classes_payload,
        "dosage.json": dosage_payload,
        "assessment.json": build_assessment(),
        "pathophysiology.json": build_pathophysiology(),
        "pathophysiology_manifest.json": build_pathophysiology_manifest(),
        "mental_health.json": build_mental_health(),
        "mental_health_manifest.json": build_mental_health_manifest(),
        "maternal_child.json": build_maternal_child(),
        "maternal_child_manifest.json": build_maternal_child_manifest(),
    }
    written: dict[str, Path] = {}
    for filename, payload in writers.items():
        written[filename] = write_json(filename, payload)
        print(f"Wrote {written[filename]}")
    return written


def validate_json_files(files: list[str]) -> list[str]:
    errors: list[str] = []
    for filename in files:
        path = CONTENT_DIR / filename
        if not path.exists():
            errors.append(f"Missing: {filename}")
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSON in {filename}: {exc}")
    return errors


def main() -> int:
    print("=== WARD Content Restoration ===")
    restore_all()

    print("\n--- Running generate_terms.py ---")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_terms.py")], check=True, cwd=str(ROOT))

    print("\n--- Validation ---")
    errors = validate_json_files(REQUIRED_FILES)
    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return 1

    print("\n--- Item Counts ---")
    summary: dict[str, dict[str, int]] = {}
    for filename in REQUIRED_FILES:
        path = CONTENT_DIR / filename
        counts = _count_file(path)
        summary[filename] = counts
        total = sum(counts.values())
        detail = ", ".join(f"{k}={v}" for k, v in counts.items())
        print(f"{filename}: total={total} ({detail})")

    report_path = ROOT / "data" / "restore_content_report.json"
    report_path.write_text(json.dumps({"files": REQUIRED_FILES, "counts": summary}, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport saved to {report_path}")
    print("All required JSON files restored and validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())