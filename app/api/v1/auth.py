from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import AuthServiceDependency
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserCreate,
    service: AuthServiceDependency,
) -> UserRead:
    try:
        user = service.register(data)
        return UserRead.model_validate(user)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None


@router.post(
    "/login",
    response_model=Token,
)
def login(
    data: LoginRequest,
    service: AuthServiceDependency,
) -> Token:
    try:
        user = service.authenticate(
            email=str(data.email),
            password=data.password.get_secret_value(),
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    access_token = create_access_token(subject=str(user.id))

    return Token(access_token=access_token)
