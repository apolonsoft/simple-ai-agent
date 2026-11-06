# app/tests/test_health_api.py
import pytest
from fastapi import status
import httpx
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
