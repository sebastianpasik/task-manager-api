from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.task_service import TaskService


def get_task_service(
    db: Annotated[Session, Depends(get_db)],
) -> TaskService:
    return TaskService(
        task_repository=TaskRepository(db),
        user_repository=UserRepository(db),
    )


TaskServiceDependency = Annotated[
    TaskService,
    Depends(get_task_service),
]