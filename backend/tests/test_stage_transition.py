import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.deps import reset_container
from app.main import create_app


@pytest.mark.anyio
async def test_cannot_transition_from_won_or_lost(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "event",
                "owner": "sales_head",
                "title": "Conference follow-up",
            },
        )
        assert create_resp.status_code == 201
        lead_uid = create_resp.json()["lead_uid"]

        to_won_resp = await client.post(
            f"/api/v1/leads/{lead_uid}/stage",
            json={"stage": "won", "author": "sales_head", "comment": "Closed deal"},
        )
        assert to_won_resp.status_code == 200

        invalid_resp = await client.post(
            f"/api/v1/leads/{lead_uid}/stage",
            json={"stage": "proposal", "author": "sales_head"},
        )
        assert invalid_resp.status_code == 400
        assert "Invalid stage transition" in invalid_resp.json()["detail"]
