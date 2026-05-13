# schemas/task.py — Pydantic schemas for task-related request and response data.
#
# There are three separate schemas for tasks:
#
#   TaskCreate  — fields accepted when creating a new task (POST /tasks/)
#   TaskUpdate  — fields accepted when updating a task (PATCH /tasks/{id})
#   TaskOut     — fields returned to the client in every task response
#
# Why three schemas instead of one?
#   - TaskCreate: title is required, everything else has sensible defaults
#   - TaskUpdate: EVERY field is Optional because PATCH only updates what you send.
#     Sending {"status": "completed"} should not wipe the title.
#   - TaskOut: the read-only fields (id, created_at, owner_id) only belong in responses.

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# --- Input schema: creating a task ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"
    due_date: Optional[datetime] = None
    recurrence: Optional[str] = "none"


# --- Input schema: updating a task (PATCH) ---
class TaskUpdate(BaseModel):
    # Every field is Optional with a default of None.
    # model_dump(exclude_unset=True) in the route will only return the fields
    # the client actually sent — so only those fields get updated in the DB.
    # Example: sending {"status": "completed"} will ONLY update status,
    # leaving title, description, priority, and due_date unchanged.
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    recurrence: Optional[str] = None


# --- Output schema: what the client receives about a task ---
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    owner_id: int
    recurrence: str
    note_count: Optional[int] = 0

    # from_attributes=True allows Pydantic to read from SQLAlchemy ORM objects.
    # Without this, returning a Task ORM object directly would raise a validation error.
    model_config = {"from_attributes": True}
