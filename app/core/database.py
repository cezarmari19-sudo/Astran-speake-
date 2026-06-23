from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

# Convertim URL pentru asyncpg (PostgreSQL async driver)
_db_url = settings.database_url
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    _db_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,      # Verifică conexiunea înainte de fiecare query
    pool_recycle=3600,       # Reciclează conexiunile la fiecare oră
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Evită lazy loading după commit
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency injection pentru FastAPI — garantează închiderea sesiunii."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Creează tabelele la pornirea serverului."""
    async with engine.begin() as conn:
        from ..models import user, message, group  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
