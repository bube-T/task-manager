from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models.note import TaskNote
from app.models.task import Task
from app.models.user import User
from app.schemas.note import NoteCreate, NoteOut

router = APIRouter(prefix="/tasks/{task_id}/notes", tags=["notes"])


def get_task_or_404(task_id: int, current_user: User, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/", response_model=list[NoteOut])
def list_notes(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_task_or_404(task_id, current_user, db)
    return (
        db.query(TaskNote)
        .filter(TaskNote.task_id == task_id)
        .order_by(TaskNote.created_at.desc())
        .all()
    )


@router.post("/", response_model=NoteOut, status_code=201)
def create_note(
    task_id: int,
    body: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_task_or_404(task_id, current_user, db)
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Note content cannot be empty")
    note = TaskNote(task_id=task_id, owner_id=current_user.id, content=body.content.strip())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(
    task_id: int,
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_task_or_404(task_id, current_user, db)
    note = db.query(TaskNote).filter(TaskNote.id == note_id, TaskNote.owner_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
