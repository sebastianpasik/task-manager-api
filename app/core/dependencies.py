from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.task_service import TaskService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(
    db: Annotated[Session, Depends(get_db)],
) -> AuthService:
    return AuthService(db)


def get_task_service(
    db: Annotated[Session, Depends(get_db)],
) -> TaskService:
    return TaskService(db)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError:
        raise credentials_exception from None

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject.isdecimal():
        raise credentials_exception

    user = UserRepository(db).get_by_id(int(subject))

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]

TaskServiceDependency = Annotated[
    TaskService,
    Depends(get_task_service),
]

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
