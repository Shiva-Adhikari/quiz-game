# Local imports
from src.core.database import AsyncSessionLocal


# Dependency to get database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
