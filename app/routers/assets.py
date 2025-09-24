from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Asset, AssetRequest, User
from ..schemas.asset import AssetCreate, AssetUpdate, AssetResponse, AssetRequestCreate, AssetRequestResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("/", response_model=List[AssetResponse])
def get_assets(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Asset)
    if status:
        query = query.filter(Asset.status == status)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    return query.offset(skip).limit(limit).all()

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("/", response_model=AssetResponse)
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
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
    
    for field, value in asset.dict(exclude_unset=True).items():
        setattr(db_asset, field, value)
    
    db.commit()
    db.refresh(db_asset)
    return db_asset

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
    
    db.delete(db_asset)
    db.commit()
    return {"message": "Asset deleted successfully"}

# Asset Requests
@router.get("/requests/", response_model=List[AssetRequestResponse])
def get_asset_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(AssetRequest)
    if current_user.role == "employee":
        query = query.filter(AssetRequest.employee_id == current_user.id)
    if status:
        query = query.filter(AssetRequest.status == status)
    return query.offset(skip).limit(limit).all()

@router.post("/requests/", response_model=AssetRequestResponse)
def create_asset_request(
    request: AssetRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_request = AssetRequest(**request.dict(), employee_id=current_user.id)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request

@router.put("/requests/{request_id}/approve")
def approve_asset_request(
    request_id: int,
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
    db.commit()
    return {"message": "Request approved successfully"}

@router.put("/requests/{request_id}/reject")
def reject_asset_request(
    request_id: int,
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
    db.commit()
    return {"message": "Request rejected successfully"}