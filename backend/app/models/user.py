# models/user.py — SQLAlchemy ORM model for the "users" table.
# This class describes the structure of the users table in PostgreSQL.
# Each class attribute maps directly to a column in the table.
#
# SQLAlchemy uses this class to:
#   - Generate the CREATE TABLE SQL (via Alembic migrations)
#   - Build SELECT, INSERT, UPDATE, DELETE queries for you in Python
#
# IMPORTANT: The plain-text password is NEVER stored here.
# Only the bcrypt hash is stored in hashed_password. Even if the database
# were compromised, the original password cannot be recovered from the hash.

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

# Import Base — the shared parent class all models inherit from.
# Base holds the metadata registry that Alembic reads during autogenerate.
from ..database import Base


class User(Base):
    # __tablename__ tells SQLAlchemy which table in PostgreSQL this class maps to.
    __tablename__ = "users"

    # Primary key — auto-incremented integer. Every user gets a unique ID.
    # index=True creates a B-tree index for fast lookups by id.
    id = Column(Integer, primary_key=True, index=True)

    # The user's email address used as their login username.
    # unique=True enforces at the database level that no two users share an email.
    # index=True speeds up the lookup in the login query: WHERE email = ?
    # nullable=False means this column is required — the DB will reject a row without it.
    email = Column(String, unique=True, index=True, nullable=False)

    # The bcrypt hash of the user's password. Never the plain-text password.
    # Example value: "$2b$12$eImiTXuWVxfM37uY4JANjQ..."
    hashed_password = Column(String, nullable=False)

    # Timestamp set automatically by PostgreSQL when the row is first inserted.
    # server_default=func.now() means the DB sets this — not Python —
    # so it is always in the database's timezone and requires no application code.
    # timezone=True stores the timestamp with UTC offset (TIMESTAMPTZ in Postgres).
    created_at = Column(DateTime(timezone=True), server_default=func.now())
