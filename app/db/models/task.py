from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import TaskPriority, TaskStatus

if TYPE_CHECKING:
    from app.db.models.user import User

task_status_enum = PgEnum(
    TaskStatus,
    name="task_status",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)

task_priority_enum = PgEnum(
    TaskPriority,
    name="task_priority",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(title)) > 0",
            name="title_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[TaskStatus] = mapped_column(
        task_status_enum,
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        task_priority_enum,
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        back_populates="tasks",
    )
