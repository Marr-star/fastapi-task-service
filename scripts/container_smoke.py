"""Verify the built Docker image over real HTTP, including volume persistence.

Run: python scripts/container_smoke.py task-service:test
Uses only the Python standard library. Cleans up its own containers and volume.
"""
import json
import os
import secrets
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener


def main():
    image = sys.argv[1] if len(sys.argv) > 1 else 'task-service:test'
    name = 'task-smoke-' + secrets.token_hex(6)
    volume = name + '-data'
    key = secrets.token_urlsafe(32)
    env = {**os.environ, 'TASK_API_KEY': key}
    opener = build_opener(ProxyHandler({}))

    def docker(*args):
        return subprocess.check_output(['docker', *args], env=env, text=True).strip()

    def start():
        docker('run', '-d', '--name', name, '-p', '127.0.0.1::8000',
               '--env', 'TASK_API_KEY', '--env', 'TASK_DATABASE_URL=sqlite:////data/tasks.db',
               '-v', f'{volume}:/data', image)
        port = docker('port', name, '8000/tcp').splitlines()[0].rsplit(':', 1)[1]
        base = f'http://127.0.0.1:{port}'
        for _ in range(100):
            try:
                with opener.open(base + '/health', timeout=1) as response:
                    if response.status == 200:
                        return base
            except (URLError, TimeoutError):
                time.sleep(.2)
        raise RuntimeError('Container did not become live within the startup deadline')

    def request(base, method, path, payload=None, authenticated=True):
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers['Authorization'] = f'Bearer {key}'
        data = json.dumps(payload).encode() if payload is not None else None
        req = Request(base + path, data=data, headers=headers, method=method)
        try:
            response = opener.open(req, timeout=5)
        except HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            return response.status, json.loads(body) if body else None

    try:
        docker('volume', 'create', volume)
        base = start()
        assert docker('exec', name, 'id', '-u') != '0', 'Container must not run as root'
        assert request(base, 'GET', '/tasks', authenticated=False)[0] == 401
        code, task = request(base, 'POST', '/tasks', {'title': 'Container persistence check'})
        assert code == 201
        path = f'/tasks/{task["id"]}'
        code, updated = request(base, 'PATCH', path, {'status': 'done'})
        assert code == 200 and updated['status'] == 'done'
        docker('rm', '-f', name)
        base = start()  # New container, same named volume.
        code, stored = request(base, 'GET', path)
        assert code == 200 and stored['title'] == task['title'] and stored['status'] == 'done'
        assert request(base, 'DELETE', path)[0] == 204
        assert request(base, 'GET', path)[0] == 404
        print('Container smoke passed: non-root user, auth, CRUD and persistence across replacement')
    except Exception:
        subprocess.run(['docker', 'logs', name], check=False)
        raise
    finally:
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        subprocess.run(['docker', 'volume', 'rm', volume], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


if __name__ == '__main__':
    main()
