# routers/auth.py — Authentication routes.
#
# This router handles everything related to user identity:
#   POST /auth/register  → create a new account
#   POST /auth/token     → log in and receive a JWT
#   GET  /auth/me        → return the currently logged-in user
#
# The prefix="/auth" means all routes in this file are automatically
# prefixed with /auth — so register() maps to POST /auth/register, etc.
# tags=["auth"] groups these routes together in the Swagger UI at /docs.

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, Token, PasswordChange

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.

    Steps:
        1. Check the email is not already registered (emails must be unique)
        2. Hash the plain-text password with bcrypt
        3. Save the new User row to the database
        4. Return the created user (without the password hash)

    Raises:
        400 Bad Request — if the email is already taken
    """
    # Check for an existing user with the same email.
    # We do this before hashing to avoid wasting CPU time on bcrypt
    # if we are going to reject the request anyway.
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the User ORM object. The plain password is hashed here —
    # only the hash is stored in the database, never the original string.
    user = User(email=body.email, hashed_password=hash_password(body.password))

    db.add(user)       # Stage the new user for insertion
    db.commit()        # Write it to the database
    db.refresh(user)   # Reload the row so id and created_at are populated from the DB
    return user        # Serialised through UserOut — hashed_password is excluded


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Log in with email and password. Returns a JWT access token on success.

    OAuth2PasswordRequestForm expects the body as form data (not JSON):
        username=alice@example.com&password=secret
    The Swagger UI /docs "Authorize" button sends exactly this format.
    We use form.username as the email field (OAuth2 standard uses "username").

    Steps:
        1. Look up the user by email
        2. Verify the submitted password against the stored bcrypt hash
        3. Create a JWT token containing the user's ID as the "sub" claim
        4. Return the token

    Raises:
        401 Unauthorized — if the email does not exist or the password is wrong
        Note: we give the same error for both cases to prevent email enumeration
              (an attacker cannot tell whether the email exists or the password is wrong)
    """
    # Find the user by email. form.username is the email — OAuth2 standard naming.
    user = db.query(User).filter(User.email == form.username).first()

    # Reject if user not found OR if the password does not match the stored hash.
    # Both conditions return the same 401 to prevent user enumeration attacks.
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a JWT. The "sub" (subject) claim stores the user's ID as a string.
    # The token is valid for ACCESS_TOKEN_EXPIRE_MINUTES minutes (default: 60).
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.patch("/password", status_code=204)
def change_password(
    body: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(body.new_password)
    db.commit()


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """
    Return the profile of the currently authenticated user.

    This route is protected — a valid JWT must be in the Authorization header.
    get_current_user() handles all token validation and DB lookup before this
    function body runs. If the token is missing or invalid, it returns 401
    automatically and this function is never called.

    Useful for the frontend to confirm a token is still valid and fetch
    the logged-in user's details (e.g. to display their email in the navbar).
    """
    # current_user is already the full User ORM object resolved by get_current_user().
    # Just return it — Pydantic serialises it through UserOut.
    return current_user
