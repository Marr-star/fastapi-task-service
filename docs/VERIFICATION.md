# Verification record

Verified locally on Python 3.12 on 22 October 2026.

| Check | Result | Evidence |
| --- | --- | --- |
| Automated tests | Passed | 75 tests passed with pytest |
| Uvicorn startup and liveness | Passed | `/health` returned 200 and `{"status":"ok"}` |
| Unauthenticated task request | Passed | `/tasks` returned 401 |
| Create over live HTTP | Passed | POST `/tasks` returned 201 |
| API to database | Passed | Created title was independently read from the SQLite row |
| Filtered list and update | Passed | Filtered list returned the task; PATCH changed status to `done` |
| Swagger UI | Passed | Actual `/docs` page rendered; browser authorized and executed GET `/tasks` with 200 |
| Browser console | Passed | No page JavaScript errors during the verified flow |
| Delete and missing record | Passed | DELETE returned 204; subsequent GET returned 404 |
| Persistence after restart | Passed | Automated test closed and recreated the app against the same SQLite file |
| OpenAPI | Passed | Security metadata tested; generated contract saved as `openapi.json` |
| Docker build/run | Not run locally | Docker is unavailable in the build environment; CI includes build and live HTTP/container-persistence checks |
| Deleted task ID reuse | Passed | Regression test confirms a deleted URL remains 404 after another task is created |
| Public deployment | Not deployed | Local development and packaging only |

The Swagger screenshot is captured before entering credentials. During browser verification, the official Swagger JavaScript and CSS were cached locally because direct browser CDN access was unavailable in the verification environment. The API HTML, OpenAPI schema and endpoint responses came from the running application.

The current Starlette test client emits one upstream deprecation warning about HTTPX. It does not fail the suite; HTTPX is pinned in the development dependencies. Revisit that test transport when upgrading dependencies.

Reproduce API checks with `python -m pytest -q`. To recapture `/docs`, start the service, install the optional Playwright browser tooling, and run `python docs/capture_docs.py`. This optional tooling is not required to run the API.
