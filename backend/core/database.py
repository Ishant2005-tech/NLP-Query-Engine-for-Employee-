from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Create engine arguments
engine_args = {
    "echo": settings.APP_ENV == "development"
}

# SQLite (aiosqlite) does not support connection pooling arguments
# like 'pool_size' or 'pool_pre_ping' as it uses a NullPool.
# We only add them if we are NOT using SQLite.
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_args["pool_size"] = settings.DB_POOL_SIZE
    engine_args["pool_pre_ping"] = True

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_args
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()