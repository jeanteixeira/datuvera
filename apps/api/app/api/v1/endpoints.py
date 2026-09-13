from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/info")
def info():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
    }
