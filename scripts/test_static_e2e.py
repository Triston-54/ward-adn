#!/usr/bin/env python3
"""End-to-end smoke tests for The Ward static site (http://127.0.0.1:8777)."""
from __future__ import annotations

import json
import random
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8777"
TIMEOUT = 15

# Pages that must return HTTP 200
HTTP_ENDPOINTS = [
    "/index.html",
    "/how-to-use.html",
    "/nclex-prep.html",
    "/modules/microbiology.html",
    "/modules/terminology.html",
    "/modules/assessment.html",
    "/modules/med_surg.html",
    "/modules/dosage.html",
    "/modules/mental-health.html",
    "/modules/pathophysiology.html",
    "/modules/maternal-child.html",
    "/modules/maternal_newborn.html",
    "/modules/pediatrics.html",
]

JSON_ENDPOINTS = [
    "/data/content/microbiology.json",
    "/data/content/nclex_prep.json",
]

PHARMACY_PATTERN = re.compile(r"pharmacy", re.IGNORECASE)
HTML_PHARMACY_TARGETS = [ROOT / "index.html", *sorted((ROOT / "modules").glob("*.html"))]


class CheckResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.notes: list[str] = []

    def ok(self, msg: str) -> None:
        self.passed.append(msg)

    def fail(self, msg: str) -> None:
        self.failed.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


def fetch(url: str) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "ward-static-e2e/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), exc.headers.get("Content-Type")


def simulate_microbiology_flashcards(pathogens: list[dict], count: int = 8) -> list[dict]:
    """Mirror WardData.Microbiology.flashcards(count) logic from static/js/data-api.js."""
    pool = list(pathogens)
    random.shuffle(pool)
    sliced = pool[: min(count, len(pool))]
    return [
        {
            "id": p["name"].lower().replace(" ", "-"),
            "front": p["name"],
            "back": p.get("full_name", ""),
            "precautions": p.get("precautions", ""),
            "nursing_action": p.get("nursing_action", ""),
        }
        for p in sliced
    ]


def check_pharmacy_references(result: CheckResult) -> None:
    hits: list[str] = []
    for path in HTML_PHARMACY_TARGETS:
        if not path.exists():
            result.fail(f"HTML file missing: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if PHARMACY_PATTERN.search(text):
            hits.append(str(path.relative_to(ROOT)))
    if hits:
        result.fail(f"Pharmacy references found in HTML: {', '.join(hits)}")
    else:
        result.ok(f"No pharmacy references in index.html or modules/*.html ({len(HTML_PHARMACY_TARGETS)} files)")


def check_deploy_configs(result: CheckResult) -> None:
    vercel_path = ROOT / "vercel.json"
    netlify_path = ROOT / "netlify.toml"

    if not vercel_path.exists():
        result.fail("vercel.json missing")
    else:
        try:
            data = json.loads(vercel_path.read_text(encoding="utf-8"))
            assert isinstance(data, dict) and "rewrites" in data
            result.ok("vercel.json valid JSON with rewrites")
        except (json.JSONDecodeError, AssertionError) as exc:
            result.fail(f"vercel.json invalid: {exc}")

    if not netlify_path.exists():
        result.fail("netlify.toml missing")
    else:
        raw = netlify_path.read_text(encoding="utf-8")
        try:
            import tomllib  # Python 3.11+

            tomllib.loads(raw)
            result.ok("netlify.toml valid TOML")
        except ImportError:
            # Minimal structural check when tomllib unavailable
            if "[build]" in raw and "publish" in raw:
                result.ok("netlify.toml present (tomllib unavailable; basic structure OK)")
            else:
                result.fail("netlify.toml missing expected [build] section")
        except Exception as exc:
            result.fail(f"netlify.toml invalid: {exc}")


def main() -> int:
    result = CheckResult()

    if port_open("127.0.0.1", 8777):
        result.note("Using existing HTTP server on port 8777")
    else:
        result.fail("No server on port 8777 — start with: python -m http.server 8777")
        print_report(result)
        return 1

    # HTTP endpoint checks
    for path in HTTP_ENDPOINTS:
        status, body, _ = fetch(f"{BASE}{path}")
        if status == 200 and len(body) > 100:
            result.ok(f"GET {path} → {status} ({len(body)} bytes)")
        else:
            result.fail(f"GET {path} → {status} (expected 200, body > 100 bytes)")

    # JSON content checks
    for path in JSON_ENDPOINTS:
        status, body, ct = fetch(f"{BASE}{path}")
        if status != 200:
            result.fail(f"GET {path} → {status}")
            continue
        try:
            data = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            result.fail(f"GET {path} → invalid JSON: {exc}")
            continue
        result.ok(f"GET {path} → 200 (Content-Type: {ct or 'unknown'})")

        if path.endswith("microbiology.json"):
            pathogens = data.get("healthcare_pathogens")
            if not isinstance(pathogens, list) or not pathogens:
                result.fail("microbiology.json missing healthcare_pathogens array")
            else:
                result.ok(f"microbiology.json healthcare_pathogens count = {len(pathogens)}")
                cards = simulate_microbiology_flashcards(pathogens, 8)
                if len(cards) >= 8:
                    result.ok(f"Microbiology.flashcards(8) simulation → {len(cards)} cards")
                else:
                    result.fail(
                        f"Microbiology.flashcards(8) simulation → only {len(cards)} cards "
                        f"(need >= 8 pathogens)"
                    )
                required_keys = {"front", "back", "precautions", "nursing_action"}
                sample = cards[0] if cards else {}
                if required_keys.issubset(sample.keys()):
                    result.ok("Flashcard shape matches data-api.js (front/back/precautions/nursing_action)")
                else:
                    result.fail(f"Flashcard missing keys: {required_keys - set(sample)}")

        if path.endswith("nclex_prep.json"):
            total = data.get("total_questions")
            questions = data.get("all_questions") or data.get("questions", [])
            computed = len(questions) if isinstance(questions, list) else 0
            if total is None:
                result.fail("nclex_prep.json missing total_questions")
            elif total >= 85:
                result.ok(f"nclex_prep.json total_questions = {total} (>= 85)")
            else:
                result.fail(f"nclex_prep.json total_questions = {total} (expected >= 85)")
            prio = sum(1 for q in questions if isinstance(q, dict) and q.get("category") == "Prioritization")
            if prio >= 4:
                result.ok(f"nclex_prep.json prioritization questions = {prio} (>= 4)")
            else:
                result.fail(f"nclex_prep.json prioritization questions = {prio} (expected >= 4)")
            if computed and computed != total:
                result.note(f"nclex_prep.json questions array length ({computed}) != total_questions ({total})")

    check_pharmacy_references(result)
    check_deploy_configs(result)

    print_report(result)
    return 0 if not result.failed else 1


def print_report(result: CheckResult) -> None:
    print("\n" + "=" * 60)
    print("THE WARD — STATIC SITE E2E REPORT")
    print("=" * 60)

    if result.notes:
        print("\nNotes:")
        for note in result.notes:
            print(f"  • {note}")

    print(f"\nPASSED ({len(result.passed)}):")
    for item in result.passed:
        print(f"  ✓ {item}")

    if result.failed:
        print(f"\nFAILED ({len(result.failed)}):")
        for item in result.failed:
            print(f"  ✗ {item}")
    else:
        print("\nFAILED (0)")

    print("\n" + "-" * 60)
    status = "PASS" if not result.failed else "FAIL"
    print(f"OVERALL: {status} — {len(result.passed)} passed, {len(result.failed)} failed")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    sys.exit(main())