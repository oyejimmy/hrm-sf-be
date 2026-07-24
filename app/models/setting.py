from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base


class SystemSetting(Base):
    """Key/value store for system settings, one row per section
    (general, attendance, notifications, security)."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
