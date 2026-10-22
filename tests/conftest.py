import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

# Test fixture only. Never used by the running service or shipped as a default.
TEST_KEY = 'test-only-key-not-for-deployment-123456789'


@pytest.fixture
def settings(tmp_path):
    return Settings(_env_file=None, api_key=TEST_KEY,
                    database_url=f'sqlite:///{tmp_path / "test.db"}',
                    cors_origins=['http://localhost:3000'])


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as client:
        client.headers['Authorization'] = f'Bearer {TEST_KEY}'
        yield client
