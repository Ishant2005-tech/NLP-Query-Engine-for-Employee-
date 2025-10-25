from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .api.routes import database, documents, query
from .core.cache import cache
from .core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Starting NLP Query Engine...")
    await cache.connect()
    yield
    logger.info("Shutting down...")
    await cache.close()

# Create app
app = FastAPI(
    title="NLP Query Engine",
    description="Simple keyword-based query system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Include routers
app.include_router(database.router)
app.include_router(documents.router)
app.include_router(query.router)

@app.get("/")
async def root():
    return {
        "message": "NLP Query Engine API",
        "version": "1.0.0",
        "features": [
            "Dynamic schema discovery",
            "Keyword-based document search",
            "Redis/In-Memory caching with fallback",
            "No Docker required"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "_main_":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV == "development"
    )