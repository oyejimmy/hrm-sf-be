from app.database import create_tables, get_db as get_database
from app.core.logger import logger

async def init_db():
    """Initialize database connection and create tables."""
    try:
        await create_tables()
        logger.info("SQLite database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def close_db():
    """Close database connection."""
    logger.info("Database connection closed")

# Export get_database function
__all__ = ['init_db', 'close_db', 'get_database']