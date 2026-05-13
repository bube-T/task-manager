import calendar
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.task import Task
from app.models.note import TaskNote
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _next_due(due_date: datetime, recurrence: str) -> datetime:
    if recurrence == "daily":
        return due_date + timedelta(days=1)
    if recurrence == "weekly":
        return due_date + timedelta(weeks=1)
    if recurrence == "monthly":
        month = due_date.month + 1
        year = due_date.year + (1 if month > 12 else 0)
        month = month if month <= 12 else 1
        day = min(due_date.day, calendar.monthrange(year, month)[1])
        return due_date.replace(year=year, month=month, day=day)
    return due_date


def _with_note_count(task: Task, db: Session) -> dict:
    count = db.query(TaskNote).filter(TaskNote.task_id == task.id).count()
    data = {c.name: getattr(task, c.name) for c in task.__table__.columns}
    data["note_count"] = count
    return data


@router.get("/stats/summary")
def stats_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = db.query(Task).filter(Task.owner_id == current_user.id)
    now = datetime.now(timezone.utc)
    return {
        "total":     base.count(),
        "completed": base.filter(Task.status == "completed").count(),
        "pending":   base.filter(Task.status == "pending").count(),
        "overdue":   base.filter(Task.due_date < now, Task.status != "completed").count(),
    }


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Task).filter(Task.owner_id == current_user.id)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    tasks = q.order_by(Task.created_at.desc()).all()
    return [_with_note_count(t, db) for t in tasks]


@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    body: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = Task(**body.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return _with_note_count(task, db)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _with_note_count(task, db)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    updates = body.model_dump(exclude_unset=True)

    completing = updates.get("status") == "completed" and task.status != "completed"

    if completing:
        updates.setdefault("completed_at", datetime.now(timezone.utc))

        # If recurring, create the next occurrence before applying updates
        if task.recurrence and task.recurrence != "none" and task.due_date:
            next_task = Task(
                title=task.title,
                description=task.description,
                priority=task.priority,
                recurrence=task.recurrence,
                due_date=_next_due(task.due_date, task.recurrence),
                owner_id=task.owner_id,
                status="pending",
            )
            db.add(next_task)

    # Reset reminder_sent if due_date is being changed
    if "due_date" in updates:
        updates["reminder_sent"] = False

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return _with_note_count(task, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
