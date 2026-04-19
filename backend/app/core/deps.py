# core/deps.py — Reusable FastAPI dependencies.
#
# A "dependency" in FastAPI is a function declared with Depends().
# FastAPI calls it automatically before the route handler runs,
# injects the return value as an argument, and handles cleanup after.
#
# This file provides two dependencies used across all protected routes:
#
#   get_db()           → opens a database session for the request, closes it after
#   get_current_user() → reads the JWT from the request header and returns the User object
#
# Usage in any route:
#   def my_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#       ...

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User


# OAuth2PasswordBearer tells FastAPI where to look for the token.
# tokenUrl="/auth/token" is the login endpoint that issues tokens.
# FastAPI uses this to render the "Authorize" button in the Swagger UI at /docs.
# On every request, this reads the "Authorization: Bearer <token>" header
# and passes the raw token string to any function that depends on it.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_db():
    """
    Opens a new SQLAlchemy database session for the duration of a request.

    Uses Python's generator pattern (yield) so cleanup always runs:
        1. A session is opened from the connection pool
        2. The session is yielded to the route handler
        3. After the route finishes (success OR exception), the finally
           block closes the session and returns the connection to the pool

    This prevents connection leaks — if the route raises an exception,
    the session is still properly closed.
    """
    db = SessionLocal()   # Get a new session from the factory
    try:
        yield db          # Hand the session to the route
    finally:
        db.close()        # Always runs — even if the route raised an exception


def get_current_user(
    token: str = Depends(oauth2_scheme),   # Reads the Bearer token from the Authorization header
    db: Session = Depends(get_db),         # Gets a DB session to look up the user
) -> User:
    """
    Validates the JWT token and returns the authenticated User object.

    This is the authentication gate for all protected routes. Any route
    that declares Depends(get_current_user) will automatically:
        - Return 401 if no token is present in the header
        - Return 401 if the token is invalid, expired, or tampered with
        - Return 401 if the user ID inside the token no longer exists in the DB
        - Return the User object if everything checks out

    The route handler never sees or touches the token — it just receives
    the already-resolved User object.
    """
    # Pre-build the 401 exception so we can raise it from multiple places
    # without repeating the status code and headers.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        # WWW-Authenticate header is required by the OAuth2 spec for 401 responses.
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Attempt to decode and verify the token.
    # decode_access_token() returns None for any invalid/expired token.
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Extract the user ID from the token payload.
    # "sub" (subject) is the standard JWT claim we use to store the user ID.
    # It was set in create_access_token() as {"sub": str(user.id)}.
    user_id: int | None = payload.get("sub")
    if user_id is None:
        # Token is valid but missing the "sub" field — should never happen
        # with tokens we issued, but guard against it anyway.
        raise credentials_exception

    # Look up the user in the database.
    # The token proves the user was authenticated at login time, but the
    # account could have been deleted since then — so we always verify.
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    # Return the full User ORM object to the route handler.
    return user
