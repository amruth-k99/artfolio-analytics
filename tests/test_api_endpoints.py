import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "Healthy"}

@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

@pytest.mark.asyncio
async def test_get_events_empty(async_client: AsyncClient):
    response = await async_client.get("/v1/events/")
    assert response.status_code == 200
    # The endpoint returns a paginated envelope, not a bare list. This asserted
    # `== []` and had been failing against the real response shape.
    body = response.json()
    assert body["data"]["events"] == []
    assert body["data"]["pagination"]["total"] == 0
