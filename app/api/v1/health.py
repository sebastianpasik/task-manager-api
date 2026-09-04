from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.health import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("", response_model=HealthResponse)
async def health_check(
    db: Session = Depends(get_db),
) -> HealthResponse:
    db.execute(text("SELECT 1"))

    return HealthResponse(status="ok")