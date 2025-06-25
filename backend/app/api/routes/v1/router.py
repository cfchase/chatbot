from fastapi import APIRouter
from .utils.router import router as utils_router

router = APIRouter()
router.include_router(utils_router, prefix="/utils")