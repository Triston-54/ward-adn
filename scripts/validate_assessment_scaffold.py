"""Validate assessment manifest and scaffold files."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.assessment_manifest import get_build_status, get_manifest, validate_scaffold


def main() -> int:
    manifest = get_manifest()
    if not manifest.get("module_id"):
        print("ERROR: assessment_manifest.json missing module_id")
        return 1

    validation = validate_scaffold()
    status = get_build_status()

    report = {
        "manifest_version": manifest.get("version"),
        "module_status": manifest.get("status"),
        "scaffold_validation": validation,
        "build_status": status,
    }

    out = ROOT / "data" / "assessment_build_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

    if not validation["valid"]:
        print("\nWARN: Scaffold has schema issues (expected for TBD placeholders).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())