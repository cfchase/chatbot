from fastapi import APIRouter
from .utils.router import router as utils_router
from .chat.router import router as chat_router
from .mcp.router import router as mcp_router

router = APIRouter()
router.include_router(utils_router, prefix="/utils")
router.include_router(chat_router, prefix="/chat")
router.include_router(mcp_router, prefix="/mcp")