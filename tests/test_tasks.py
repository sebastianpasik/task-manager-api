from app.db.models import User


def create_user(db_session, email: str = "test@example.com") -> User:
    user = User(
        email=email,
        password_hash="temporary-hash",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


def test_create_task(client, db_session):
    user = create_user(db_session)

    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Learn FastAPI",
            "description": "Build a REST API",
            "status": "todo",
            "priority": "high",
            "user_id": user.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Learn FastAPI"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["user_id"] == user.id


def test_get_task(client, db_session):
    user = create_user(db_session)

    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Test GET",
            "user_id": user.id,
        },
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/tasks/{task_id}",
        params={"user_id": user.id},
    )

    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_from_another_user_returns_404(
    client,
    db_session,
):
    owner = create_user(
        db_session,
        email="owner@example.com",
    )

    another_user = create_user(
        db_session,
        email="another@example.com",
    )

    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Private task",
            "user_id": owner.id,
        },
    )

    task_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/tasks/{task_id}",
        params={"user_id": another_user.id},
    )

    assert response.status_code == 404


def test_list_tasks(client, db_session):
    user = create_user(db_session)

    client.post(
        "/api/v1/tasks",
        json={
            "title": "Task 1",
            "priority": "high",
            "user_id": user.id,
        },
    )

    client.post(
        "/api/v1/tasks",
        json={
            "title": "Task 2",
            "priority": "low",
            "user_id": user.id,
        },
    )

    response = client.get(
        "/api/v1/tasks",
        params={"user_id": user.id},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_filter_tasks_by_priority(client, db_session):
    user = create_user(db_session)

    client.post(
        "/api/v1/tasks",
        json={
            "title": "High priority",
            "priority": "high",
            "user_id": user.id,
        },
    )

    client.post(
        "/api/v1/tasks",
        json={
            "title": "Low priority",
            "priority": "low",
            "user_id": user.id,
        },
    )

    response = client.get(
        "/api/v1/tasks",
        params={
            "user_id": user.id,
            "priority": "high",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["title"] == "High priority"


def test_update_task(client, db_session):
    user = create_user(db_session)

    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Original title",
            "user_id": user.id,
        },
    )

    task_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        params={"user_id": user.id},
        json={
            "title": "Updated title",
            "status": "done",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Updated title"
    assert data["status"] == "done"


def test_delete_task(client, db_session):
    user = create_user(db_session)

    create_response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Task to delete",
            "user_id": user.id,
        },
    )

    task_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        params={"user_id": user.id},
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/api/v1/tasks/{task_id}",
        params={"user_id": user.id},
    )

    assert get_response.status_code == 404


def test_create_task_for_nonexistent_user(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Orphan task",
            "user_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User 999999 not found"


def test_create_task_with_blank_title(client, db_session):
    user = create_user(db_session)

    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "   ",
            "user_id": user.id,
        },
    )

    assert response.status_code == 422
