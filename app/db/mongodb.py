from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logger import logger

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Connect to MongoDB."""
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
        mongodb.database = mongodb.client[settings.DATABASE_NAME]
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    """Create necessary indexes."""
    try:
        # Users collection indexes
        await mongodb.database.users.create_index("email", unique=True)
        await mongodb.database.users.create_index("created_at")
        
        # Documents collection indexes
        await mongodb.database.documents.create_index("user_id")
        await mongodb.database.documents.create_index("created_at")
        
        # Attendance collection indexes
        await mongodb.database.attendance.create_index("user_id")
        await mongodb.database.attendance.create_index([("user_id", 1), ("date", 1)])
        
        # Leave requests collection indexes
        await mongodb.database.leave_requests.create_index("user_id")
        await mongodb.database.leave_requests.create_index("status")
        
        logger.info("MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

def get_database():
    """Get MongoDB database instance."""
    if not mongodb.database:
        raise RuntimeError("MongoDB not connected")
    return mongodb.database