from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from app.api.router import router as api_router
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="React FastAPI Template API",
    description="A template API built with FastAPI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "React FastAPI Template API"}

@app.on_event("startup")
async def startup_event():
    """Log configuration status on startup"""
    from app.services.claude import claude_service
    
    logger.info(f"Starting application in {settings.environment} mode")
    logger.info(f"Claude integration: {'Enabled' if settings.anthropic_api_key else 'Disabled'}")
    
    # Model selection happens on first use, so we just log that it's enabled
    if settings.anthropic_api_key:
        if settings.claude_model:
            logger.info(f"Claude model configured: {settings.claude_model}")
        else:
            logger.info("Claude model will be auto-selected on first use")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)