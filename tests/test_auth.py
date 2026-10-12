from sqlalchemy import select
from sqlalchemy.orm import Session

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
