"""IT Asset & Inventory API.

Covers the four workflows the IT specialist owns:
  1. Inventory + custody       — who holds which item, and collecting it back
  2. Asset requests            — employees ask, IT fulfils, four roles get notified
  3. Purchase requisitions     — IT asks, Admin/HR approve, IT files the invoice
  4. Public stock directory    — spare kit any employee can see and request

Access model (single source of truth for the whole module):
  MANAGER_ROLES   admin, hr, accountant, it  → full visibility incl. costs + invoices
  OPERATOR_ROLES  admin, it                  → move stock: create, issue, collect, requisition
  APPROVER_ROLES  admin, hr                  → approve/reject purchase requisitions
  everyone else                              → own assets, public stock, own requests

Cost and invoice data never leaves this router for a non-manager: `_asset_payload`
drops the cost keys and the invoice endpoints are gated outright.
"""
import os
import shutil
import uuid
from datetime import date, datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_role
from ..database import get_db
from ..models import (
    Asset,
    AssetAssignmentLog,
    AssetRequest,
    InvoiceDocument,
    PurchaseRequisition,
    User,
)
from ..models.notification import Notification
from ..schemas.it_asset import (
    AssetItemCreate,
    AssetItemResponse,
    AssetItemUpdate,
    AssetRequestCreate,
    AssetRequestDecision,
    AssetRequestFulfil,
    AssetRequestResponse,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentReturn,
    CategoryCount,
    ITAssetStats,
    InvoiceDocumentResponse,
    PublicAssetResponse,
    RequisitionCreate,
    RequisitionDecision,
    RequisitionReceive,
    RequisitionResponse,
)

router = APIRouter(prefix="/api/it-assets", tags=["it-assets"])

MANAGER_ROLES = ("admin", "hr", "accountant", "it")
OPERATOR_ROLES = ("admin", "it")
APPROVER_ROLES = ("admin", "hr")
# Roles alerted whenever an employee raises an asset request.
REQUEST_NOTIFY_ROLES = ("it", "hr", "accountant", "admin")

operator_user = require_role(list(OPERATOR_ROLES))
manager_user = require_role(list(MANAGER_ROLES))
approver_user = require_role(list(APPROVER_ROLES))

INVOICE_DIR = "uploads/asset_invoices"
ALLOWED_INVOICE_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
}
MAX_INVOICE_BYTES = 10 * 1024 * 1024  # 10 MB


# ── helpers ─────────────────────────────────────────────────────────────────

def _is_manager(user: User) -> bool:
    return user.role in MANAGER_ROLES


def _user_names(db: Session, ids) -> Dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {u.id: u.full_name for u in db.query(User).filter(User.id.in_(ids)).all()}


def _available_units(asset: Asset) -> int:
    """Units free to issue right now, tolerating rows created before this module."""
    if asset.tracking_mode == "consumable":
        return max(int(asset.quantity_available or 0), 0)
    return 1 if asset.status == "available" and not asset.assigned_to else 0


def _asset_payload(asset: Asset, names: Dict[int, str], *, include_costs: bool) -> dict:
    total = int(asset.quantity_total or 1)
    available = _available_units(asset)
    data = {
        "id": asset.id,
        "name": asset.name,
        "asset_type": asset.asset_type,
        "serial_number": asset.serial_number,
        "category": asset.category,
        "brand": asset.brand,
        "model_name": asset.model_name,
        "specifications": asset.specifications,
        "status": asset.status,
        "condition": asset.condition,
        "location": asset.location,
        "tracking_mode": asset.tracking_mode or "serialized",
        "quantity_total": total,
        "quantity_available": available,
        "reorder_level": int(asset.reorder_level or 0),
        "is_low_stock": available <= int(asset.reorder_level or 0) and (asset.reorder_level or 0) > 0,
        "assigned_to": asset.assigned_to,
        "assigned_to_name": names.get(asset.assigned_to),
        "assigned_date": asset.assigned_date,
        "purchase_date": asset.purchase_date,
        "warranty_expiry": asset.warranty_expiry,
        "created_at": asset.created_at,
    }
    # Employees never receive the cost keys at all — not null, absent.
    if include_costs:
        data["unit_cost"] = asset.unit_cost
        data["purchase_cost"] = asset.purchase_cost
    return data


def _notify_roles(
    db: Session,
    *,
    roles,
    title: str,
    message: str,
    sender: User,
    notification_type: str = "asset",
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    action_url: Optional[str] = None,
    priority: str = "medium",
) -> int:
    """Fan a system notification out to every active holder of `roles`."""
    recipients = (
        db.query(User)
        .filter(User.role.in_(list(roles)), User.status == "active", User.id != sender.id)
        .all()
    )
    for recipient in recipients:
        db.add(
            Notification(
                recipient_id=recipient.id,
                sender_id=sender.id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                is_system_generated=True,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
            )
        )
    return len(recipients)


def _notify_user(
    db: Session,
    *,
    recipient_id: int,
    title: str,
    message: str,
    sender: User,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    action_url: Optional[str] = None,
) -> None:
    db.add(
        Notification(
            recipient_id=recipient_id,
            sender_id=sender.id,
            title=title,
            message=message,
            notification_type="asset",
            priority="medium",
            is_system_generated=True,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            action_url=action_url,
        )
    )


def _next_requisition_number(db: Session, year: int) -> str:
    count = db.query(PurchaseRequisition).filter(
        PurchaseRequisition.requisition_number.like(f"PR-{year}-%")
    ).count()
    while True:
        count += 1
        candidate = f"PR-{year}-{count:04d}"
        if not db.query(PurchaseRequisition).filter(
            PurchaseRequisition.requisition_number == candidate
        ).first():
            return candidate


def _generate_sku(db: Session, name: str) -> str:
    """Consumable lines have no manufacturer serial, but the column is NOT NULL."""
    slug = "".join(ch for ch in name.upper() if ch.isalnum())[:10] or "ITEM"
    while True:
        candidate = f"SKU-{slug}-{uuid.uuid4().hex[:6].upper()}"
        if not db.query(Asset).filter(Asset.serial_number == candidate).first():
            return candidate


# ── Inventory ───────────────────────────────────────────────────────────────

@router.get("/inventory", response_model=List[AssetItemResponse])
def list_inventory(
    search: Optional[str] = None,
    category: Optional[str] = None,
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    tracking_mode: Optional[str] = None,
    low_stock_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(300, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_user),
):
    query = db.query(Asset)
    if category:
        query = query.filter(Asset.category == category)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if status:
        query = query.filter(Asset.status == status)
    if tracking_mode:
        query = query.filter(Asset.tracking_mode == tracking_mode)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Asset.name.ilike(term),
                Asset.serial_number.ilike(term),
                Asset.brand.ilike(term),
                Asset.model_name.ilike(term),
                Asset.asset_type.ilike(term),
            )
        )

    assets = query.order_by(Asset.name.asc()).offset(skip).limit(limit).all()
    names = _user_names(db, [a.assigned_to for a in assets])
    payload = [_asset_payload(a, names, include_costs=True) for a in assets]
    if low_stock_only:
        payload = [p for p in payload if p["is_low_stock"]]
    return payload


@router.get("/inventory/available", response_model=List[PublicAssetResponse])
def list_available_stock(
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Public "Available Office Assets" directory — every authenticated employee.

    Unassigned stock only. `PublicAssetResponse` carries no cost fields, so this
    endpoint cannot expose purchase prices to anyone regardless of role.
    """
    query = db.query(Asset).filter(Asset.status.notin_(("retired", "maintenance")))
    if category:
        query = query.filter(Asset.category == category)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Asset.name.ilike(term), Asset.asset_type.ilike(term), Asset.brand.ilike(term)))

    assets = query.order_by(Asset.name.asc()).all()
    return [
        _asset_payload(a, {}, include_costs=False)
        for a in assets
        if _available_units(a) > 0
    ]


@router.get("/inventory/categories")
def list_categories(current_user: User = Depends(get_current_user)):
    return [
        {"value": "computing", "label": "Computing"},
        {"value": "peripheral", "label": "Peripherals"},
        {"value": "display", "label": "Displays"},
        {"value": "cable", "label": "Cables & Adapters"},
        {"value": "networking", "label": "Networking"},
        {"value": "accessory", "label": "Accessories"},
        {"value": "consumable", "label": "Consumables"},
    ]


@router.get("/employees")
def list_assignable_employees(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """Minimal staff directory for the "issue to…" picker.

    `/api/employees` is gated to admin/hr, so IT cannot use it. Rather than
    widening that endpoint, this returns only what a picker needs — no salary,
    no personal data — and stays behind OPERATOR_ROLES.
    """
    query = db.query(User).filter(User.status == "active")
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(User.first_name.ilike(term), User.last_name.ilike(term), User.email.ilike(term))
        )

    users = query.order_by(User.first_name.asc()).limit(500).all()
    holdings: Dict[int, int] = {}
    for log in db.query(AssetAssignmentLog).filter(AssetAssignmentLog.status == "assigned").all():
        holdings[log.employee_id] = holdings.get(log.employee_id, 0) + int(log.quantity or 1)

    return [
        {
            "id": u.id,
            "name": u.full_name,
            "email": u.email,
            "role": u.role,
            "assets_held": holdings.get(u.id, 0),
        }
        for u in users
    ]


@router.post("/inventory", response_model=AssetItemResponse, status_code=201)
def create_asset(
    payload: AssetItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    consumable = payload.tracking_mode == "consumable"

    if consumable:
        serial = payload.serial_number or _generate_sku(db, payload.name)
        quantity = max(int(payload.quantity_total or 0), 0)
    else:
        if not payload.serial_number:
            raise HTTPException(status_code=422, detail="Serialized assets need a serial number")
        serial = payload.serial_number
        quantity = 1

    if db.query(Asset).filter(Asset.serial_number == serial).first():
        raise HTTPException(status_code=409, detail=f"An asset with serial '{serial}' already exists")

    asset = Asset(
        name=payload.name,
        asset_type=payload.asset_type,
        serial_number=serial,
        category=payload.category,
        brand=payload.brand,
        model_name=payload.model_name,
        specifications=payload.specifications,
        condition=payload.condition or "good",
        location=payload.location,
        tracking_mode=payload.tracking_mode,
        quantity_total=quantity,
        quantity_available=quantity,
        reorder_level=payload.reorder_level or 0,
        unit_cost=payload.unit_cost,
        purchase_cost=payload.purchase_cost if payload.purchase_cost is not None
        else (payload.unit_cost * quantity if payload.unit_cost else None),
        purchase_date=payload.purchase_date,
        warranty_expiry=payload.warranty_expiry,
        status="available",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _asset_payload(asset, {}, include_costs=True)


@router.put("/inventory/{asset_id}", response_model=AssetItemResponse)
def update_asset(
    asset_id: int,
    payload: AssetItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    updates = payload.dict(exclude_unset=True)

    # Restocking a consumable moves total and available together, so IT doesn't
    # have to reason about how many are currently out on loan.
    if "quantity_total" in updates and (asset.tracking_mode or "serialized") == "consumable":
        delta = int(updates["quantity_total"]) - int(asset.quantity_total or 0)
        asset.quantity_available = max(int(asset.quantity_available or 0) + delta, 0)

    for field, value in updates.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    names = _user_names(db, [asset.assigned_to])
    return _asset_payload(asset, names, include_costs=True)


@router.delete("/inventory/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    logs = db.query(AssetAssignmentLog).filter(AssetAssignmentLog.asset_id == asset_id).all()
    if any(log.status == "assigned" for log in logs):
        raise HTTPException(status_code=409, detail="Collect this asset from its holders before deleting it")
    if logs:
        # Custody history is an audit record. Deleting the asset would orphan it
        # (SQLAlchemy nulls the child FK, which is NOT NULL), and more to the
        # point we should not lose the record of who once held the item.
        raise HTTPException(
            status_code=409,
            detail="This asset has custody history and cannot be deleted. Set its status to 'retired' instead.",
        )

    db.delete(asset)
    db.commit()
    return {"message": "Asset removed from inventory", "asset_id": asset_id}


# ── Custody / assignments ───────────────────────────────────────────────────

def _assignment_payload(log: AssetAssignmentLog, assets: Dict[int, Asset], names: Dict[int, str], emails: Dict[int, str]) -> dict:
    asset = assets.get(log.asset_id)
    return {
        "id": log.id,
        "asset_id": log.asset_id,
        "asset_name": asset.name if asset else None,
        "asset_type": asset.asset_type if asset else None,
        "category": asset.category if asset else None,
        "employee_id": log.employee_id,
        "employee_name": names.get(log.employee_id),
        "employee_email": emails.get(log.employee_id),
        "quantity": int(log.quantity or 1),
        "serial_snapshot": log.serial_snapshot,
        "status": log.status,
        "issued_by": log.issued_by,
        "issued_by_name": names.get(log.issued_by),
        "issued_at": log.issued_at,
        "condition_on_issue": log.condition_on_issue,
        "returned_at": log.returned_at,
        "received_by": log.received_by,
        "condition_on_return": log.condition_on_return,
        "notes": log.notes,
    }


def _load_assignments(db: Session, logs: List[AssetAssignmentLog]) -> List[dict]:
    asset_ids = {l.asset_id for l in logs}
    assets = {a.id: a for a in db.query(Asset).filter(Asset.id.in_(asset_ids)).all()} if asset_ids else {}
    user_ids = {l.employee_id for l in logs} | {l.issued_by for l in logs}
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    names = {u.id: u.full_name for u in users}
    emails = {u.id: u.email for u in users}
    return [_assignment_payload(l, assets, names, emails) for l in logs]


@router.get("/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    employee_id: Optional[int] = None,
    asset_id: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_user),
):
    """Who holds what. Defaults to open custody; pass status to see history."""
    query = db.query(AssetAssignmentLog)
    if employee_id:
        query = query.filter(AssetAssignmentLog.employee_id == employee_id)
    if asset_id:
        query = query.filter(AssetAssignmentLog.asset_id == asset_id)
    if status:
        query = query.filter(AssetAssignmentLog.status == status)

    logs = query.order_by(AssetAssignmentLog.issued_at.desc(), AssetAssignmentLog.id.desc()).limit(500).all()
    payload = _load_assignments(db, logs)

    if search:
        term = search.lower()
        payload = [
            p for p in payload
            if term in (p["employee_name"] or "").lower()
            or term in (p["asset_name"] or "").lower()
            or term in (p["serial_snapshot"] or "").lower()
        ]
    return payload


@router.get("/assignments/me", response_model=List[AssignmentResponse])
def my_assignments(
    include_returned: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AssetAssignmentLog).filter(AssetAssignmentLog.employee_id == current_user.id)
    if not include_returned:
        query = query.filter(AssetAssignmentLog.status == "assigned")
    logs = query.order_by(AssetAssignmentLog.issued_at.desc()).all()
    return _load_assignments(db, logs)


def _issue_asset(
    db: Session,
    *,
    asset: Asset,
    employee: User,
    quantity: int,
    issuer: User,
    condition: Optional[str] = None,
    notes: Optional[str] = None,
    request_id: Optional[int] = None,
) -> AssetAssignmentLog:
    """Move stock out and open a custody row. Caller owns the commit."""
    consumable = (asset.tracking_mode or "serialized") == "consumable"
    available = _available_units(asset)

    if consumable:
        if quantity > available:
            raise HTTPException(
                status_code=409,
                detail=f"Only {available} unit(s) of '{asset.name}' are in stock",
            )
        asset.quantity_available = available - quantity
        if asset.quantity_available == 0:
            asset.status = "assigned"
    else:
        if available < 1:
            raise HTTPException(status_code=409, detail=f"'{asset.name}' is already assigned")
        quantity = 1
        asset.assigned_to = employee.id
        asset.assigned_date = date.today()
        asset.status = "assigned"
        asset.quantity_available = 0

    log = AssetAssignmentLog(
        asset_id=asset.id,
        employee_id=employee.id,
        request_id=request_id,
        quantity=quantity,
        serial_snapshot=asset.serial_number,
        status="assigned",
        issued_by=issuer.id,
        condition_on_issue=condition or asset.condition,
        notes=notes,
    )
    db.add(log)
    return log


@router.post("/assignments", response_model=AssignmentResponse, status_code=201)
def issue_asset(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    employee = db.query(User).filter(User.id == payload.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    log = _issue_asset(
        db,
        asset=asset,
        employee=employee,
        quantity=payload.quantity,
        issuer=current_user,
        condition=payload.condition_on_issue,
        notes=payload.notes,
        request_id=payload.request_id,
    )
    _notify_user(
        db,
        recipient_id=employee.id,
        title="Asset issued to you",
        message=f"{asset.name} ({asset.serial_number}) has been issued to you by IT.",
        sender=current_user,
        related_entity_type="asset",
        related_entity_id=asset.id,
    )
    db.commit()
    db.refresh(log)
    return _load_assignments(db, [log])[0]


@router.put("/assignments/{log_id}/return", response_model=AssignmentResponse)
def collect_asset(
    log_id: int,
    payload: AssignmentReturn,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """Collect an item back — the offboarding / handover step."""
    log = db.query(AssetAssignmentLog).filter(AssetAssignmentLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if log.status != "assigned":
        raise HTTPException(status_code=409, detail=f"This assignment is already closed ({log.status})")
    if payload.status not in ("returned", "lost", "damaged"):
        raise HTTPException(status_code=422, detail="status must be returned, lost or damaged")

    asset = db.query(Asset).filter(Asset.id == log.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset no longer exists")

    consumable = (asset.tracking_mode or "serialized") == "consumable"
    quantity = int(log.quantity or 1)

    if payload.status == "returned":
        if consumable:
            asset.quantity_available = int(asset.quantity_available or 0) + quantity
        else:
            asset.assigned_to = None
            asset.assigned_date = None
            asset.quantity_available = 1
        asset.status = "available"
        if payload.condition_on_return:
            asset.condition = payload.condition_on_return
    else:
        # Lost or damaged stock leaves the pool rather than returning to it.
        if consumable:
            asset.quantity_total = max(int(asset.quantity_total or 0) - quantity, 0)
            if asset.quantity_total == 0:
                asset.status = "retired"
        else:
            asset.assigned_to = None
            asset.assigned_date = None
            asset.quantity_available = 0
            asset.status = "retired" if payload.status == "lost" else "maintenance"

    log.status = payload.status
    log.returned_at = datetime.utcnow()
    log.received_by = current_user.id
    log.condition_on_return = payload.condition_on_return
    if payload.notes:
        log.notes = f"{log.notes}\n{payload.notes}" if log.notes else payload.notes

    db.commit()
    db.refresh(log)
    return _load_assignments(db, [log])[0]


@router.post("/assignments/collect-all/{employee_id}")
def collect_all_from_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """Offboarding sweep: close every open custody row for one employee."""
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    logs = db.query(AssetAssignmentLog).filter(
        AssetAssignmentLog.employee_id == employee_id,
        AssetAssignmentLog.status == "assigned",
    ).all()
    if not logs:
        return {"message": "This employee is not holding any assets", "collected": 0}

    assets = {a.id: a for a in db.query(Asset).filter(Asset.id.in_({l.asset_id for l in logs})).all()}
    for log in logs:
        asset = assets.get(log.asset_id)
        if asset:
            if (asset.tracking_mode or "serialized") == "consumable":
                asset.quantity_available = int(asset.quantity_available or 0) + int(log.quantity or 1)
            else:
                asset.assigned_to = None
                asset.assigned_date = None
                asset.quantity_available = 1
            asset.status = "available"
        log.status = "returned"
        log.returned_at = datetime.utcnow()
        log.received_by = current_user.id

    _notify_roles(
        db,
        roles=("hr", "admin"),
        title="Assets collected on offboarding",
        message=f"IT collected {len(logs)} asset(s) from {employee.full_name}.",
        sender=current_user,
        related_entity_type="employee",
        related_entity_id=employee_id,
    )
    db.commit()
    return {"message": f"Collected {len(logs)} asset(s) from {employee.full_name}", "collected": len(logs)}


# ── Asset requests ──────────────────────────────────────────────────────────

def _request_payload(req: AssetRequest, names: Dict[int, str], assets: Dict[int, Asset]) -> dict:
    issued = assets.get(req.issued_asset_id) if req.issued_asset_id else None
    return {
        "id": req.id,
        "employee_id": req.employee_id,
        "employee_name": names.get(req.employee_id),
        "asset_id": req.asset_id,
        "asset_type": req.asset_type,
        "request_type": req.request_type,
        "quantity": int(req.quantity or 1),
        "priority": req.priority or "normal",
        "reason": req.reason,
        "status": req.status,
        "requested_date": req.requested_date,
        "issued_asset_id": req.issued_asset_id,
        "issued_asset_name": issued.name if issued else None,
        "issued_serial": issued.serial_number if issued else None,
        "fulfilled_by": req.fulfilled_by,
        "fulfilled_by_name": names.get(req.fulfilled_by),
        "fulfilled_at": req.fulfilled_at,
        "admin_comments": req.admin_comments,
        "created_at": req.created_at,
    }


def _load_requests(db: Session, requests: List[AssetRequest]) -> List[dict]:
    names = _user_names(
        db, [r.employee_id for r in requests] + [r.fulfilled_by for r in requests]
    )
    asset_ids = {r.issued_asset_id for r in requests if r.issued_asset_id}
    assets = {a.id: a for a in db.query(Asset).filter(Asset.id.in_(asset_ids)).all()} if asset_ids else {}
    return [_request_payload(r, names, assets) for r in requests]


@router.get("/requests", response_model=List[AssetRequestResponse])
def list_asset_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    mine: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AssetRequest)
    # Non-managers only ever see their own tickets.
    if mine or not _is_manager(current_user):
        query = query.filter(AssetRequest.employee_id == current_user.id)
    if status:
        query = query.filter(AssetRequest.status == status)
    if priority:
        query = query.filter(AssetRequest.priority == priority)

    requests = query.order_by(AssetRequest.created_at.desc(), AssetRequest.id.desc()).limit(400).all()
    return _load_requests(db, requests)


@router.post("/requests", response_model=AssetRequestResponse, status_code=201)
def create_asset_request(
    payload: AssetRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Any employee can raise a ticket. IT, HR, Accountant and Admin are all told."""
    if payload.asset_id and not db.query(Asset).filter(Asset.id == payload.asset_id).first():
        raise HTTPException(status_code=404, detail="Requested asset not found")

    request = AssetRequest(
        employee_id=current_user.id,
        asset_id=payload.asset_id,
        asset_type=payload.asset_type,
        request_type="request",
        quantity=payload.quantity,
        priority=payload.priority,
        reason=payload.reason,
        status="pending",
        requested_date=date.today(),
    )
    db.add(request)
    db.flush()

    notified = _notify_roles(
        db,
        roles=REQUEST_NOTIFY_ROLES,
        title="New asset request",
        message=(
            f"{current_user.full_name} requested {payload.quantity} × {payload.asset_type}. "
            f"Reason: {payload.reason}"
        ),
        sender=current_user,
        related_entity_type="asset_request",
        related_entity_id=request.id,
        action_url="/it/requests",
        priority="high" if payload.priority in ("high", "urgent") else "medium",
    )
    db.commit()
    db.refresh(request)

    result = _load_requests(db, [request])[0]
    result["admin_comments"] = result.get("admin_comments")
    # `notified` is intentionally not part of the schema; it's visible in logs only.
    print(f"[it-assets] request {request.id} notified {notified} recipient(s)")
    return result


@router.put("/requests/{request_id}/fulfil", response_model=AssetRequestResponse)
def fulfil_asset_request(
    request_id: int,
    payload: AssetRequestFulfil,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """IT issues the item: opens custody, stamps the request with serial + time."""
    request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status not in ("pending", "approved"):
        raise HTTPException(status_code=409, detail=f"This request is already {request.status}")

    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    employee = db.query(User).filter(User.id == request.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Requesting employee no longer exists")

    _issue_asset(
        db,
        asset=asset,
        employee=employee,
        quantity=payload.quantity or int(request.quantity or 1),
        issuer=current_user,
        condition=payload.condition_on_issue,
        notes=payload.notes,
        request_id=request.id,
    )

    request.status = "completed"
    request.issued_asset_id = asset.id
    request.fulfilled_by = current_user.id
    request.fulfilled_at = datetime.utcnow()
    request.completed_at = datetime.utcnow()
    if payload.notes:
        request.admin_comments = payload.notes

    _notify_user(
        db,
        recipient_id=employee.id,
        title="Asset request fulfilled",
        message=f"Your request for {request.asset_type} was fulfilled: {asset.name} ({asset.serial_number}).",
        sender=current_user,
        related_entity_type="asset_request",
        related_entity_id=request.id,
    )
    db.commit()
    db.refresh(request)
    return _load_requests(db, [request])[0]


@router.put("/requests/{request_id}/reject", response_model=AssetRequestResponse)
def reject_asset_request(
    request_id: int,
    payload: AssetRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != "pending":
        raise HTTPException(status_code=409, detail=f"This request is already {request.status}")

    request.status = "rejected"
    request.approved_by = current_user.id
    request.approved_at = datetime.utcnow()
    request.admin_comments = payload.admin_comments

    _notify_user(
        db,
        recipient_id=request.employee_id,
        title="Asset request declined",
        message=f"Your request for {request.asset_type} was declined."
        + (f" Reason: {payload.admin_comments}" if payload.admin_comments else ""),
        sender=current_user,
        related_entity_type="asset_request",
        related_entity_id=request.id,
    )
    db.commit()
    db.refresh(request)
    return _load_requests(db, [request])[0]


# ── Purchase requisitions ───────────────────────────────────────────────────

def _requisition_payload(req: PurchaseRequisition, names: Dict[int, str], invoice_counts: Dict[int, int]) -> dict:
    return {
        "id": req.id,
        "requisition_number": req.requisition_number,
        "title": req.title,
        "item_name": req.item_name,
        "category": req.category,
        "tracking_mode": req.tracking_mode or "serialized",
        "quantity": int(req.quantity or 1),
        "estimated_unit_cost": req.estimated_unit_cost,
        "estimated_total": req.estimated_total,
        "preferred_vendor": req.preferred_vendor,
        "justification": req.justification,
        "urgency": req.urgency or "normal",
        "status": req.status,
        "requested_by": req.requested_by,
        "requested_by_name": names.get(req.requested_by),
        "approved_by": req.approved_by,
        "approved_by_name": names.get(req.approved_by),
        "approved_at": req.approved_at,
        "rejection_reason": req.rejection_reason,
        "received_at": req.received_at,
        "created_asset_id": req.created_asset_id,
        "invoice_count": invoice_counts.get(req.id, 0),
        "created_at": req.created_at,
    }


def _load_requisitions(db: Session, requisitions: List[PurchaseRequisition]) -> List[dict]:
    names = _user_names(
        db, [r.requested_by for r in requisitions] + [r.approved_by for r in requisitions]
    )
    ids = [r.id for r in requisitions]
    counts: Dict[int, int] = {}
    if ids:
        for inv in db.query(InvoiceDocument).filter(InvoiceDocument.requisition_id.in_(ids)).all():
            counts[inv.requisition_id] = counts.get(inv.requisition_id, 0) + 1
    return [_requisition_payload(r, names, counts) for r in requisitions]


@router.get("/requisitions", response_model=List[RequisitionResponse])
def list_requisitions(
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_user),
):
    """Restricted: requisitions carry cost data, so managers only."""
    query = db.query(PurchaseRequisition)
    if status:
        query = query.filter(PurchaseRequisition.status == status)
    if urgency:
        query = query.filter(PurchaseRequisition.urgency == urgency)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                PurchaseRequisition.title.ilike(term),
                PurchaseRequisition.item_name.ilike(term),
                PurchaseRequisition.requisition_number.ilike(term),
                PurchaseRequisition.preferred_vendor.ilike(term),
            )
        )

    requisitions = query.order_by(PurchaseRequisition.created_at.desc(), PurchaseRequisition.id.desc()).all()
    return _load_requisitions(db, requisitions)


@router.post("/requisitions", response_model=RequisitionResponse, status_code=201)
def create_requisition(
    payload: RequisitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """IT asks to buy stock; Admin and HR are notified to approve."""
    estimated_total = (
        round(payload.estimated_unit_cost * payload.quantity, 2)
        if payload.estimated_unit_cost is not None
        else None
    )
    requisition = PurchaseRequisition(
        requisition_number=_next_requisition_number(db, date.today().year),
        title=payload.title,
        item_name=payload.item_name,
        category=payload.category,
        tracking_mode=payload.tracking_mode,
        quantity=payload.quantity,
        estimated_unit_cost=payload.estimated_unit_cost,
        estimated_total=estimated_total,
        preferred_vendor=payload.preferred_vendor,
        justification=payload.justification,
        urgency=payload.urgency,
        status="pending",
        requested_by=current_user.id,
    )
    db.add(requisition)
    db.flush()

    _notify_roles(
        db,
        roles=APPROVER_ROLES,
        title="Purchase requisition awaiting approval",
        message=(
            f"{current_user.full_name} raised {requisition.requisition_number} for "
            f"{payload.quantity} × {payload.item_name}."
        ),
        sender=current_user,
        related_entity_type="purchase_requisition",
        related_entity_id=requisition.id,
        action_url="/it/requisitions",
        priority="high" if payload.urgency in ("high", "urgent") else "medium",
    )
    db.commit()
    db.refresh(requisition)
    return _load_requisitions(db, [requisition])[0]


@router.put("/requisitions/{requisition_id}/approve", response_model=RequisitionResponse)
def approve_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(approver_user),
):
    requisition = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if requisition.status != "pending":
        raise HTTPException(status_code=409, detail=f"This requisition is already {requisition.status}")
    if requisition.requested_by == current_user.id:
        raise HTTPException(status_code=403, detail="A requisition must be approved by someone other than its author")

    requisition.status = "approved"
    requisition.approved_by = current_user.id
    requisition.approved_at = datetime.utcnow()

    _notify_user(
        db,
        recipient_id=requisition.requested_by,
        title="Purchase requisition approved",
        message=f"{requisition.requisition_number} was approved. You can now file the asset and its invoice.",
        sender=current_user,
        related_entity_type="purchase_requisition",
        related_entity_id=requisition.id,
        action_url="/it/requisitions",
    )
    db.commit()
    db.refresh(requisition)
    return _load_requisitions(db, [requisition])[0]


@router.put("/requisitions/{requisition_id}/reject", response_model=RequisitionResponse)
def reject_requisition(
    requisition_id: int,
    payload: RequisitionDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(approver_user),
):
    requisition = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if requisition.status != "pending":
        raise HTTPException(status_code=409, detail=f"This requisition is already {requisition.status}")

    requisition.status = "rejected"
    requisition.approved_by = current_user.id
    requisition.approved_at = datetime.utcnow()
    requisition.rejection_reason = payload.reason

    _notify_user(
        db,
        recipient_id=requisition.requested_by,
        title="Purchase requisition declined",
        message=f"{requisition.requisition_number} was declined."
        + (f" Reason: {payload.reason}" if payload.reason else ""),
        sender=current_user,
        related_entity_type="purchase_requisition",
        related_entity_id=requisition.id,
    )
    db.commit()
    db.refresh(requisition)
    return _load_requisitions(db, [requisition])[0]


@router.post("/requisitions/{requisition_id}/receive", response_model=RequisitionResponse)
def receive_requisition(
    requisition_id: int,
    payload: RequisitionReceive,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """Approved stock arrived — create the inventory entry from the requisition."""
    requisition = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if requisition.status != "approved":
        raise HTTPException(status_code=409, detail="Only approved requisitions can be received into stock")

    consumable = (requisition.tracking_mode or "serialized") == "consumable"
    quantity = int(requisition.quantity or 1)

    if consumable:
        serial = payload.serial_number or _generate_sku(db, requisition.item_name)
    else:
        if not payload.serial_number:
            raise HTTPException(status_code=422, detail="Serialized stock needs a serial number")
        serial = payload.serial_number
        quantity = 1

    if db.query(Asset).filter(Asset.serial_number == serial).first():
        raise HTTPException(status_code=409, detail=f"An asset with serial '{serial}' already exists")

    unit_cost = payload.actual_unit_cost if payload.actual_unit_cost is not None else requisition.estimated_unit_cost
    asset = Asset(
        name=requisition.item_name,
        asset_type=requisition.item_name,
        serial_number=serial,
        category=requisition.category,
        tracking_mode=requisition.tracking_mode or "serialized",
        quantity_total=quantity,
        quantity_available=quantity,
        condition=payload.condition or "excellent",
        location=payload.location,
        unit_cost=unit_cost,
        purchase_cost=round(unit_cost * quantity, 2) if unit_cost else None,
        purchase_date=date.today(),
        status="available",
    )
    db.add(asset)
    db.flush()

    requisition.status = "received"
    requisition.received_at = datetime.utcnow()
    requisition.created_asset_id = asset.id

    db.commit()
    db.refresh(requisition)
    return _load_requisitions(db, [requisition])[0]


# ── Invoices (admin / hr / accountant / it only) ────────────────────────────

def _invoice_payload(inv: InvoiceDocument, names: Dict[int, str], numbers: Dict[int, str]) -> dict:
    return {
        "id": inv.id,
        "requisition_id": inv.requisition_id,
        "requisition_number": numbers.get(inv.requisition_id),
        "invoice_number": inv.invoice_number,
        "vendor": inv.vendor,
        "invoice_date": inv.invoice_date,
        "amount": inv.amount,
        "tax_amount": inv.tax_amount or 0.0,
        "file_name": inv.file_name,
        "content_type": inv.content_type,
        "file_size": inv.file_size,
        "has_file": bool(inv.file_path),
        "notes": inv.notes,
        "uploaded_by": inv.uploaded_by,
        "uploaded_by_name": names.get(inv.uploaded_by),
        "uploaded_at": inv.uploaded_at,
    }


def _load_invoices(db: Session, invoices: List[InvoiceDocument]) -> List[dict]:
    names = _user_names(db, [i.uploaded_by for i in invoices])
    req_ids = {i.requisition_id for i in invoices}
    numbers = (
        {r.id: r.requisition_number
         for r in db.query(PurchaseRequisition).filter(PurchaseRequisition.id.in_(req_ids)).all()}
        if req_ids else {}
    )
    return [_invoice_payload(i, names, numbers) for i in invoices]


@router.get("/invoices", response_model=List[InvoiceDocumentResponse])
def list_invoices(
    requisition_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_user),
):
    query = db.query(InvoiceDocument)
    if requisition_id:
        query = query.filter(InvoiceDocument.requisition_id == requisition_id)
    invoices = query.order_by(InvoiceDocument.uploaded_at.desc()).all()
    return _load_invoices(db, invoices)


@router.post("/requisitions/{requisition_id}/invoice", response_model=InvoiceDocumentResponse, status_code=201)
async def upload_invoice(
    requisition_id: int,
    invoice_number: str = Form(...),
    amount: float = Form(...),
    vendor: Optional[str] = Form(None),
    invoice_date: Optional[str] = Form(None),
    tax_amount: float = Form(0.0),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    """Attach the purchase invoice to an approved requisition."""
    requisition = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == requisition_id).first()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if requisition.status not in ("approved", "received"):
        raise HTTPException(status_code=409, detail="Invoices can only be filed against an approved requisition")
    if amount <= 0:
        raise HTTPException(status_code=422, detail="Invoice amount must be greater than zero")

    parsed_date = None
    if invoice_date:
        try:
            parsed_date = date.fromisoformat(invoice_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="invoice_date must be YYYY-MM-DD")

    file_path = file_name = content_type = None
    file_size = None
    if file is not None and file.filename:
        if file.content_type not in ALLOWED_INVOICE_TYPES:
            raise HTTPException(
                status_code=415,
                detail="Invoice must be a PDF, image or spreadsheet",
            )
        contents = await file.read()
        if len(contents) > MAX_INVOICE_BYTES:
            raise HTTPException(status_code=413, detail="Invoice file must be 10 MB or smaller")

        os.makedirs(INVOICE_DIR, exist_ok=True)
        extension = os.path.splitext(file.filename)[1][:10]
        stored_name = f"{uuid.uuid4().hex}{extension}"
        file_path = os.path.join(INVOICE_DIR, stored_name)
        try:
            with open(file_path, "wb") as buffer:
                buffer.write(contents)
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"Could not store the invoice file: {exc}")

        file_name = file.filename
        content_type = file.content_type
        file_size = len(contents)

    invoice = InvoiceDocument(
        requisition_id=requisition_id,
        invoice_number=invoice_number,
        vendor=vendor,
        invoice_date=parsed_date,
        amount=amount,
        tax_amount=tax_amount or 0.0,
        file_name=file_name,
        file_path=file_path,
        content_type=content_type,
        file_size=file_size,
        notes=notes,
        uploaded_by=current_user.id,
    )
    db.add(invoice)

    _notify_roles(
        db,
        roles=("accountant", "admin"),
        title="Purchase invoice filed",
        message=(
            f"{current_user.full_name} filed invoice {invoice_number} "
            f"({amount:.2f}) against {requisition.requisition_number}."
        ),
        sender=current_user,
        related_entity_type="purchase_requisition",
        related_entity_id=requisition_id,
        action_url="/it/requisitions",
    )
    db.commit()
    db.refresh(invoice)
    return _load_invoices(db, [invoice])[0]


@router.get("/invoices/{invoice_id}/file")
def download_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(manager_user),
):
    """Streams the stored invoice. Gated to admin / hr / accountant / it."""
    invoice = db.query(InvoiceDocument).filter(InvoiceDocument.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if not invoice.file_path or not os.path.exists(invoice.file_path):
        raise HTTPException(status_code=404, detail="No file was attached to this invoice")

    return FileResponse(
        invoice.file_path,
        media_type=invoice.content_type or "application/octet-stream",
        filename=invoice.file_name or f"invoice-{invoice.invoice_number}",
    )


@router.delete("/invoices/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_user),
):
    invoice = db.query(InvoiceDocument).filter(InvoiceDocument.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    if invoice.file_path and os.path.exists(invoice.file_path):
        try:
            os.remove(invoice.file_path)
        except OSError:
            pass  # metadata removal still proceeds

    db.delete(invoice)
    db.commit()
    return {"message": "Invoice removed", "invoice_id": invoice_id}


# ── Dashboard stats ─────────────────────────────────────────────────────────

@router.get("/stats", response_model=ITAssetStats)
def asset_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Shared by every role; cost figures are withheld from non-managers."""
    assets = db.query(Asset).all()
    manager = _is_manager(current_user)

    total_units = sum(int(a.quantity_total or 1) for a in assets)
    available_units = sum(_available_units(a) for a in assets)

    open_logs = db.query(AssetAssignmentLog).filter(AssetAssignmentLog.status == "assigned").all()
    assigned_units = sum(int(l.quantity or 1) for l in open_logs)

    by_category: Dict[str, CategoryCount] = {}
    for asset in assets:
        key = asset.category or "uncategorised"
        bucket = by_category.setdefault(key, CategoryCount(category=key, total=0, available=0, assigned=0))
        bucket.total += int(asset.quantity_total or 1)
        bucket.available += _available_units(asset)
        bucket.assigned += max(int(asset.quantity_total or 1) - _available_units(asset), 0)

    stats = ITAssetStats(
        total_assets=len(assets),
        total_units=total_units,
        available_units=available_units,
        assigned_units=assigned_units,
        maintenance_assets=sum(1 for a in assets if a.status == "maintenance"),
        low_stock_items=sum(
            1 for a in assets
            if (a.reorder_level or 0) > 0 and _available_units(a) <= int(a.reorder_level or 0)
        ),
        employees_holding_assets=len({l.employee_id for l in open_logs}),
        pending_requests=db.query(AssetRequest).filter(AssetRequest.status == "pending").count(),
        urgent_requests=db.query(AssetRequest).filter(
            AssetRequest.status == "pending", AssetRequest.priority.in_(("high", "urgent"))
        ).count(),
        pending_requisitions=db.query(PurchaseRequisition).filter(
            PurchaseRequisition.status == "pending"
        ).count(),
        approved_requisitions=db.query(PurchaseRequisition).filter(
            PurchaseRequisition.status == "approved"
        ).count(),
        by_category=sorted(by_category.values(), key=lambda c: c.total, reverse=True),
    )

    if manager:
        stats.inventory_value = round(
            sum((a.unit_cost or 0) * int(a.quantity_total or 1) for a in assets), 2
        )
        stats.pending_requisition_value = round(
            sum(
                r.estimated_total or 0
                for r in db.query(PurchaseRequisition).filter(PurchaseRequisition.status == "pending").all()
            ),
            2,
        )
        stats.invoiced_total = round(
            sum((i.amount or 0) + (i.tax_amount or 0) for i in db.query(InvoiceDocument).all()), 2
        )
    else:
        # An employee's view of the pending queue is their own tickets only.
        stats.pending_requests = db.query(AssetRequest).filter(
            AssetRequest.status == "pending", AssetRequest.employee_id == current_user.id
        ).count()
        stats.urgent_requests = 0
        stats.pending_requisitions = 0
        stats.approved_requisitions = 0

    return stats
