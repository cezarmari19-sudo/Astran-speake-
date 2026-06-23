from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import init_db
from app.core.config import get_settings
from app.api import users, messages, websocket, groups
from app.services.expiry import cleanup_expired_messages
from app.middleware.rate_limiter import rate_limiter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management:
    - La pornire: inițializează DB și pornește scheduler-ul de cleanup
    - La oprire: oprește scheduler-ul curat
    """
    logger.info("🚀 Astran Server pornit")
    await init_db()

    # Cleanup mesaje expirate — rulează la fiecare 6 ore
    scheduler.add_job(cleanup_expired_messages, "interval", hours=6)
    scheduler.start()

    yield

    scheduler.shutdown()
    logger.info("🛑 Astran Server oprit")


app = FastAPI(
    title="Astran Chat Server",
    description="Zero-Knowledge Secure Messaging Server",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

# CORS — permite conexiuni din app Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    await rate_limiter.check(request)
    return await call_next(request)


# Routere
app.include_router(users.router)
app.include_router(messages.router)
app.include_router(groups.router)
app.include_router(websocket.router)


@app.get("/health")
async def health():
    """Endpoint pentru Render health check."""
    return {"status": "ok", "service": "astran-chat"}
