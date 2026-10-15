from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.db.models import User


def register_payload(
    email: str = "alice@example.com",
    password: str = "StrongPassword123!",
) -> dict[str, str]:
    return {
        "email": email,
        "password": password,
    }


def test_register_user(client, db_session: Session) -> None:
    password = "StrongPassword123!"

    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(password=password),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "alice@example.com"
    assert "password_hash" not in data
    assert "password" not in data

    user = db_session.scalar(select(User).where(User.email == "alice@example.com"))

    assert user is not None
    assert user.password_hash != password
    assert verify_password(password, user.password_hash)


def test_duplicate_email_returns_409(client) -> None:
    payload = register_payload()

    first_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_register_rejects_short_password(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json=register_payload(password="short"),
    )

    assert response.status_code == 422


def test_login_returns_access_token(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(),
    )

    response = client.post(
        "/api/v1/auth/login",
        json=register_payload(),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data["token_type"] == "bearer"


def test_invalid_password_returns_401(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(),
    )

    response = client.post(
        "/api/v1/auth/login",
        json=register_payload(password="WrongPassword123!"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_current_user_requires_valid_token(client) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_current_user_returns_profile(client) -> None:
    client.post(
        "/api/v1/auth/register",
        json=register_payload(),
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json=register_payload(),
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
    assert "password_hash" not in response.json()


def test_invalid_token_returns_401(client) -> None:
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_expired_token_returns_401(client) -> None:
    now = datetime.now(UTC)

    expired_token = jwt.encode(
        {
            "sub": "1",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


def test_token_for_deleted_or_unknown_user_returns_401(
    client,
    auth_headers,
) -> None:
    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers(999999),
    )

    assert response.status_code == 401


def test_inactive_user_cannot_access_profile(
    client,
    create_user,
    auth_headers,
    db_session,
) -> None:
    user = create_user("inactive@example.com")
    user_id = user.id

    user.is_active = False
    db_session.commit()

    response = client.get(
        "/api/v1/users/me",
        headers=auth_headers(user_id),
    )

    assert response.status_code == 403


def test_task_title_cannot_be_blank(
    client,
    create_user,
    auth_headers,
) -> None:
    user = create_user("blank-title@example.com")

    response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(user.id),
        json={"title": "   "},
    )

    assert response.status_code == 422


def test_invalid_task_status_is_rejected(
    client,
    create_user,
    auth_headers,
) -> None:
    user = create_user("invalid-status@example.com")

    response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(user.id),
        json={
            "title": "Valid title",
            "status": "unknown",
        },
    )

    assert response.status_code == 422


def test_patch_rejects_null_title(
    client,
    create_user,
    auth_headers,
) -> None:
    user = create_user("patch-title@example.com")
    headers = auth_headers(user.id)

    create_response = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "Original title"},
    )
    task_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=headers,
        json={"title": None},
    )

    assert response.status_code == 422


def test_user_cannot_update_or_delete_another_users_task(
    client,
    create_user,
    auth_headers,
) -> None:
    owner = create_user("owner-update@example.com")
    other_user = create_user("other-update@example.com")

    create_response = client.post(
        "/api/v1/tasks",
        headers=auth_headers(owner.id),
        json={"title": "Private task"},
    )
    task_id = create_response.json()["id"]

    other_headers = auth_headers(other_user.id)

    update_response = client.patch(
        f"/api/v1/tasks/{task_id}",
        headers=other_headers,
        json={"title": "Stolen task"},
    )

    delete_response = client.delete(
        f"/api/v1/tasks/{task_id}",
        headers=other_headers,
    )

    assert update_response.status_code == 404
    assert delete_response.status_code == 404
