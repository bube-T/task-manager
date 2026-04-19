# routers/tasks.py — Task CRUD routes and stats endpoint.
#
# All routes in this file require authentication (Depends(get_current_user)).
# Every database query filters by owner_id == current_user.id, which means:
#   - Users can only see, edit, and delete their own tasks
#   - If user A requests task ID 99 and it belongs to user B, they get a 404
#     (not 403) — this hides the existence of other users' data entirely
#
# Routes provided:
#   GET  /tasks/stats/summary   → count breakdown: total, completed, pending, overdue
#   GET  /tasks/                → list all tasks (with optional status/priority filters)
#   POST /tasks/                → create a new task
#   GET  /tasks/{task_id}       → fetch one task by ID
#   PATCH /tasks/{task_id}      → partially update a task (only send changed fields)
#   DELETE /tasks/{task_id}     → delete a task permanently

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/stats/summary")
def stats_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return aggregate counts for the logged-in user's tasks.

    Used by the Dashboard page to populate the stat cards:
        total     → all tasks owned by this user
        completed → tasks where status = "completed"
        pending   → tasks where status = "pending"
        overdue   → tasks where due_date is in the past AND status != "completed"

    Note: this route is defined BEFORE /{task_id} so FastAPI does not
    try to interpret "stats" as a task ID integer.
    """
    # Build a base query filtered to this user's tasks only.
    # All four counts re-use this base query with additional filters.
    base = db.query(Task).filter(Task.owner_id == current_user.id)
    now = datetime.now(timezone.utc)

    return {
        "total":     base.count(),
        "completed": base.filter(Task.status == "completed").count(),
        "pending":   base.filter(Task.status == "pending").count(),
        # Overdue = deadline has passed AND the task is not yet done.
        "overdue":   base.filter(Task.due_date < now, Task.status != "completed").count(),
    }


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    # Query parameters — both are optional. Add them to the URL like:
    #   GET /tasks/?status=pending
    #   GET /tasks/?priority=high
    #   GET /tasks/?status=pending&priority=high
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all tasks owned by the current user, with optional filters.

    Filters are additive — providing both status and priority returns
    only tasks that match BOTH conditions.
    Tasks are returned newest-first (ORDER BY created_at DESC).
    """
    # Start with a base query restricted to the current user's tasks.
    q = db.query(Task).filter(Task.owner_id == current_user.id)

    # Conditionally add filters only if the query parameter was provided.
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)

    # Return results ordered by most recently created first.
    return q.order_by(Task.created_at.desc()).all()


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new task for the current user.

    The owner_id is set automatically from the authenticated user —
    the client never needs to (and cannot) specify who owns the task.

    body.model_dump() converts the Pydantic schema to a plain dict,
    which is then unpacked as keyword arguments into the Task constructor.
    """
    # Unpack all fields from the request body and assign this user as the owner.
    task = Task(**body.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)   # Reload from DB so id and created_at are populated
    return task


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Fetch a single task by its ID.

    The query filters by BOTH task ID and owner_id, so if the task
    exists but belongs to a different user, the result is None and we
    return 404 — indistinguishable from "task does not exist".
    This prevents users from probing other users' task IDs.
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id,  # Ownership check — returns 404 for other users' tasks
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Partially update a task. Only the fields included in the request body are changed.

    Uses PATCH (not PUT) because PUT would require sending the full task object.
    PATCH lets the client send only what changed:
        {"status": "completed"}           → only updates status
        {"title": "New name", "priority": "high"}  → only updates those two fields

    Special behaviour: if status is changed to "completed" and the task was
    not already completed, completed_at is automatically set to the current
    UTC time — the client does not need to send it.
    """
    # Verify the task exists and belongs to this user.
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id,
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # exclude_unset=True is critical for PATCH behaviour.
    # It only includes fields the client explicitly sent in the request body.
    # Without it, all Optional fields would be included as None, wiping existing data.
    updates = body.model_dump(exclude_unset=True)

    # Auto-complete logic: if the status is being changed TO "completed"
    # and it wasn't already completed, record the exact moment it was finished.
    # setdefault() only sets completed_at if the client did not already provide one.
    if updates.get("status") == "completed" and task.status != "completed":
        updates.setdefault("completed_at", datetime.now(timezone.utc))

    # Apply each changed field to the ORM object.
    # setattr(task, "status", "completed") is equivalent to task.status = "completed"
    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()        # Persist the changes to the database
    db.refresh(task)   # Reload the row to reflect any DB-side changes
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete a task.

    Returns HTTP 204 No Content on success — no response body is sent.
    Returns 404 if the task does not exist or belongs to another user.
    """
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == current_user.id,  # Users can only delete their own tasks
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)   # Stage the row for deletion
    db.commit()       # Execute the DELETE in the database
    # 204 responses must have no body — FastAPI handles this automatically
