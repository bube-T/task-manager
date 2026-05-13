from datetime import datetime
from pydantic import BaseModel


class NoteCreate(BaseModel):
    content: str


class NoteOut(BaseModel):
    id: int
    task_id: int
    owner_id: int
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}
