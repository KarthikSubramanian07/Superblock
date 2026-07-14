"""Shared auth and demo-mode helpers for mutating API routes."""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import get_auth0_user
from app.settings import get_settings

optional_bearer = HTTPBearer(auto_error=False)


def demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "true").strip().lower() in {"1", "true", "yes", "on"}


def require_write_access(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> dict:
    """
    Gate write/control routes.

    - DEMO_MODE=true (default): allow unauthenticated local/demo use.
    - DEMO_MODE=false: require a valid Auth0 bearer token when Auth0 is configured;
      otherwise reject (misconfigured production).
    """
    if demo_mode_enabled():
        return {"mode": "demo"}

    settings = get_settings()
    if not settings.auth0_domain or not settings.auth0_audience:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DEMO_MODE is false but AUTH0_DOMAIN/AUTH0_AUDIENCE are not set",
        )
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_auth0_user(credentials)
