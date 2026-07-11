"""
Auth Service.

Business logic for user authentication and session management.
Handles registration, login, token refresh, and password management.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.database import get_database
from app.auth.models import User, UserRole, RefreshToken

logger = get_logger("app.auth.service")

# --------------------------------------------------------------------------- #
# Password Hashing (Argon2 via passlib)
# --------------------------------------------------------------------------- #

try:
    from passlib.hash import argon2

    _hash_ctx = argon2.using(
        time_cost=3,
        memory_cost=65536,  # 64 MB
        parallelism=4,
        salt_size=16,
    )
    _has_argon2 = True
except ImportError:
    from passlib.hash import pbkdf2_sha256

    _hash_ctx = pbkdf2_sha256.using(rounds=600_000)
    _has_argon2 = False
    logger.warning("Argon2 not available, falling back to PBKDF2-SHA256")


def _hash_password(password: str) -> str:
    return _hash_ctx.hash(password)


def _verify_password(password: str, hashed: str) -> bool:
    try:
        return _hash_ctx.verify(password, hashed)
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# JWT Helpers
# --------------------------------------------------------------------------- #

def _create_access_token(user_id: str, role: str) -> Tuple[str, int]:
    """Create a JWT access token.

    Returns:
        Tuple of (token_string, expires_in_seconds).
    """
    settings = get_settings()
    from jose import jwt

    expires_in = settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        settings.AUTH_SECRET_KEY,
        algorithm=settings.AUTH_ALGORITHM,
    )
    return token, expires_in


def _decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    settings = get_settings()
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            token,
            settings.AUTH_SECRET_KEY,
            algorithms=[settings.AUTH_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        return None


# --------------------------------------------------------------------------- #
# Auth Service
# --------------------------------------------------------------------------- #

class AuthService:
    """Service for authentication and user management."""

    def __init__(self):
        self._db = get_database()

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #

    async def register(
        self,
        email: str,
        username: str,
        password: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new user account.

        Returns:
            Dict with user data (no tokens — user must log in).

        Raises:
            ValueError: If email or username already exists.
        """
        email = email.strip().lower()
        username = username.strip()

        async with self._db.session() as session:
            # Check existing email
            existing = await session.execute(
                select(User).where(User.email == email)
            )
            if existing.scalar_one_or_none():
                raise ValueError("Email already registered")

            # Check existing username
            existing = await session.execute(
                select(User).where(User.username == username)
            )
            if existing.scalar_one_or_none():
                raise ValueError("Username already taken")

            user = User(
                id=str(uuid.uuid4()),
                email=email,
                username=username,
                display_name=display_name or username,
                hashed_password=_hash_password(password),
                role=UserRole.USER,
            )
            session.add(user)
            logger.info(f"User registered: {user.id} ({email})")
            return user.to_dict()

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #

    async def login(
        self,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        """Authenticate a user and return tokens.

        Accepts username OR email as the credential.

        Returns:
            Dict with access_token, refresh_token, expires_in, user.

        Raises:
            ValueError: If credentials are invalid or account is locked.
        """
        async with self._db.session() as session:
            user = await self._authenticate(session, username, password)
            if not user:
                raise ValueError("Invalid credentials")

            # Generate tokens
            access_token, expires_in = _create_access_token(
                user.id, user.role.value,
            )
            refresh_token = await self._create_refresh_token(session, user.id)

            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            session.add(user)

            logger.info(f"User logged in: {user.id}")
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "user": user.to_dict(),
            }

    # ------------------------------------------------------------------ #
    # Token Refresh
    # ------------------------------------------------------------------ #

    async def refresh_token(
        self,
        refresh_token_str: str,
    ) -> Dict[str, Any]:
        """Exchange a refresh token for a new access token.

        Returns:
            Dict with new access_token, refresh_token (rotated), expires_in, user.

        Raises:
            ValueError: If the refresh token is invalid, expired, or revoked.
        """
        async with self._db.session() as session:
            stored = await self._validate_refresh_token(session, refresh_token_str)
            if not stored:
                raise ValueError("Invalid or expired refresh token")

            # Revoke the old refresh token (rotation)
            stored.is_revoked = True
            stored.revoked_at = datetime.now(timezone.utc)
            session.add(stored)

            # Fetch user
            result = await session.execute(
                select(User).where(User.id == stored.user_id)
            )
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                raise ValueError("User account is inactive")

            # Issue new tokens
            access_token, expires_in = _create_access_token(
                user.id, user.role.value,
            )
            new_refresh_token = await self._create_refresh_token(
                session, user.id,
            )

            logger.info(f"Token refreshed for user: {user.id}")
            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": expires_in,
                "user": user.to_dict(),
            }

    async def logout(self, refresh_token_str: str) -> None:
        """Revoke a refresh token (logout)."""
        async with self._db.session() as session:
            # Hash the incoming token to look it up
            token_hash = hashlib.sha256(refresh_token_str.encode()).hexdigest()

            result = await session.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False,  # noqa: E712
                )
            )
            stored = result.scalar_one_or_none()
            if stored:
                stored.is_revoked = True
                stored.revoked_at = datetime.now(timezone.utc)
                session.add(stored)
                logger.info(f"Refresh token revoked: {stored.id}")

    # ------------------------------------------------------------------ #
    # User Management
    # ------------------------------------------------------------------ #

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        async with self._db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            return user.to_dict() if user else None

    async def update_user(
        self,
        user_id: str,
        data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update user profile fields."""
        allowed_fields = {"display_name", "avatar_url", "preferences"}
        async with self._db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return None

            for key, value in data.items():
                if key in allowed_fields:
                    if key == "preferences" and isinstance(value, dict):
                        import json
                        setattr(user, key, json.dumps(value))
                    else:
                        setattr(user, key, value)

            session.add(user)
            return user.to_dict()

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change a user's password."""
        async with self._db.session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                return False

            if not _verify_password(current_password, user.hashed_password):
                return False

            user.hashed_password = _hash_password(new_password)
            session.add(user)

            # Revoke all existing refresh tokens
            await session.execute(
                delete(RefreshToken).where(RefreshToken.user_id == user_id)
            )

            logger.info(f"Password changed for user: {user_id}")
            return True

    # ------------------------------------------------------------------ #
    # Internal Helpers
    # ------------------------------------------------------------------ #

    async def _authenticate(
        self,
        session: AsyncSession,
        username: str,
        password: str,
    ) -> Optional[User]:
        """Verify username/email + password combo."""
        # Try username first, then email
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            result = await session.execute(
                select(User).where(User.email == username)
            )
            user = result.scalar_one_or_none()

        if not user:
            return None

        if not user.is_active:
            logger.warning(f"Login attempt on inactive account: {user.id}")
            return None

        if not _verify_password(password, user.hashed_password):
            return None

        return user

    async def _create_refresh_token(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> str:
        """Generate and store a refresh token.

        Returns:
            The raw refresh token string (hash stored in DB).
        """
        settings = get_settings()
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.AUTH_REFRESH_TOKEN_EXPIRE_DAYS,
        )

        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(rt)
        return raw_token

    async def _validate_refresh_token(
        self,
        session: AsyncSession,
        raw_token: str,
    ) -> Optional[RefreshToken]:
        """Look up and validate a refresh token."""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False,  # noqa: E712
            )
        )
        stored = result.scalar_one_or_none()

        if not stored:
            return None

        # Check expiry (handle SQLite returning naive datetimes)
        expires_at = stored.expires_at
        if expires_at is not None:
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                stored.is_revoked = True
                session.add(stored)
                return None

        return stored