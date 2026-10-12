from fastapi import APIRouter

from app.core.dependencies import CurrentUser
from app.schemas.user import UserRead

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: CurrentUser) -> UserRead:
    return current_user
