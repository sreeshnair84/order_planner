#!/usr/bin/env python3
"""
Test database connection and list available databases
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.utils.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection():
    """Test database connection and list available databases"""
    try:
        # Try to import asyncpg
        import asyncpg
        
        # Parse the database URL
        db_url = settings.DATABASE_URL
        logger.info(f"Testing connection to: {db_url}")
        
        # Extract connection parameters
        parts = db_url.replace('postgresql://', '').split('/')
        connection_part = parts[0]
        
        # Split connection part
        auth_host = connection_part.split('@')
        auth_part = auth_host[0]
        host_port = auth_host[1]
        
        # Extract credentials
        username, password = auth_part.split(':')
        host, port = host_port.split(':')
        
        logger.info(f"Connecting to {host}:{port} as {username}")
        
        # Try connecting to postgres database first
        try:
            conn = await asyncpg.connect(
                host=host,
                port=int(port),
                user=username,
                password=password,
                database='postgres'
            )
            
            logger.info("Connected successfully to 'postgres' database")
            
            # List available databases
            databases = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false")
            logger.info("Available databases:")
            for db in databases:
                logger.info(f"  - {db['datname']}")
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Failed to connect to 'postgres' database: {e}")
            
            # Try connecting to the target database directly
            try:
                target_db = parts[1] if len(parts) > 1 else 'order_management'
                conn = await asyncpg.connect(
                    host=host,
                    port=int(port),
                    user=username,
                    password=password,
                    database=target_db
                )
                logger.info(f"Connected successfully to '{target_db}' database")
                await conn.close()
            except Exception as e2:
                logger.error(f"Failed to connect to '{target_db}' database: {e2}")
                raise
        
    except ImportError:
        logger.error("asyncpg not found. Install it with: pip install asyncpg")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_connection())
