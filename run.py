#!/usr/bin/env python3
"""Single-command launcher for The Ward nursing study suite."""
import os
import sys
import webbrowser
from pathlib import Path

import uvicorn

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main():
    """Start the local development server."""
    from app.config import settings

    print("\n" + "=" * 56)
    print("  THE WARD — ADN Nursing Study Suite")
    print("  New River Community and Technical College")
    print("=" * 56)
    print(f"\n  Local:   http://{settings.host}:{settings.port}")
    print("  Press Ctrl+C to stop\n")

    # Open browser unless an external launcher handles it (e.g. launch_ward.bat)
    if not os.environ.get("WARD_SKIP_BROWSER"):
        try:
            webbrowser.open(f"http://{settings.host}:{settings.port}")
        except Exception:
            pass

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
    )


if __name__ == "__main__":
    main()