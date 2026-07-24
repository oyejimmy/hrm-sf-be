from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class Asset(Base):
    """A line in the IT inventory.

    Two shapes share this table, distinguished by `tracking_mode`:

    - `serialized`  — one row per physical unit (laptop, monitor). `serial_number`
      is the real manufacturer serial and `assigned_to` names its single holder.
    - `consumable`  — one row per stock line (mouse batteries, HDMI cables).
      `quantity_total`/`quantity_available` carry the counts and `assigned_to`
      stays NULL; who holds what lives in AssetAssignmentLog instead.

    `serial_number` is NOT NULL for historical reasons, so consumable lines get a
    generated SKU (`SKU-…`) rather than a manufacturer serial.
    """
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # laptop, monitor, phone, etc.
    serial_number = Column(String, unique=True, nullable=False)
    specifications = Column(Text, nullable=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Float, nullable=True)
    warranty_expiry = Column(Date, nullable=True)
    status = Column(String, default="available")  # available, assigned, maintenance, retired
    condition = Column(String, default="good")  # excellent, good, fair, poor
    location = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── IT logistics extensions (added via ensure_columns on existing DBs) ──
    tracking_mode = Column(String, default="serialized")   # serialized | consumable
    category = Column(String, nullable=True)               # computing, peripheral, networking, accessory, cable
    brand = Column(String, nullable=True)
    model_name = Column(String, nullable=True)
    quantity_total = Column(Integer, default=1)
    quantity_available = Column(Integer, default=1)
    reorder_level = Column(Integer, default=0)             # stock floor that flags a reorder
    unit_cost = Column(Float, nullable=True)               # cost-restricted: managers only

    # Relationships
    department = relationship("Department")
    assignee = relationship("User", foreign_keys=[assigned_to])
    # AssetRequest points here twice (what was asked for vs what was issued),
    # so the join column has to be spelled out on both sides.
    requests = relationship(
        "AssetRequest", foreign_keys="AssetRequest.asset_id", back_populates="asset"
    )
    assignment_logs = relationship("AssetAssignmentLog", back_populates="asset")

class AssetRequest(Base):
    __tablename__ = "asset_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    asset_type = Column(String, nullable=False)  # For new asset requests
    request_type = Column(String, nullable=False)  # request, return, maintenance
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, approved, rejected, completed
    requested_date = Column(Date, nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    admin_comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # ── IT fulfilment extensions ──
    quantity = Column(Integer, default=1)
    priority = Column(String, default="normal")            # low, normal, high, urgent
    issued_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    fulfilled_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    employee = relationship("User", foreign_keys=[employee_id])
    asset = relationship("Asset", foreign_keys=[asset_id], back_populates="requests")
    approver = relationship("User", foreign_keys=[approved_by])
    fulfiller = relationship("User", foreign_keys=[fulfilled_by])


class AssetAssignmentLog(Base):
    """Custody ledger: every issue and every collection, append-only in spirit.

    A row is opened when IT hands an item over and closed (`returned_at` set)
    when it comes back — so offboarding is "close every open row for this user".
    """
    __tablename__ = "asset_assignment_logs"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    request_id = Column(Integer, ForeignKey("asset_requests.id"), nullable=True)

    quantity = Column(Integer, default=1)
    serial_snapshot = Column(String, nullable=True)   # serial at issue time, survives asset edits
    status = Column(String, default="assigned", index=True)  # assigned, returned, lost, damaged

    issued_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    condition_on_issue = Column(String, nullable=True)

    returned_at = Column(DateTime(timezone=True), nullable=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    condition_on_return = Column(String, nullable=True)

    notes = Column(Text, nullable=True)

    asset = relationship("Asset", back_populates="assignment_logs")
    employee = relationship("User", foreign_keys=[employee_id])
    issuer = relationship("User", foreign_keys=[issued_by])
    receiver = relationship("User", foreign_keys=[received_by])


class PurchaseRequisition(Base):
    """IT's request to buy more stock. Needs Admin or HR approval before the
    asset entry and its invoice can be filed."""
    __tablename__ = "purchase_requisitions"

    id = Column(Integer, primary_key=True, index=True)
    requisition_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    tracking_mode = Column(String, default="serialized")
    quantity = Column(Integer, default=1)

    # Cost fields are restricted to admin / hr / accountant / it.
    estimated_unit_cost = Column(Float, nullable=True)
    estimated_total = Column(Float, nullable=True)
    preferred_vendor = Column(String, nullable=True)

    justification = Column(Text, nullable=True)
    urgency = Column(String, default="normal")   # low, normal, high, urgent
    # pending -> approved -> received, or pending -> rejected
    status = Column(String, default="pending", index=True)

    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    invoices = relationship("InvoiceDocument", back_populates="requisition")


class InvoiceDocument(Base):
    """Purchase invoice attached to a requisition.

    Both the metadata and the file itself are readable only by
    admin / hr / accountant / it — enforced in the router, never in the client.
    """
    __tablename__ = "asset_invoice_documents"

    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("purchase_requisitions.id"), nullable=False, index=True)

    invoice_number = Column(String, nullable=False)
    vendor = Column(String, nullable=True)
    invoice_date = Column(Date, nullable=True)
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)

    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)

    notes = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    requisition = relationship("PurchaseRequisition", back_populates="invoices")
    uploader = relationship("User", foreign_keys=[uploaded_by])