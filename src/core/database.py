# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# Local imports
from src.core.config import settings


DATABASE_URL = settings.DATABASE_URL.get_secret_value()
engine = create_async_engine(DATABASE_URL, echo=settings.DEBUG)

# pool_pre_ping=True helps in maintaining connections for long-running applications
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False)


class Base(DeclarativeBase):
    pass
