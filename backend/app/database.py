# database.py — SQLAlchemy engine and session setup.
# This file is responsible for three things:
#   1. Creating the engine  — the single connection to the database
#   2. Creating SessionLocal — a factory that produces one session per request
#   3. Defining Base        — the parent class all ORM models inherit from
#
# SQLAlchemy is an ORM (Object Relational Mapper). It lets you write Python
# objects instead of raw SQL. For example, instead of:
#   INSERT INTO tasks (title, owner_id) VALUES ('Buy milk', 1)
# you write:
#   db.add(Task(title="Buy milk", owner_id=1))
#   db.commit()

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings


# --- Engine ---
# The engine manages the raw connection to PostgreSQL.
# It reads DATABASE_URL from .env via the settings object.
engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping=True: before handing out a connection from the pool,
    # SQLAlchemy sends a lightweight "SELECT 1" to make sure it is still alive.
    # This prevents errors if the database container was restarted.
    pool_pre_ping=True,
    # pool_size: how many connections to keep open permanently in the pool.
    # Each concurrent request uses one connection while it is processing.
    pool_size=10,
    # max_overflow: extra connections allowed when all pool_size slots are busy.
    # Total max simultaneous connections = pool_size + max_overflow = 30.
    max_overflow=20,
)

# --- SessionLocal ---
# SessionLocal is a factory class. Calling SessionLocal() creates a new
# database session — think of a session as one "conversation" with the database.
# One session is opened per request and closed when the request finishes.
SessionLocal = sessionmaker(
    autocommit=False,  # Never commit automatically. We call db.commit() explicitly
                       # so we control exactly when data is written.
    autoflush=False,   # Don't push pending changes to the DB until commit() is called.
                       # This prevents partial writes if an error occurs mid-request.
    bind=engine,       # Link this factory to the engine created above.
)

# --- Base ---
# Base is the parent class that all ORM model classes inherit from.
# It holds shared metadata — the registry of table names, columns, and relationships.
# When Alembic runs --autogenerate, it reads Base.metadata to discover what
# tables should exist and compares them against the actual database.
Base = declarative_base()
