"""Task persistence operations, independent of HTTP request handling."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Task
from .schemas import Priority, Status, TaskCreate, TaskUpdate


class TaskNotFound(Exception):
    """The requested task does not exist."""


class TaskService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, task_id: int) -> Task:
        task = self.session.get(Task, task_id)
        if task is None:
            raise TaskNotFound
        return task

    def create(self, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        self.session.add(task)
        return self._save(task)

    def list(
        self,
        *,
        status: Status | None = None,
        priority: Priority | None = None,
        owner: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        filters = [
            column == value
            for column, value in (
                (Task.status, status),
                (Task.priority, priority),
                (Task.owner, owner),
            )
            if value is not None
        ]
        total = self.session.scalar(
            select(func.count()).select_from(Task).where(*filters)
        )
        query = (
            select(Task).where(*filters).order_by(Task.id).offset(offset).limit(limit)
        )
        return list(self.session.scalars(query)), total or 0

    def update(self, task_id: int, payload: TaskUpdate) -> Task:
        task = self.get(task_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        return self._save(task)

    def delete(self, task_id: int) -> None:
        self.session.delete(self.get(task_id))
        self.session.commit()

    def _save(self, task: Task) -> Task:
        self.session.commit()
        self.session.refresh(task)
        return task
