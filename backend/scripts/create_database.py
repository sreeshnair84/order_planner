#!/usr/bin/env python3
"""
Script to create the order_management database on Azure PostgreSQL
"""
import asyncio
import asyncpg
from app.utils.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_database():
    """Create the order_management database if it doesn't exist"""
    
    # Parse the database URL
    db_url = settings.DATABASE_URL
    
    # Extract connection parameters
    # Format: postgresql://user:password@host:port/database
    parts = db_url.replace('postgresql://', '').split('/')
    connection_part = parts[0]
    target_database = parts[1] if len(parts) > 1 else 'order_management'
    
    # Split connection part
    auth_host = connection_part.split('@')
    auth_part = auth_host[0]
    host_port = auth_host[1]
    
    # Extract credentials
    username, password = auth_part.split(':')
    host, port = host_port.split(':')
    
    # Connect to the default postgres database first
    try:
        logger.info(f"Connecting to PostgreSQL server at {host}:{port}")
        conn = await asyncpg.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database='postgres'  # Connect to default database
        )
        
        # Check if database exists
        existing_db = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", 
            target_database
        )
        
        if existing_db:
            logger.info(f"Database '{target_database}' already exists")
        else:
            # Create the database
            logger.info(f"Creating database '{target_database}'")
            await conn.execute(f'CREATE DATABASE "{target_database}"')
            logger.info(f"Database '{target_database}' created successfully")
        
        await conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_database())
