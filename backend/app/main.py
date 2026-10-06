"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.database.base import init_db, close_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting Adaptive Exam Prep Agent...")
    logger.info(f"Demo mode: {settings.is_demo_mode}")
    logger.info(f"Database: {settings.DATABASE_URL}")
    await init_db()
    logger.info("Database initialized.")
    yield
    await close_db()
    logger.info("Application shutdown.")


app = FastAPI(
    title="Adaptive Exam Prep Agent",
    description="AI-powered adaptive exam preparation platform with 10 coordinated agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.api.auth import router as auth_router
from app.api.profiles import router as profiles_router
from app.api.syllabus import router as syllabus_router
from app.api.study_plans import router as study_router
from app.api.assessments import router as assessments_router
from app.api.tutor import router as tutor_router
from app.api.analytics import router as analytics_router

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(syllabus_router)
app.include_router(study_router)
app.include_router(assessments_router)
app.include_router(tutor_router)
app.include_router(analytics_router)

# Serve uploaded files
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)


@app.get("/")
async def root():
    return {
        "name": "Adaptive Exam Prep Agent",
        "version": "1.0.0",
        "demo_mode": settings.is_demo_mode,
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "demo_mode": settings.is_demo_mode}
