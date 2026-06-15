from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.v1.router import api_router
from app.infra.db.session import init_db
from app.infra.cache.redis import init_redis, close_redis


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    await init_redis()
    yield
    await close_redis()


app = FastAPI(
    title="World Cup Realtime Analytics",
    description="Real-time analysis platform for FIFA World Cup matches",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
