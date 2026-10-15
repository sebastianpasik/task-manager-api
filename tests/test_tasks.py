import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.models import Task
from app.schemas.task import TaskCreate
from app.services.task_service import TaskService


def test_create_task(client, create_user, auth_headers) -> None:
    user = create_user("owner@example.com")
    headers = auth_headers(user.id)

    response = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Learn FastAPI",
            "description": "Build a REST API",
            "priority": "high",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Learn FastAPI"
    assert data["priority"] == "high"
    assert data["user_id"] == user.id


def test_client_cannot_set_task_owner(
    client,
    create_user,
    auth_headers,
) -> None:
    owner = create_user("owner@example.com")
    another_user = create_user("another@example.com")

    response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        json={
            "title": "My task",
            "user_id": another_user.id,
        },
    )

    assert response.status_code == 422


def test_list_tasks_only_returns_current_users_tasks(
    client,
    create_user,
    auth_headers,
) -> None:
    owner = create_user("owner@example.com")
    another_user = create_user("another@example.com")

    client.post(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        json={"title": "High priority", "priority": "high"},
    )

    client.post(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        json={"title": "Low priority", "priority": "low"},
    )

    client.post(
        "/api/v1/tasks",
        headers=auth_headers(another_user.id),
        json={"title": "Another user's task"},
    )

    response = client.get(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        params={"priority": "high"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "High priority"


def test_user_cannot_read_another_users_task(
    client,
    create_user,
    auth_headers,
) -> None:
    owner = create_user("owner@example.com")
    another_user = create_user("another@example.com")

    create_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        json={"title": "Private task"},
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=auth_headers(another_user.id),
    )

    assert response.status_code == 404


def test_update_and_delete_task(
    client,
    create_user,
    auth_headers,
) -> None:
    user = create_user("owner@example.com")
    headers = auth_headers(user.id)

    create_response = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Original title"},
    )

    task_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={
            "title": "Updated title",
            "status": "done",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated title"
    assert update_response.json()["status"] == "done"

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_tasks_require_authentication(client) -> None:
    response = client.get("/api/v1/tasks")

    assert response.status_code == 401


def test_task_creation_rolls_back_after_database_error(
    db_session,
    create_user,
    monkeypatch,
) -> None:
    user = create_user("rollback@example.com")
    user_id = user.id

    db_session.rollback()
    service = TaskService(db_session)

    def fail_add(task: Task) -> None:
        # Wymuszamy naruszenie CHECK constraint w PostgreSQL.
        db_session.add(Task(title="   ", user_id=user_id))
        db_session.flush()

    monkeypatch.setattr(service.task_repository, "add", fail_add)

    with pytest.raises(IntegrityError):
        service.create(
            TaskCreate(title="A valid task"),
            user_id=user_id,
        )

    # Po błędzie sesja powinna znów nadawać się do użytku.
    count = db_session.scalar(select(func.count()).select_from(Task))

    assert count == 0
