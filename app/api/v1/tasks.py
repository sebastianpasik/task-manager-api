from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.dependencies import CurrentUser, TaskServiceDependency
from app.domain.enums import TaskPriority, TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
)

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    data: TaskCreate,
    current_user: CurrentUser,
    service: TaskServiceDependency,
) -> TaskRead:
    return service.create(data, user_id=current_user.id)


@router.get("", response_model=TaskListResponse)
def list_tasks(
    current_user: CurrentUser,
    service: TaskServiceDependency,
    status_filter: Annotated[
        TaskStatus | None,
        Query(alias="status"),
    ] = None,
    priority: TaskPriority | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TaskListResponse:
    items, total = service.list(
        user_id=current_user.id,
        status=status_filter,
        priority=priority,
        skip=skip,
        limit=limit,
    )

    return TaskListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    task_id: int,
    current_user: CurrentUser,
    service: TaskServiceDependency,
) -> TaskRead:
    task = service.get(task_id, current_user.id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: CurrentUser,
    service: TaskServiceDependency,
) -> TaskRead:
    task = service.update(task_id, current_user.id, data)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_task(
    task_id: int,
    current_user: CurrentUser,
    service: TaskServiceDependency,
) -> None:
    deleted = service.delete(task_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
