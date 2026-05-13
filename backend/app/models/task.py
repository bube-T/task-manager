# models/task.py — SQLAlchemy ORM model for the "tasks" table.
# This class describes every column that a task row contains in PostgreSQL.
#
# Key design decision: every task has an owner_id foreign key.
# This links each task to exactly one user. All task queries filter by
# owner_id == current_user.id, so users can only ever see their own tasks.

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func

# Import Base — the shared parent class all models inherit from.
from ..database import Base


class Task(Base):
    # __tablename__ tells SQLAlchemy which PostgreSQL table this maps to.
    __tablename__ = "tasks"

    # Primary key — auto-incremented. Uniquely identifies each task row.
    id = Column(Integer, primary_key=True, index=True)

    # The task title. Required — a task must have a name.
    title = Column(String, nullable=False)

    # Optional longer description. nullable=True means the column can be NULL in the DB.
    description = Column(String, nullable=True)

    # Priority level of the task. Stored as a plain string.
    # Expected values: "low", "medium", "high"
    # default="medium" is a Python-side default — SQLAlchemy sets it before INSERT
    # if no value is provided.
    priority = Column(String, default="medium")

    # Current state of the task. Stored as a plain string.
    # Expected values: "pending", "completed"
    # Starts as "pending" when a task is first created.
    status = Column(String, default="pending")

    # Optional deadline for the task. Stored as a timezone-aware timestamp.
    # Used by the stats endpoint to count overdue tasks:
    #   due_date < now() AND status != "completed"
    due_date = Column(DateTime(timezone=True), nullable=True)

    # Creation timestamp set automatically by PostgreSQL on INSERT.
    # Used to sort tasks by most recently created (ORDER BY created_at DESC).
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Timestamp recorded when the task's status is changed to "completed".
    # Set automatically by the PATCH route — the client does not need to send it.
    # NULL when the task is still pending.
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Foreign key — links this task to the user who owns it.
    # ForeignKey("users.id") references the id column of the users table.
    # nullable=False means every task must have an owner — orphan tasks are not allowed.
    # When a task is created, owner_id is set to current_user.id automatically in the route.
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # How often this task repeats after completion.
    # "none" = one-off task. "daily" / "weekly" / "monthly" = auto-creates next occurrence.
    recurrence = Column(String, default="none", nullable=False, server_default="none")

    # Prevents sending duplicate due-date reminder emails.
    # Reset to False whenever due_date is updated.
    reminder_sent = Column(Boolean, default=False, nullable=False, server_default="false")
