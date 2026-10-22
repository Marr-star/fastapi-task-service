"""Shared bearer API key for a single trusted team; not user authentication."""
from secrets import compare_digest
from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False, scheme_name='TeamApiKey', description='Paste TASK_API_KEY. This demo uses a shared team key, not per-user accounts.')


def require_api_key(request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    expected = request.app.state.settings.api_key.get_secret_value().encode()
    supplied = credentials.credentials.encode() if credentials else b''
    if not compare_digest(supplied, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Missing or invalid API key',
                            headers={'WWW-Authenticate': 'Bearer'})
