"""HTTP contracts for task operations; persistence lives in TaskService."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from .database import get_session
from .models import Task
from .schemas import Priority, Status, TaskCreate, TaskPage, TaskRead, TaskUpdate
from .security import require_api_key
from .task_service import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
    dependencies=[Depends(require_api_key)],
    responses={401: {"description": "Missing or invalid bearer API key"}},
)
NOT_FOUND = {404: {"description": "Task not found"}}
TaskId = Annotated[int, Path(ge=1, description="Positive task ID")]


def get_task_service(session: Annotated[Session, Depends(get_session)]) -> TaskService:
    return TaskService(session)


Service = Annotated[TaskService, Depends(get_task_service)]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(payload: TaskCreate, service: Service, response: Response) -> Task:
    task = service.create(payload)
    response.headers["Location"] = f"/tasks/{task.id}"
    return task


@router.get("", response_model=TaskPage, summary="List and filter tasks")
def list_tasks(
    service: Service,
    status: Status | None = None,
    priority: Priority | None = None,
    owner: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskPage:
    items, total = service.list(
        status=status, priority=priority, owner=owner, limit=limit, offset=offset
    )
    return TaskPage(
        items=[TaskRead.model_validate(task) for task in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{task_id}", response_model=TaskRead, responses=NOT_FOUND, summary="Get one task"
)
def get_task(task_id: TaskId, service: Service) -> Task:
    return service.get(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    responses=NOT_FOUND,
    summary="Update selected task fields",
)
def update_task(task_id: TaskId, payload: TaskUpdate, service: Service) -> Task:
    return service.update(task_id, payload)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
    summary="Delete a task",
)
def delete_task(task_id: TaskId, service: Service) -> Response:
    service.delete(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
