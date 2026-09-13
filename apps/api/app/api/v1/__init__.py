from fastapi import APIRouter
router = APIRouter()
from . import endpoints  # noqa: E402,F401
# include the endpoints' router so routes are registered under this prefix
router.include_router(endpoints.router)
# Package initializer for api.v1
# Route registration is handled explicitly in app.api.v1.router
