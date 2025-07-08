"""
Database session management for the order processing system.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

async def get_async_session() -> AsyncSession:
    """Get an async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

class DatabaseSession:
    """Database session context manager"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        await self.session.close()
