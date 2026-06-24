"""Socratic tutor smoke tests — no Ollama required."""
from __future__ import annotations

import asyncio
import json

from app.models import SocraticRequest
from app.services.ai_service import (
    _search_module_content,
    detect_topic_category,
    socratic_tutor,
)
from app.services.socratic_registry import (
    SOCRATIC_MODULES,
    detect_module_from_path,
    get_client_config,
)


def test_registry() -> None:
    assert "pathophysiology" in SOCRATIC_MODULES
    assert "maternal_child" in SOCRATIC_MODULES
    assert detect_module_from_path("/modules/pathophysiology") == "pathophysiology"
    assert detect_module_from_path("/modules/maternal-child") == "maternal_child"
    assert detect_topic_category("what is heart failure pathophysiology", "pathophysiology") == "pathophysiology"
    assert detect_topic_category("apgar score newborn", "maternal_child") == "assessment_finding"
    snips = _search_module_content("microbiology", "hand hygiene infection chain", "pathophysiology")
    assert len(snips) > 0
    cfg = get_client_config("pathophysiology")
    assert cfg["module_label"] == "Pathophysiology"


async def test_chat_flow() -> None:
    r1 = await socratic_tutor(
        SocraticRequest(
            module_id="microbiology",
            question="How does MRSA spread in hospitals?",
            socratic_mode=True,
            intent="explore",
        )
    )
    assert r1.phase == "explore"
    assert r1.guiding_only is True
    assert r1.ai_status == "placeholder"
    assert len(r1.follow_up_questions) >= 2
    assert len(r1.sources) > 0

    history = [
        {"role": "user", "content": "How does MRSA spread in hospitals?"},
        {"role": "assistant", "content": r1.response},
    ]
    r2 = await socratic_tutor(
        SocraticRequest(
            module_id="microbiology",
            question="I think contact precautions and hand hygiene break transmission.",
            context=json.dumps(history),
            socratic_mode=True,
        )
    )
    assert r2.phase == "explore"
    assert "shared" in r2.response.lower() or "turn 2" in r2.response.lower()

    history += [
        {"role": "user", "content": "I think contact precautions and hand hygiene break transmission."},
        {"role": "assistant", "content": r2.response},
    ]
    r3 = await socratic_tutor(
        SocraticRequest(
            module_id="microbiology",
            question="So what nursing action is highest priority?",
            context=json.dumps(history),
            socratic_mode=True,
        )
    )
    assert r3.phase == "teach"
    assert r3.guiding_only is False

    r4 = await socratic_tutor(
        SocraticRequest(
            module_id="dosage",
            question="insulin sliding scale",
            intent="explain_mechanism",
            page_context=json.dumps({"subject": "Insulin", "snippet": "Regular insulin onset 30 min"}),
        )
    )
    assert r4.intent == "explain_mechanism"
    assert r4.phase == "teach"


async def main() -> None:
    test_registry()
    await test_chat_flow()
    print("All socratic tests passed!")


if __name__ == "__main__":
    asyncio.run(main())