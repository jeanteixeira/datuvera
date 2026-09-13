from fastapi import APIRouter

router = APIRouter()

from . import endpoints  # noqa: E402,F401
