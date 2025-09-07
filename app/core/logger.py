import logging
import sys
from datetime import datetime
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/hrm.log", mode="a")
    ]
)

logger = logging.getLogger("hrm")

# Create logs directory if it doesn't exist
import os
os.makedirs("logs", exist_ok=True)