from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger
from app.core.config import settings


class Base(DeclarativeBase):
    pass


# ─── Lazy engine creation ─────────────────────────────────

_engine = None
_AsyncSessionLocal = None

def get_engine():
    global _engine, _AsyncSessionLocal
    if _engine is None and settings.DATABASE_URL:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        _AsyncSessionLocal = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _engine, _AsyncSessionLocal


async def get_db() -> AsyncSession:
    _, session_factory = get_engine()
    if session_factory is None:
        yield None
        return
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise


async def init_db():
    engine, _ = get_engine()
    if engine is None:
        logger.warning("No DATABASE_URL — skipping DB init")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized")