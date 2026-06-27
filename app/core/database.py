from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings
from typing import AsyncGenerator

settings = get_settings()

_db_url = settings.database_url
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    _db_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
    # ← ADAUGĂ ASTA pentru PostgreSQL pe Render
    pool_size=5,
    max_overflow=10,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection corectă pentru FastAPI async."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()  # ← ADAUGĂ close() explicit


async def init_db() -> None:
    async with engine.begin() as conn:
        from ..models.user import User  # noqa: F401
        from ..models.message import OfflineMessage  # noqa: F401
        from ..models.group import Group  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)