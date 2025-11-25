import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from httpx import AsyncClient
from sqlmodel import SQLModel

from src.app.database import engine
from src.app.main import app


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
