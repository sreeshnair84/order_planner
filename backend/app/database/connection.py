from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.utils.config import settings
import logging

logger = logging.getLogger(__name__)

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,
    future=True
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()

async def check_database_exists():
    """Check if the database exists and create it if necessary"""
    try:
        # Try to connect to the database
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models.user import User
        from app.models.order import Order
        from app.models.sku_item import OrderSKUItem
        from app.models.tracking import OrderTracking, EmailCommunication
        from app.models.retailer import Retailer, Manufacturer, Route
        
        # Check if database exists first
        if not await check_database_exists():
            logger.error("Cannot connect to database. Please ensure the database exists.")
            raise Exception("Database connection failed")
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_engine():
    """Get the database engine for migrations"""
    return engine
