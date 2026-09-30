import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Task, User
from app.domain.enums import TaskPriority, TaskStatus


def test_user_can_have_tasks(db_session):
    user = User(
        email="john@example.com",
        password_hash="hashed-password",
    )

    task = Task(
        title="Learn FastAPI",
        status=TaskStatus.TODO,
        priority=TaskPriority.HIGH,
        user=user,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert len(user.tasks) == 1
    assert user.tasks[0].title == "Learn FastAPI"
    assert user.tasks[0].user_id == user.id


def test_task_uses_enum_values(db_session):
    user = User(
        email="enum@example.com",
        password_hash="hashed-password",
    )

    task = Task(
        title="Test enum",
        user=user,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.MEDIUM,
    )

    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.status is TaskStatus.IN_PROGRESS
    assert task.priority is TaskPriority.MEDIUM


def test_user_email_must_be_unique(db_session):
    first_user = User(
        email="duplicate@example.com",
        password_hash="hash-1",
    )

    second_user = User(
        email="duplicate@example.com",
        password_hash="hash-2",
    )

    db_session.add(first_user)
    db_session.commit()

    db_session.add(second_user)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_task_title_cannot_be_blank(db_session):
    user = User(
        email="blank@example.com",
        password_hash="hash",
    )

    task = Task(
        title="   ",
        user=user,
    )

    db_session.add(task)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_deleting_user_deletes_tasks(db_session):
    user = User(
        email="delete@example.com",
        password_hash="hash",
    )

    task = Task(
        title="Task to delete",
        user=user,
    )

    db_session.add(user)
    db_session.commit()

    task_id = task.id
    user_id = user.id

    db_session.delete(user)
    db_session.commit()

    assert db_session.get(User, user_id) is None
    assert db_session.get(Task, task_id) is None
