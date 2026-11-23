# app/tests/test_health_api.py
from unittest.mock import patch

import httpx
import pytest
from fastapi import status
from httpx import ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "environment" in data
        assert "database" in data
        assert "redis" in data


@pytest.mark.asyncio
async def test_health_check_hides_internal_exception_details():
    from unittest.mock import MagicMock

    mock_engine = MagicMock()
    mock_engine.connect.side_effect = RuntimeError("secret-host:5432")
    with patch("app.main.engine", mock_engine):
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert "secret-host" not in response.text
    assert response.json()["database"] == "unhealthy"
    assert response.json()["status"] == "degraded"
