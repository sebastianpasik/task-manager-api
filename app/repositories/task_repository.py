from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Task
from app.domain.enums import TaskPriority, TaskStatus


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(
        self,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        statement = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )

        return self.db.scalar(statement)

    def list(
        self,
        user_id: int,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        filters = [Task.user_id == user_id]

        if status is not None:
            filters.append(Task.status == status)

        if priority is not None:
            filters.append(Task.priority == priority)

        items_statement = (
            select(Task)
            .where(*filters)
            .order_by(Task.created_at.desc(), Task.id.desc())
            .offset(skip)
            .limit(limit)
        )

        count_statement = select(func.count(Task.id)).where(*filters)

        items = list(self.db.scalars(items_statement).all())
        total = self.db.scalar(count_statement) or 0

        return items, total

    def add(self, task: Task) -> Task:
        self.db.add(task)
        self.db.flush()

        return task

    def delete(self, task: Task) -> None:
        self.db.delete(task)