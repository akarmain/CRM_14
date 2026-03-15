import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.deps import reset_container
from app.main import create_app


@pytest.mark.anyio
async def test_smoke_create_and_move_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/leads",
            json={
                "source_code": "website",
                "owner": "manager_1",
                "title": "New inbound lead",
                "notes": "Interested in annual subscription",
            },
        )
        assert create_resp.status_code == 201
        lead = create_resp.json()
        assert lead["current_stage"] == "new"

        move_resp = await client.post(
            f"/api/v1/leads/{lead['lead_uid']}/stage",
            json={
                "stage": "qualified",
                "author": "manager_2",
                "comment": "Reached out and confirmed budget",
            },
        )
        assert move_resp.status_code == 200
        moved = move_resp.json()
        assert moved["lead"]["current_stage"] == "qualified"
        assert moved["stage_event"]["stage"] == "qualified"
        assert moved["stage_event"]["comment"]["comment"] == "Reached out and confirmed budget"

        stages_resp = await client.get(f"/api/v1/leads/{lead['lead_uid']}/stages")
        assert stages_resp.status_code == 200
        stages = stages_resp.json()
        assert len(stages) == 2
        assert stages[0]["stage"] == "new"
        assert stages[1]["stage"] == "qualified"

        list_resp = await client.get("/api/v1/leads")
        assert list_resp.status_code == 200
        items = list_resp.json()
        listed = next(item for item in items if item["lead_uid"] == lead["lead_uid"])
        assert "stage_info" in listed
        assert set(listed["stage_info"].keys()) >= {"new", "qualified"}
        assert listed["stage_info"]["new"]["left_at"] is not None
        assert listed["stage_info"]["qualified"]["left_at"] is None
        assert listed["stage_info"]["qualified"]["approved"] is True


@pytest.mark.anyio
async def test_new_lead_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORAGE_MODE", "memo")
    get_settings.cache_clear()
    reset_container()

    app = create_app()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/new-lead",
            json={
                "owner": "manager_1",
                "title": "Lead from legacy endpoint",
                "notes": "Created via /new-lead",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["owner"] == "manager_1"
        assert payload["current_stage"] == "new"
        assert payload["source_code"] == "other"
