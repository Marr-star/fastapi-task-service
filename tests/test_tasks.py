from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from conftest import TEST_KEY


def test_full_task_lifecycle(client):
    response = client.post('/tasks', json={'title': 'Review invoice', 'owner': 'Mariam', 'priority': 'high', 'due_date': '2026-12-01'})
    assert response.status_code == 201
    task = response.json()
    assert response.headers['Location'] == f'/tasks/{task["id"]}'
    assert task['status'] == 'todo'
    assert task['priority'] == 'high'
    assert task['owner'] == 'Mariam'
    assert datetime.fromisoformat(task['created_at'].replace('Z', '+00:00')).utcoffset().total_seconds() == 0
    url = f'/tasks/{task["id"]}'
    assert client.get(url).json() == task
    updated = client.patch(url, json={'status': 'in_progress', 'title': '  Review paid invoice  '})
    assert updated.status_code == 200
    assert updated.json()['title'] == 'Review paid invoice'
    assert updated.json()['due_date'] == '2026-12-01'
    assert updated.json()['created_at'] == task['created_at']
    deleted = client.delete(url)
    assert deleted.status_code == 204
    assert deleted.content == b''
    assert client.get(url).status_code == 404


@pytest.mark.parametrize('payload', [
    {}, {'title': ''}, {'title': '   '}, {'title': 'a' * 201}, {'title': 123},
    {'title': 'x', 'status': 'blocked'}, {'title': 'x', 'priority': 'urgent'},
    {'title': 'x', 'due_date': '2026-02-30'}, {'title': 'x', 'due_date': 0},
    {'title': 'x', 'owner': ' '}, {'title': 'x', 'owner': 'a' * 101},
    {'title': 'x', 'description': 'x' * 5001}, {'title': 'x', 'id': 99},
    {'title': 'x', 'created_at': '2026-01-01'},
])
def test_invalid_create_is_rejected(client, payload):
    assert client.post('/tasks', json=payload).status_code == 422
    assert client.get('/tasks').json()['total'] == 0


@pytest.mark.parametrize('payload', [{}, {'title': None}, {'status': None}, {'priority': None}, {'title': '  '}, {'unknown': 1}, {'due_date': 'tomorrow'}])
def test_invalid_patch_leaves_record_unchanged(client, payload):
    task = client.post('/tasks', json={'title': 'Original'}).json()
    url = f'/tasks/{task["id"]}'
    assert client.patch(url, json=payload).status_code == 422
    assert client.get(url).json() == task


def test_nullable_fields_can_be_cleared(client):
    task = client.post('/tasks', json={'title': 'Clear fields', 'owner': 'Mariam', 'description': 'Details', 'due_date': '2026-01-01'}).json()
    response = client.patch(f'/tasks/{task["id"]}', json={'owner': None, 'description': None, 'due_date': None})
    assert response.status_code == 200
    assert all(response.json()[field] is None for field in ('owner', 'description', 'due_date'))


def test_filtering_pagination_and_stable_order(client):
    for i in range(6):
        client.post('/tasks', json={'title': f'Task {i}', 'status': 'done' if i % 2 else 'todo', 'owner': 'Mariam' if i < 4 else 'Ali', 'priority': 'high' if i < 4 else 'low'})
    page = client.get('/tasks?status=todo&limit=1&offset=1').json()
    assert page['total'] == 3
    assert len(page['items']) == 1
    assert page['items'][0]['title'] == 'Task 2'
    assert (page['limit'], page['offset']) == (1, 1)
    combined = client.get('/tasks?status=done&owner=Mariam&priority=high').json()
    assert combined['total'] == 2
    assert [t['title'] for t in combined['items']] == ['Task 1', 'Task 3']
    assert client.get('/tasks?offset=999').json()['items'] == []


@pytest.mark.parametrize('query', ['limit=0', 'limit=101', 'offset=-1', 'status=unknown', 'priority=urgent', 'limit=nope', 'owner='])
def test_invalid_filters_and_pagination(client, query):
    assert client.get(f'/tasks?{query}').status_code == 422


@pytest.mark.parametrize('method', ['get', 'patch', 'delete'])
def test_missing_task_is_404(client, method):
    kwargs = {'json': {'title': 'No task'}} if method == 'patch' else {}
    response = getattr(client, method)('/tasks/99999', **kwargs)
    assert response.status_code == 404
    assert response.json()['detail'] == 'Task not found'


@pytest.mark.parametrize('value', ['0', '-1', 'invalid'])
def test_bad_id_is_422(client, value):
    assert client.get(f'/tasks/{value}').status_code == 422


def test_empty_list(client):
    assert client.get('/tasks').json() == {'items': [], 'total': 0, 'limit': 20, 'offset': 0}


def test_owner_filter_treats_sql_as_literal(client):
    client.post('/tasks', json={'title': 'Keep this', 'owner': 'Mariam'})
    assert client.get('/tasks', params={'owner': "' OR 1=1 --"}).json()['total'] == 0
    assert client.get('/tasks').json()['total'] == 1


def test_file_database_survives_app_restart(settings):
    headers = {'Authorization': f'Bearer {TEST_KEY}'}
    with TestClient(create_app(settings)) as first:
        task = first.post('/tasks', headers=headers, json={'title': 'Persistent task'}).json()
    with TestClient(create_app(settings)) as second:
        assert second.get(f'/tasks/{task["id"]}', headers=headers).json()['title'] == 'Persistent task'


def test_deleted_task_url_never_resolves_to_a_new_task(client):
    first = client.post('/tasks', json={'title': 'Original task'}).json()
    original_url = f'/tasks/{first["id"]}'
    assert client.delete(original_url).status_code == 204
    second = client.post('/tasks', json={'title': 'Different task'}).json()
    assert second['id'] > first['id']
    assert client.get(original_url).status_code == 404
