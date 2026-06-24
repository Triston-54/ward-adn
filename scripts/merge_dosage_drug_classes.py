"""Merge drug_classes pharmacology content into dosage.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOSAGE_PATH = ROOT / "data" / "content" / "dosage.json"
CLASSES_PATH = ROOT / "data" / "content" / "dosage_drug_classes.json"


def _normalize(dc: dict) -> dict:
    pd = dc.get("prototype_drugs")
    if isinstance(pd, str):
        dc["prototype_drugs"] = [x.strip() for x in pd.split(",")]
    for key in (
        "nursing_implications", "monitoring", "common_side_effects",
        "contraindications", "interactions",
    ):
        if key in dc and isinstance(dc[key], str):
            dc[key] = [dc[key]]
    return dc


def main() -> None:
    if not CLASSES_PATH.exists():
        raise SystemExit(f"Missing {CLASSES_PATH}")

    payload = json.loads(CLASSES_PATH.read_text(encoding="utf-8"))
    classes = [_normalize(dc) for dc in payload["drug_classes"]]

    data = json.loads(DOSAGE_PATH.read_text(encoding="utf-8"))
    data["drug_classes"] = classes
    data["pharm_categories"] = payload.get("pharm_categories", [])

    DOSAGE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Merged {len(classes)} drug classes into dosage.json")


if __name__ == "__main__":
    main()