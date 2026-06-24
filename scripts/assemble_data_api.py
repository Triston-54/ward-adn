#!/usr/bin/env python3
"""Assemble static/js/data-api.js from part files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT / "static" / "js" / "_data_api_parts"
OUT = ROOT / "static" / "js" / "data-api.js"

def main():
    parts = sorted(PARTS_DIR.glob("*.js"))
    if not parts:
        raise SystemExit(f"No parts in {PARTS_DIR}")
    content = "\n".join(p.read_text(encoding="utf-8") for p in parts)
    OUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT} ({len(content.splitlines())} lines)")

if __name__ == "__main__":
    main()