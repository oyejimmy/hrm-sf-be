from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, Date, Time, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
from datetime import datetime, date, time

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    TEAM_LEAD = "team_lead"
    EMPLOYEE = "employee"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class EmploymentStatus(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"

class LeaveType(str, enum.Enum):
    SICK_LEAVE = "sick_leave"
    ANNUAL_LEAVE = "annual_leave"
    PERSONAL_LEAVE = "personal_leave"
    MATERNITY_LEAVE = "maternity_leave"
    PATERNITY_LEAVE = "paternity_leave"
    EMERGENCY_LEAVE = "emergency_leave"
    UNPAID_LEAVE = "unpaid_leave"

class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class MaritalStatus(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"

class Department(str, enum.Enum):
    HUMAN_RESOURCES = "human_resources"
    INFORMATION_TECHNOLOGY = "information_technology"
    FINANCE = "finance"
    MARKETING = "marketing"
    SALES = "sales"
    OPERATIONS = "operations"
    CUSTOMER_SERVICE = "customer_service"
    RESEARCH_DEVELOPMENT = "research_development"
    LEGAL = "legal"
    ADMINISTRATION = "administration"

class PositionLevel(str, enum.Enum):
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"

class WorkLocation(str, enum.Enum):
    OFFICE = "office"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FIELD = "field"

class DocumentType(str, enum.Enum):
    CONTRACT = "contract"
    ID_PROOF = "id_proof"
    ADDRESS_PROOF = "address_proof"
    EDUCATIONAL_CERTIFICATE = "educational_certificate"
    EXPERIENCE_CERTIFICATE = "experience_certificate"
    MEDICAL_CERTIFICATE = "medical_certificate"
    LEAVE_DOCUMENT = "leave_document"
    PERFORMANCE_REVIEW = "performance_review"
    TRAINING_CERTIFICATE = "training_certificate"
    OTHER = "other"

class NotificationType(str, enum.Enum):
    LEAVE_REQUEST = "leave_request"
    LEAVE_APPROVAL = "leave_approval"
    ATTENDANCE_REMINDER = "attendance_reminder"
    TRAINING_ASSIGNMENT = "training_assignment"
    PERFORMANCE_REVIEW = "performance_review"
    ANNOUNCEMENT = "announcement"
    SYSTEM_ALERT = "system_alert"

class NotificationStatus(str, enum.Enum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    phone = Column(String(20), nullable=True)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="user", uselist=False)
    attendance_records = relationship("Attendance", back_populates="user")
    leave_requests = relationship(
        "LeaveRequest",
        back_populates="user",
        foreign_keys="LeaveRequest.user_id",
    )
    documents = relationship("Document", back_populates="user")
    notifications_sent = relationship("Notification", foreign_keys="Notification.sender_id", back_populates="sender")
    notifications_received = relationship("Notification", foreign_keys="Notification.recipient_id", back_populates="recipient")
    team = relationship(
        "Team",
        back_populates="members",
        foreign_keys=[team_id],
    )

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department = Column(SQLEnum(Department), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship(
        "User",
        back_populates="team",
        foreign_keys="User.team_id",
    )
    manager = relationship("User", foreign_keys=[manager_id])

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id = Column(String(20), unique=True, index=True, nullable=False)
    department = Column(SQLEnum(Department), nullable=False)
    position = Column(String(100), nullable=False)
    position_level = Column(SQLEnum(PositionLevel), nullable=False)
    employment_status = Column(SQLEnum(EmploymentStatus), nullable=False)
    hire_date = Column(Date, nullable=False)
    salary = Column(Float, nullable=True)
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    work_location = Column(SQLEnum(WorkLocation), nullable=True)
    work_schedule = Column(String(50), nullable=True)
    
    # Personal Details
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    marital_status = Column(SQLEnum(MaritalStatus), nullable=True)
    nationality = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    
    # Additional Information
    skills = Column(Text, nullable=True)  # JSON string
    certifications = Column(Text, nullable=True)  # JSON string
    education = Column(Text, nullable=True)  # JSON string
    work_experience = Column(Text, nullable=True)  # JSON string
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employee")
    manager = relationship("Employee", remote_side=[id])
    subordinates = relationship("Employee", back_populates="manager")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    status = Column(SQLEnum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    work_hours = Column(Float, nullable=True)
    overtime_hours = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="attendance_records")

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(SQLEnum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(SQLEnum(LeaveStatus), default=LeaveStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    documents = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship(
        "User",
        back_populates="leave_requests",
        foreign_keys=[user_id],
    )
    approver = relationship("User", foreign_keys=[approved_by])

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.UNREAD)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="notifications_received")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="notifications_sent")

class Announcement(Base):
    __tablename__ = "announcements"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="active")
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    target_audience = Column(String(50), nullable=True)  # all, department, team, individual
    target_id = Column(Integer, nullable=True)  # department_id, team_id, or user_id
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User")

class PerformanceReview(Base):
    __tablename__ = "performance_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    overall_rating = Column(Float, nullable=False)
    goals_achieved = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    status = Column(String(20), default="draft")  # draft, submitted, approved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee")
    reviewer = relationship("User")

class TrainingProgram(Base):
    __tablename__ = "training_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    status = Column(String(20), default="active")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User")

class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    training_program_id = Column(Integer, ForeignKey("training_programs.id"), nullable=False)
    status = Column(String(20), default="enrolled")  # enrolled, in_progress, completed, cancelled
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    
    # Relationships
    employee = relationship("Employee")
    training_program = relationship("TrainingProgram")

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    assigned_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    status = Column(String(20), default="available")  # available, assigned, maintenance, retired
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Float, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee")

class Payslip(Base):
    __tablename__ = "payslips"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    basic_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0)
    deductions = Column(Float, default=0)
    overtime_pay = Column(Float, default=0)
    bonus = Column(Float, default=0)
    net_salary = Column(Float, nullable=False)
    status = Column(String(20), default="generated")  # generated, approved, paid
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    employee = relationship("Employee")
    generator = relationship("User")
