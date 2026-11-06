from fastapi import FastAPI
from app.routes import api_router

def create_application() -> FastAPI:
    application = FastAPI(
        title="Modular FastAPI Web API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    application.include_router(api_router)
    return application

app = create_application()