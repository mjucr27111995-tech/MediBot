"""Demo user store and authentication helpers.

Uses bcrypt directly (avoiding passlib compatibility issues with newer bcrypt versions).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import Settings


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# Pre-hashed demo passwords
DEMO_USERS = {
    "dr.mehta": {
        "password_hash": _hash_password("doctor"),
        "role": "doctor",
        "full_name": "Dr. Anil Mehta",
    },
    "nurse.priya": {
        "password_hash": _hash_password("nurse"),
        "role": "nurse",
        "full_name": "Priya Sharma",
    },
    "billing.ravi": {
        "password_hash": _hash_password("billing"),
        "role": "billing_executive",
        "full_name": "Ravi Kumar",
    },
    "tech.anand": {
        "password_hash": _hash_password("technician"),
        "role": "technician",
        "full_name": "Anand Rao",
    },
    "admin.sys": {
        "password_hash": _hash_password("admin"),
        "role": "admin",
        "full_name": "System Admin",
    },
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Verify credentials against the demo user store."""
    user = DEMO_USERS.get(username)
    if user is None:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return {"username": username, "role": user["role"], "full_name": user["full_name"]}


def create_access_token(data: dict, settings: Settings) -> str:
    """Create a JWT token with expiry."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
