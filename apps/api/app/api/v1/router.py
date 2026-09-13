from fastapi import APIRouter

from . import endpoints

router = APIRouter()

# Mount endpoints router here to keep imports simple and explicit
router.include_router(endpoints.router)

from .quality_rules import router as quality_rules_router
router.include_router(quality_rules_router)
