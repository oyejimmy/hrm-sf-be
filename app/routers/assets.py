from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import date, datetime
from ..database import get_db
from ..models import Asset, AssetRequest, User, Employee
from ..schemas.asset import AssetCreate, AssetUpdate, AssetResponse, AssetRequestCreate, AssetRequestUpdate, AssetRequestResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("/", response_model=List[AssetResponse])
def get_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    assigned_to_me: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Asset)
    
    # Role-based filtering
    if current_user.role == "employee" and not assigned_to_me:
        # Employees can see available assets and their own assigned assets
        query = query.filter(or_(Asset.status == "available", Asset.assigned_to == current_user.id))
    elif assigned_to_me:
        query = query.filter(Asset.assigned_to == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Asset.status == status)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if search:
        query = query.filter(or_(
            Asset.name.ilike(f"%{search}%"),
            Asset.serial_number.ilike(f"%{search}%"),
            Asset.specifications.ilike(f"%{search}%")
        ))
    
    return query.offset(skip).limit(limit).all()

@router.get("/my-assets", response_model=List[AssetResponse])
def get_my_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Asset).filter(Asset.assigned_to == current_user.id).all()

@router.get("/stats")
def get_asset_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        # Employee stats
        assigned_count = db.query(Asset).filter(Asset.assigned_to == current_user.id).count()
        pending_requests = db.query(AssetRequest).filter(
            and_(AssetRequest.employee_id == current_user.id, AssetRequest.status == "pending")
        ).count()
        return {
            "assigned_to_me": assigned_count,
            "pending_requests": pending_requests,
            "available_assets": db.query(Asset).filter(Asset.status == "available").count(),
            "total_visible": db.query(Asset).filter(
                or_(Asset.status == "available", Asset.assigned_to == current_user.id)
            ).count()
        }
    else:
        # Admin/HR stats
        return {
            "total_assets": db.query(Asset).count(),
            "assigned_assets": db.query(Asset).filter(Asset.status == "assigned").count(),
            "available_assets": db.query(Asset).filter(Asset.status == "available").count(),
            "maintenance_assets": db.query(Asset).filter(Asset.status == "maintenance").count(),
            "pending_requests": db.query(AssetRequest).filter(AssetRequest.status == "pending").count()
        }

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if asset.status != "available" and asset.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return asset

@router.post("/", response_model=AssetResponse)
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check if serial number already exists
    existing_asset = db.query(Asset).filter(Asset.serial_number == asset.serial_number).first()
    if existing_asset:
        raise HTTPException(status_code=400, detail="Asset with this serial number already exists")
    
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: int,
    asset: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    update_data = asset.dict(exclude_unset=True)
    
    # Handle assignment logic
    if "assigned_to" in update_data:
        if update_data["assigned_to"]:
            update_data["status"] = "assigned"
            update_data["assigned_date"] = date.today()
        else:
            update_data["status"] = "available"
            update_data["assigned_date"] = None
    
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    db.commit()
    db.refresh(db_asset)
    return db_asset

@router.put("/{asset_id}/assign")
def assign_asset(
    asset_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    if asset.status != "available":
        raise HTTPException(status_code=400, detail="Asset is not available for assignment")
    
    # Verify employee exists
    employee = db.query(User).filter(User.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    asset.assigned_to = employee_id
    asset.status = "assigned"
    asset.assigned_date = date.today()
    
    db.commit()
    return {"message": "Asset assigned successfully"}

@router.put("/{asset_id}/unassign")
def unassign_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    asset.assigned_to = None
    asset.status = "available"
    asset.assigned_date = None
    
    db.commit()
    return {"message": "Asset unassigned successfully"}

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Check if asset is assigned
    if db_asset.status == "assigned":
        raise HTTPException(status_code=400, detail="Cannot delete assigned asset")
    
    # Check for pending requests
    pending_requests = db.query(AssetRequest).filter(
        and_(AssetRequest.asset_id == asset_id, AssetRequest.status == "pending")
    ).count()
    if pending_requests > 0:
        raise HTTPException(status_code=400, detail="Cannot delete asset with pending requests")
    
    db.delete(db_asset)
    db.commit()
    return {"message": "Asset deleted successfully"}

# Asset Requests
@router.get("/requests/", response_model=List[AssetRequestResponse])
def get_asset_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status: Optional[str] = Query(None),
    request_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AssetRequest)
    
    # Role-based filtering
    if current_user.role == "employee":
        query = query.filter(AssetRequest.employee_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(AssetRequest.status == status)
    if request_type:
        query = query.filter(AssetRequest.request_type == request_type)
    
    return query.order_by(AssetRequest.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/requests/my-requests", response_model=List[AssetRequestResponse])
def get_my_asset_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(AssetRequest).filter(
        AssetRequest.employee_id == current_user.id
    ).order_by(AssetRequest.created_at.desc()).all()

@router.post("/requests/", response_model=AssetRequestResponse)
def create_asset_request(
    request: AssetRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate asset exists if asset_id is provided
    if request.asset_id:
        asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        if asset.status != "available" and request.request_type == "request":
            raise HTTPException(status_code=400, detail="Asset is not available")
    
    db_request = AssetRequest(**request.dict(), employee_id=current_user.id)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.put("/requests/{request_id}", response_model=AssetRequestResponse)
def update_asset_request(
    request_id: int,
    request_update: AssetRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    update_data = request_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_request, field, value)
    
    if "status" in update_data and update_data["status"] in ["approved", "rejected"]:
        db_request.approved_by = current_user.id
        db_request.approved_at = datetime.now()
    
    db.commit()
    db.refresh(db_request)
    return db_request

@router.put("/requests/{request_id}/approve")
def approve_asset_request(
    request_id: int,
    admin_comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db_request.status = "approved"
    db_request.approved_by = current_user.id
    db_request.approved_at = datetime.now()
    if admin_comments:
        db_request.admin_comments = admin_comments
    
    # If it's a specific asset request, assign it
    if db_request.asset_id and db_request.request_type == "request":
        asset = db.query(Asset).filter(Asset.id == db_request.asset_id).first()
        if asset and asset.status == "available":
            asset.assigned_to = db_request.employee_id
            asset.status = "assigned"
            asset.assigned_date = date.today()
            db_request.completed_at = datetime.now()
    
    db.commit()
    return {"message": "Request approved successfully"}

@router.put("/requests/{request_id}/reject")
def reject_asset_request(
    request_id: int,
    admin_comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    db_request.status = "rejected"
    db_request.approved_by = current_user.id
    db_request.approved_at = datetime.now()
    if admin_comments:
        db_request.admin_comments = admin_comments
    
    db.commit()
    return {"message": "Request rejected successfully"}

@router.delete("/requests/{request_id}")
def cancel_asset_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_request = db.query(AssetRequest).filter(AssetRequest.id == request_id).first()
    if not db_request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Only allow employee to cancel their own pending requests or admin/hr to cancel any
    if current_user.role == "employee":
        if db_request.employee_id != current_user.id or db_request.status != "pending":
            raise HTTPException(status_code=403, detail="Cannot cancel this request")
    elif current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_request)
    db.commit()
    return {"message": "Request cancelled successfully"}