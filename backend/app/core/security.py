# core/security.py — Password hashing and JWT token utilities.
#
# This file handles the two core security concerns of the app:
#
#   1. Passwords — bcrypt hashing so plain-text passwords are never stored
#   2. JWT tokens — creating and verifying the tokens used to authenticate requests
#
# These functions are used in two places:
#   - routers/auth.py: hash_password() on register, verify_password() on login,
#                      create_access_token() to issue the token after login
#   - core/deps.py:    decode_access_token() to identify the user on every request

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import settings


# --- Password hashing ---
# CryptContext manages which hashing algorithm to use.
# schemes=["bcrypt"] means passwords are hashed with bcrypt.
# bcrypt is specifically designed to be slow and CPU-intensive, making
# brute-force attacks impractical even if the hashed database is stolen.
# deprecated="auto" will automatically upgrade older hashes to the current scheme
# if the configuration is ever changed in future.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """
    Takes a plain-text password and returns a bcrypt hash.

    The hash includes a random salt, so the same password produces a
    different hash every time. This prevents attackers from using
    precomputed rainbow tables.

    Example:
        hash_password("mysecret")
        → "$2b$12$eImiTXuWVxfM37uY4JANjQ..."  (changes every call)
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Checks whether a plain-text password matches a stored bcrypt hash.

    passlib extracts the salt from the stored hash, re-hashes the plain
    password with that same salt, then compares the two hashes.

    Example:
        verify_password("mysecret", "$2b$12$eImiTXuWVxfM37uY4JANjQ...")  → True
        verify_password("wrongpass", "$2b$12$eImiTXuWVxfM37uY4JANjQ...") → False
    """
    return pwd_context.verify(plain, hashed)


# --- JWT tokens ---
def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT token containing the given data payload.

    The token encodes who the user is (via the "sub" claim) and when
    it expires (via the "exp" claim). It is signed with SECRET_KEY so
    the server can verify it has not been tampered with.

    The client receives this token at login and must include it in every
    subsequent request header:
        Authorization: Bearer <token>

    Example payload before encoding:
        {"sub": "42", "exp": 1713600000}
        → "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    payload = data.copy()
    # Calculate the exact UTC datetime when this token should stop being valid.
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # Add the expiry to the payload under the standard "exp" JWT claim key.
    payload.update({"exp": expire})
    # Encode and sign the payload. The resulting string is the token.
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decodes and verifies a JWT token. Returns the payload dict if valid,
    or None if the token is invalid, expired, or tampered with.

    python-jose automatically checks:
        - The signature (was this signed with our SECRET_KEY?)
        - The expiry (is "exp" still in the future?)

    Returning None (instead of raising) keeps the error handling logic
    in get_current_user() in one place.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        # JWTError covers: expired tokens, bad signature, malformed token strings.
        return None
