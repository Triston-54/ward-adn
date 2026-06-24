"""HTTP smoke tests for Socratic endpoints."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

health = client.get("/health").json()
assert health["status"] == "healthy"

socratic_health = client.get("/api/socratic/health").json()
assert "ai_provider" in socratic_health
assert socratic_health["ollama"]["available"] is False

chat = client.post(
    "/api/socratic/chat",
    json={
        "module_id": "dosage",
        "question": "convert 500 mg to tablets",
        "socratic_mode": True,
        "intent": "explore",
    },
).json()
assert chat["phase"] == "explore"
assert chat["ai_status"] == "placeholder"
assert chat["module_id"] == "dosage"

detect = client.get("/api/socratic/detect-module", params={"path": "/modules/maternal-child"}).json()
assert detect["module_id"] == "maternal_child"

print("HTTP socratic tests passed!")