"""
Authentication service — resolves a Bearer token to a local User.

Supports two providers controlled by AUTH_PROVIDER env var:
  • local  – signs & verifies JWTs with JWT_SECRET_KEY  (dev / testing)
  • supabase – verifies JWTs signed by Supabase using SUPABASE_JWT_SECRET
"""

import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.models import Role, User, UserRole
from app.utils.database import SessionLocal

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "local")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

security = HTTPBearer()

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def create_dev_token(
    sub: str,
    email: str,
    roles: List[str],
    display_name: Optional[str] = None,
) -> str:
    """Create a JWT for local dev/testing."""
    payload = {
        "sub": sub,
        "email": email,
        "roles": roles,
        "display_name": display_name or email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    """Decode and verify a JWT using the configured provider's secret."""
    secret = SUPABASE_JWT_SECRET if AUTH_PROVIDER == "supabase" else JWT_SECRET_KEY

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured for the active auth provider.",
        )

    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
        )

    return payload


# ---------------------------------------------------------------------------
# User resolution
# ---------------------------------------------------------------------------


def _get_or_create_user_from_token(db: Session, payload: dict) -> User:
    """Find or create the local user that matches the token payload."""
    sub = payload.get("sub")
    email = payload.get("email")
    display_name = payload.get("display_name") or email
    provider = AUTH_PROVIDER

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim.",
        )

    # Look up by (auth_provider, auth_subject)
    user = (
        db.query(User)
        .filter(User.auth_provider == provider, User.auth_subject == sub)
        .first()
    )

    if not user:
        user = User(
            auth_provider=provider,
            auth_subject=sub,
            email=email,
            display_name=display_name,
            name=display_name,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Assign default role from token (or "patient")
        token_roles = payload.get("roles", ["patient"])
        for role_code in token_roles:
            role = db.query(Role).filter(Role.code == role_code).first()
            if role:
                db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    return user


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: extracts the Bearer token, decodes it, returns a User."""
    payload = _decode_token(credentials.credentials)
    return _get_or_create_user_from_token(db, payload)


def _get_user_role_codes(db: Session, user: User) -> List[str]:
    """Return the list of role codes assigned to a user."""
    return [
        ur.role.code
        for ur in db.query(UserRole).filter(UserRole.user_id == user.id).all()
    ]


def require_role(role_code: str):
    """Dependency factory: current user must have a specific role."""

    def _check(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        codes = _get_user_role_codes(db, user)
        if role_code not in codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_code}' required.",
            )
        return user

    return _check


def require_any_role(role_codes: List[str]):
    """Dependency factory: current user must have at least one of the roles."""

    def _check(
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        codes = _get_user_role_codes(db, user)
        if not set(role_codes) & set(codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {role_codes} required.",
            )
        return user

    return _check
