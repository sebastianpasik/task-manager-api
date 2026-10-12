import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.security import create_access_token
from app.db.base import Base
from app.db.database import get_db
from app.db.models import User
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://task_manager:task_manager@localhost:5433/task_manager_test",
)


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool,
)


TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    with TestingSessionLocal() as db:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    tasks,
                    users
                RESTART IDENTITY
                CASCADE
                """
            )
        )
        db.commit()

    yield


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def create_user(db_session: Session):
    def factory(email: str) -> User:
        user = User(
            email=email.lower(),
            password_hash="test-only-placeholder",
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return factory


@pytest.fixture
def auth_headers():
    def factory(user_id: int) -> dict[str, str]:
        token = create_access_token(subject=str(user_id))

        return {"Authorization": f"Bearer {token}"}

    return factory
