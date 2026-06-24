"""Print merged audit catalog + DB status summary."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import async_session, init_db
from app.services.audit_service import get_audit_summary


async def main() -> None:
    await init_db()
    async with async_session() as db:
        summary = await get_audit_summary(db)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())