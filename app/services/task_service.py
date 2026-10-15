from sqlalchemy.orm import Session

from app.db.models import Task
from app.domain.enums import TaskPriority, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.task_repository = TaskRepository(db)

    def create(self, data: TaskCreate, *, user_id: int) -> Task:
        task = Task(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            user_id=user_id,
        )

        try:
            self.task_repository.add(task)
            self.db.commit()
            self.db.refresh(task)
        except Exception:
            self.db.rollback()
            raise

        return task

    def get(self, task_id: int, user_id: int) -> Task | None:
        return self.task_repository.get_by_id(task_id, user_id)

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
        task = self.task_repository.get_by_id(task_id, user_id)

        if task is None:
            return None

        try:
            update_data = data.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(task, field, value)

            self.db.commit()
            self.db.refresh(task)
        except Exception:
            self.db.rollback()
            raise

        return task

    def delete(self, task_id: int, user_id: int) -> bool:
        task = self.task_repository.get_by_id(task_id, user_id)

        if task is None:
            return False
        
        try:
            self.task_repository.delete(task)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return True
