# Security decisions and production changes

## Demo authentication

This API deliberately uses one high-entropy shared bearer key for a trusted team. There is no registration endpoint, password storage, JWT issuance or fabricated login flow. A missing, weak or placeholder key prevents startup. The example environment file contains no usable credential. Tests use an isolated test-only key.

A shared key is easy to demonstrate in Swagger and curl, but cannot identify individuals, revoke just one person or enforce ownership. The `owner` field is a display label. Every key holder can create, read, change and delete every task. Keys do not expire automatically. Rotate the environment value and restart the app to invalidate the previous key.

Use HTTPS whenever requests leave localhost; bearer keys are credentials. Never commit `.env`, put a key in a URL, embed it in a public frontend, or include it in screenshots or logs. Interactive docs are enabled locally; set `TASK_DOCS_ENABLED=false` when they should not be public.

## Browser access

CORS defaults to an empty list, with no wildcard and no credentialed cross-origin sessions. Configure exact origins only when a browser client needs them. CORS does not block curl or other non-browser clients and does not replace authentication.

## Database and data

SQLAlchemy parameterizes queries. Each request uses a dedicated session and failed work is rolled back. SQLite is a development database for a small workload, with a single local file and limited concurrent writes. The liveness endpoint confirms the process is running; it does not prove database readiness.

Creation time is recorded as UTC and returned with an explicit timezone. No user-controlled creation timestamp is accepted. This version has no audit history or optimistic locking: simultaneous updates are last-write-wins, and offset pages can shift when records change.

## Before real production

1. Replace the shared key with managed OIDC/OAuth2 authentication and verify issuer, audience, expiration and signatures through a maintained library. Add actual user IDs, team membership and task authorization.
2. Terminate HTTPS at a trusted proxy, configure trusted hosts and proxy headers deliberately, and keep internal application ports private.
3. Use a managed relational database suited to concurrency. Add Alembic migrations; `create_all()` creates tables but does not migrate existing schemas. Add backups and a tested restore process.
4. Store credentials in a secret manager with rotation, revocation and least privilege. Add rate limits and request-size limits at the ingress.
5. Add structured logs without credentials, request IDs, error monitoring, audit events, readiness checks and operational alerts.
6. Pin and review dependencies and container images, scan them for vulnerabilities, and validate the deployed service under representative load. Add integration tests for the chosen production database.

These are concrete next steps, not features implemented by this demonstration.
