# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.core.redis import close_redis_pool, get_redis_client
from app.db.session import engine
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes and cleans up global connection pools (DB & Redis).
    """
    # Startup: Resources are lazily created on first request
    yield
    # Shutdown: Gracefully disconnect connection pools
    await close_redis_pool()
    await engine.dispose()


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS configuration for Angular frontend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", tags=["Monitoring"], status_code=status.HTTP_200_OK)
    async def health_check():
        """Comprehensive health check monitoring PostgreSQL and Redis connectivity."""
        health_status = {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "database": "unknown",
            "redis": "unknown",
        }

        # Check DB
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["database"] = "connected"
        except Exception as e:
            health_status["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Check Redis
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            health_status["redis"] = "connected"
            await redis_client.aclose()
        except Exception as e:
            health_status["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        return health_status

    application.include_router(api_router)
    return application


app = create_application()
