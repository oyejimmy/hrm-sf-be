"""
Award models — HR Quarterly Awards workflow.
Supports multi-project separation (smart_forum, medlez, phone_world).
Award types: bravo | star_performer
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class ProjectEnum(str, enum.Enum):
    smart_forum = "smart_forum"
    medlez = "medlez"
    phone_world = "phone_world"


class AwardTypeEnum(str, enum.Enum):
    bravo = "bravo"
    star_performer = "star_performer"


class NominationStatusEnum(str, enum.Enum):
    pending = "pending"       # submitted by team lead, awaiting HR review
    evaluated = "evaluated"   # HR is evaluating
    approved = "approved"     # HR selected as winner
    rejected = "rejected"     # not selected this quarter


class AwardNomination(Base):
    """Team leads submit nominees for quarterly evaluation."""
    __tablename__ = "award_nominations"

    id = Column(Integer, primary_key=True, index=True)

    # Who was nominated
    nominee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Who nominated them
    nominated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Which project this belongs to — data stays siloed
    project = Column(String, nullable=False)   # smart_forum | medlez | phone_world

    # Reason submitted by team lead
    reason = Column(Text, nullable=True)

    # Quarter e.g. "2026-Q3"
    quarter = Column(String, nullable=False)

    status = Column(String, default="pending")  # pending | evaluated | approved | rejected

    # HR evaluation fields
    hr_notes = Column(Text, nullable=True)
    evaluated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    nominee = relationship("Employee", foreign_keys=[nominee_id])
    nominated_by = relationship("User", foreign_keys=[nominated_by_id])
    evaluated_by = relationship("User", foreign_keys=[evaluated_by_id])


class Award(Base):
    """Final quarterly award granted by HR to exactly one employee per type per quarter per project."""
    __tablename__ = "awards"

    id = Column(Integer, primary_key=True, index=True)

    # Recipient
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Award classification
    award_type = Column(String, nullable=False)   # bravo | star_performer
    project = Column(String, nullable=False)       # smart_forum | medlez | phone_world
    quarter = Column(String, nullable=False)       # e.g. "2026-Q3"

    # HR commentary shown on dashboard card
    citation = Column(Text, nullable=True)

    # Controls whether this shows on everyone's dashboard
    is_published = Column(Boolean, default=True)

    # HR granting this award
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Back-link to the nomination that triggered this (optional)
    nomination_id = Column(Integer, ForeignKey("award_nominations.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    nomination = relationship("AwardNomination", foreign_keys=[nomination_id])
