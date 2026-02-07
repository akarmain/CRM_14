import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.models import Base
from app.db.seed import seed_contacts
from app.db.session import engine
from app.main import create_app


@pytest.fixture(scope="module", autouse=True)
async def setup_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    await seed_contacts()
    yield
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.mark.anyio
async def test_list_contacts() -> None:
    app = create_app()
    transport = ASGITransport(app=app, lifespan="on")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/contacts")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload
    assert "first_name" in payload[0]
