"""Task CRUD with deterministic pagination and explicit error responses."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .database import get_session
from .models import Task
from .schemas import Priority, Status, TaskCreate, TaskPage, TaskRead, TaskUpdate
from .security import require_api_key

router = APIRouter(prefix='/tasks', tags=['Tasks'], dependencies=[Depends(require_api_key)],
                   responses={401: {'description': 'Missing or invalid bearer API key'}})
DB = Annotated[Session, Depends(get_session)]
TaskId = Annotated[int, Path(ge=1, description='Positive task ID')]


def find_task(task_id: int, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail='Task not found')
    return task


@router.post('', response_model=TaskRead, status_code=status.HTTP_201_CREATED,
             summary='Create a task')
def create_task(payload: TaskCreate, db: DB, response: Response):
    task = Task(**payload.model_dump(mode='python'))
    db.add(task)
    db.commit()
    db.refresh(task)
    response.headers['Location'] = f'/tasks/{task.id}'
    return task


@router.get('', response_model=TaskPage, summary='List and filter tasks')
def list_tasks(db: DB, status: Status | None = None, priority: Priority | None = None,
               owner: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
               limit: Annotated[int, Query(ge=1, le=100)] = 20,
               offset: Annotated[int, Query(ge=0)] = 0):
    filters = []
    for field, value in ((Task.status, status), (Task.priority, priority), (Task.owner, owner)):
        if value is not None:
            filters.append(field == value)
    total = db.scalar(select(func.count()).select_from(Task).where(*filters))
    items = db.scalars(select(Task).where(*filters).order_by(Task.id).offset(offset).limit(limit)).all()
    return {'items': items, 'total': total, 'limit': limit, 'offset': offset}


@router.get('/{task_id}', response_model=TaskRead, responses={404: {'description': 'Task not found'}}, summary='Get one task')
def get_task(task_id: TaskId, db: DB):
    return find_task(task_id, db)


@router.patch('/{task_id}', response_model=TaskRead, responses={404: {'description': 'Task not found'}}, summary='Update selected task fields')
def update_task(task_id: TaskId, payload: TaskUpdate, db: DB):
    task = find_task(task_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete('/{task_id}', status_code=status.HTTP_204_NO_CONTENT, responses={404: {'description': 'Task not found'}}, summary='Delete a task')
def delete_task(task_id: TaskId, db: DB):
    db.delete(find_task(task_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
