from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.core.logger import logger

async def init_db():
    """Initialize MongoDB connection."""
    try:
        await connect_to_mongo()
        logger.info("MongoDB initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection."""
    await close_mongo_connection()
    logger.info("MongoDB connection closed")

# Export get_database function
__all__ = ['init_db', 'close_db', 'get_database']