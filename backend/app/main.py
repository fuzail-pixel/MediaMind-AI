# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import engine, Base

import app.models.document
import app.models.chat
import app.models.user

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ {settings.APP_NAME} started successfully")
    yield
    await engine.dispose()
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION
    }


from app.api.routes import upload
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])


from app.api.routes import chat
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

from app.api.routes import auth
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])