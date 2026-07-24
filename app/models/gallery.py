"""
Gallery models — HR creates albums; employees can view & download images.
Images are stored as base64 data URIs or URLs (same pattern as avatar_url).
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class GalleryAlbum(Base):
    __tablename__ = "gallery_albums"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(Text, nullable=True)       # first image URL / base64
    is_published = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    images = relationship("GalleryImage", back_populates="album", cascade="all, delete-orphan")


class GalleryImage(Base):
    __tablename__ = "gallery_images"

    id = Column(Integer, primary_key=True, index=True)
    album_id = Column(Integer, ForeignKey("gallery_albums.id"), nullable=False)
    title = Column(String, nullable=True)
    file_name = Column(String, nullable=False)
    file_url = Column(Text, nullable=False)         # base64 data URI or relative path
    file_size = Column(Integer, nullable=True)      # bytes
    mime_type = Column(String, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    album = relationship("GalleryAlbum", back_populates="images")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class CelebrationBroadcast(Base):
    """
    HR posts a birthday wish or holiday announcement that broadcasts to everyone's dashboard.
    Also serves as the dashboard-visible celebration for award winners.
    """
    __tablename__ = "celebration_broadcasts"

    id = Column(Integer, primary_key=True, index=True)

    # birthday | holiday | award
    broadcast_type = Column(String, nullable=False)

    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)

    # For birthday/award: link to an employee; their photo will be shown with fireworks
    subject_employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)

    # For award broadcasts, link back to the Award record
    award_id = Column(Integer, ForeignKey("awards.id"), nullable=True)

    # Date this celebration is active/visible (birthday date, holiday date, award publish date)
    event_date = Column(DateTime(timezone=True), nullable=False)

    # Optional expiry — auto-hide after this date
    expires_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subject_employee = relationship("Employee", foreign_keys=[subject_employee_id])
    award = relationship("Award", foreign_keys=[award_id])
    creator = relationship("User", foreign_keys=[created_by])
