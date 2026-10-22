import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.config import Settings
from app.main import create_app


@pytest.mark.parametrize('authorization', [None, 'Bearer wrong-key', 'Basic dXNlcjpwYXNz', 'Bearer'])
@pytest.mark.parametrize('method,path,payload', [
    ('GET', '/tasks', None), ('POST', '/tasks', {'title': 'Unauthorized'}),
    ('GET', '/tasks/1', None), ('PATCH', '/tasks/1', {'title': 'Unauthorized'}),
    ('DELETE', '/tasks/1', None),
])
def test_all_task_routes_require_auth(client, authorization, method, path, payload):
    client.headers.pop('Authorization', None)
    headers = {'Authorization': authorization} if authorization is not None else {}
    response = client.request(method, path, headers=headers, json=payload)
    assert response.status_code == 401
    assert response.headers['WWW-Authenticate'] == 'Bearer'
    from conftest import TEST_KEY
    assert TEST_KEY not in response.text


def test_liveness_is_public(client):
    client.headers.clear()
    assert client.get('/health').json() == {'status': 'ok'}


def test_cors_is_allowlisted(client):
    headers = {'Origin': 'http://localhost:3000', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'Authorization,Content-Type'}
    allowed = client.options('/tasks', headers=headers)
    assert allowed.status_code == 200
    assert allowed.headers['access-control-allow-origin'] == headers['Origin']
    headers['Origin'] = 'https://untrusted.example'
    denied = client.options('/tasks', headers=headers)
    assert denied.status_code == 400
    assert 'access-control-allow-origin' not in denied.headers


@pytest.mark.parametrize('key', ['', 'short', 'replace-with-your-random-secret-key-000000'])
def test_insecure_key_is_rejected(key):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_key=key)


@pytest.mark.parametrize('origin', ['*', 'https://example.com/path', 'https://*.example.com', 'file://example', 'https://user:password@example.com'])
def test_invalid_cors_origin_is_rejected(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, api_key='test-key-123456789012345678901234567890', cors_origins=[origin])


def test_environment_settings(monkeypatch):
    monkeypatch.setenv('TASK_API_KEY', 'test-environment-key-12345678901234567890')
    monkeypatch.setenv('TASK_CORS_ORIGINS', '["http://localhost:3000"]')
    assert Settings(_env_file=None).cors_origins == ['http://localhost:3000']


def test_missing_api_key_fails_configuration(monkeypatch):
    monkeypatch.delenv('TASK_API_KEY', raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_docs_and_openapi_security(client):
    assert client.get('/docs').status_code == 200
    schema = client.get('/openapi.json').json()
    assert schema['components']['securitySchemes']['TeamApiKey']['scheme'] == 'bearer'
    for path, operations in schema['paths'].items():
        if path.startswith('/tasks'):
            for operation in operations.values():
                assert operation['security'] == [{'TeamApiKey': []}]


def test_docs_can_be_disabled(settings):
    settings.docs_enabled = False
    with TestClient(create_app(settings)) as client:
        for path in ('/docs', '/redoc', '/openapi.json'):
            assert client.get(path).status_code == 404
