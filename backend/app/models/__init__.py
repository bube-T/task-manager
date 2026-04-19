# models/__init__.py — Exports all ORM models from a single location.
#
# Importing both models here serves two purposes:
#
# 1. Alembic autogenerate: alembic/env.py imports Base and these models.
#    For Alembic to detect a table it must be imported BEFORE Base.metadata
#    is read. If a model is never imported, Alembic will not know it exists
#    and will not generate the CREATE TABLE migration for it.
#
# 2. Convenience: other parts of the app can import from app.models directly:
#    from app.models import User, Task
#    instead of reaching into the individual files.

from .user import User
from .task import Task
