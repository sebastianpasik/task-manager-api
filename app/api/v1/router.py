from fastapi import APIRouter

from app.api.v1 import health, tasks

router = APIRouter()

router.include_router(health.router)
router.include_router(tasks.router)