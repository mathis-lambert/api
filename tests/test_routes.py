import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.v1.endpoints import health_check


class DummyDB:
    def __init__(self):
        self.find_one = AsyncMock()
        self.insert_one = AsyncMock()
        self.get_client = lambda: MagicMock(close=lambda: None)


@pytest.fixture(autouse=True)
def startup_patch():
    with patch("api.main.ensure_database_connection", AsyncMock(return_value=(DummyDB(), DummyDB()))):
        yield


@pytest.mark.asyncio
async def test_health_endpoint(startup_patch):
    result = await health_check()
    assert result["status"] == "ok"
