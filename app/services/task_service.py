from app.db.models import Task
from app.domain.enums import TaskPriority, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate, TaskUpdate


class UserNotFoundError(Exception):
    pass


class TaskService:
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository: UserRepository,
    ) -> None:
        self.task_repository = task_repository
        self.user_repository = user_repository

    def create(
        self,
        data: TaskCreate,
    ) -> Task:
        user = self.user_repository.get_by_id(data.user_id)

        if user is None:
            raise UserNotFoundError(data.user_id)

        task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            user_id=data.user_id,
        )

        self.task_repository.add(task)
        self.task_repository.db.commit()
        self.task_repository.db.refresh(task)

        return task

    def get(
        self,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        return self.task_repository.get_by_id(
            task_id=task_id,
            user_id=user_id,
        )

    def list(
        self,
        user_id: int,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        return self.task_repository.list(
            user_id=user_id,
            status=status,
            priority=priority,
            skip=skip,
            limit=limit,
        )

    def update(
        self,
        task_id: int,
        user_id: int,
        data: TaskUpdate,
    ) -> Task | None:
        task = self.task_repository.get_by_id(
            task_id=task_id,
            user_id=user_id,
        )

        if task is None:
            return None

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(task, field, value)

        self.task_repository.db.commit()
        self.task_repository.db.refresh(task)

        return task

    def delete(
        self,
        task_id: int,
        user_id: int,
    ) -> bool:
        task = self.task_repository.get_by_id(
            task_id=task_id,
            user_id=user_id,
        )

        if task is None:
            return False

        self.task_repository.delete(task)
        self.task_repository.db.commit()

        return True