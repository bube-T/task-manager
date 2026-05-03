# schemas/user.py — Pydantic schemas for user-related request and response data.
#
# Schemas are separate from ORM models. They define:
#   - What fields the API *accepts* in a request body (input schemas)
#   - What fields the API *returns* in a response (output schemas)
#
# This separation is important for security. The User ORM model has a
# hashed_password column, but UserOut does NOT include it — so that field
# is never accidentally leaked into an API response.
#
# Pydantic validates every incoming value automatically. If a required field
# is missing or the wrong type, FastAPI returns a 422 error before your route
# code even runs.

from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


# --- Input schema: creating a new user ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


# --- Output schema: what gets returned to the client about a user ---
class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    # from_attributes=True (formerly orm_mode=True in Pydantic v1) tells Pydantic
    # it can read data from SQLAlchemy ORM objects (which use attribute access)
    # instead of only from plain dictionaries.
    # Without this, returning a User ORM object from a route would raise an error.
    model_config = {"from_attributes": True}


# --- Input schema: changing password ---
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


# --- Output schema: the token returned after a successful login ---
class Token(BaseModel):
    # The signed JWT string the client must include in future requests:
    # Authorization: Bearer <access_token>
    access_token: str

    # Always "bearer" — tells the client what kind of token this is.
    # This follows the OAuth2 standard that Swagger UI expects.
    token_type: str = "bearer"
