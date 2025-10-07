from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date
import os
import shutil
from ..database import get_db
from ..models import Document, DocumentVersion, DocumentType, User, Employee
from ..schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentVersionResponse, DocumentTypeResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    employee_id: Optional[int] = Query(None),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document)
    
    # Role-based filtering
    if current_user.role == "employee":
        # Employees can see their own documents and shared documents
        query = query.filter(
            or_(
                Document.employee_id == current_user.id,
                and_(Document.status == "approved", Document.category.in_(["HR", "Training", "Company"]))
            )
        )
    elif employee_id and current_user.role in ["admin", "hr"]:
        query = query.filter(Document.employee_id == employee_id)
    
    # Apply filters
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if status:
        query = query.filter(Document.status == status)
    if category:
        query = query.filter(Document.category == category)
    if search:
        query = query.filter(
            or_(
                Document.file_name.ilike(f"%{search}%"),
                Document.document_type.ilike(f"%{search}%"),
                Document.category.ilike(f"%{search}%"),
                Document.description.ilike(f"%{search}%")
            )
        )
    
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/my-documents", response_model=List[DocumentResponse])
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Document).filter(
        Document.employee_id == current_user.id
    ).order_by(Document.created_at.desc()).all()

@router.get("/stats")
def get_document_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        my_docs = db.query(Document).filter(Document.employee_id == current_user.id).count()
        pending_docs = db.query(Document).filter(
            and_(Document.employee_id == current_user.id, Document.status == "pending")
        ).count()
        approved_docs = db.query(Document).filter(
            and_(Document.employee_id == current_user.id, Document.status == "approved")
        ).count()
        shared_docs = db.query(Document).filter(
            and_(Document.status == "approved", Document.category.in_(["HR", "Training", "Company"]))
        ).count()
        
        return {
            "my_documents": my_docs,
            "pending_review": pending_docs,
            "approved": approved_docs,
            "shared_with_me": shared_docs
        }
    else:
        total_docs = db.query(Document).count()
        pending_docs = db.query(Document).filter(Document.status == "pending").count()
        approved_docs = db.query(Document).filter(Document.status == "approved").count()
        rejected_docs = db.query(Document).filter(Document.status == "rejected").count()
        
        return {
            "total_documents": total_docs,
            "pending_review": pending_docs,
            "approved": approved_docs,
            "rejected": rejected_docs
        }

@router.get("/categories")
def get_document_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        # Get categories for employee's documents and shared documents
        categories = db.query(Document.category).filter(
            or_(
                Document.employee_id == current_user.id,
                and_(Document.status == "approved", Document.category.in_(["HR", "Training", "Company"]))
            )
        ).distinct().all()
    else:
        categories = db.query(Document.category).distinct().all()
    
    category_counts = []
    for cat in categories:
        if current_user.role == "employee":
            count = db.query(Document).filter(
                and_(
                    Document.category == cat[0],
                    or_(
                        Document.employee_id == current_user.id,
                        and_(Document.status == "approved", Document.category.in_(["HR", "Training", "Company"]))
                    )
                )
            ).count()
        else:
            count = db.query(Document).filter(Document.category == cat[0]).count()
        
        category_counts.append({"name": cat[0], "count": count})
    
    # Add "All Documents" category
    total_count = sum(cat["count"] for cat in category_counts)
    category_counts.insert(0, {"name": "All Documents", "count": total_count})
    
    return category_counts

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if document.employee_id != current_user.id:
            # Check if it's a shared document
            if not (document.status == "approved" and document.category in ["HR", "Training", "Company"]):
                raise HTTPException(status_code=403, detail="Not authorized")
    
    return document

@router.post("/", response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Role-based employee_id assignment
    if current_user.role == "employee":
        document.employee_id = current_user.id
    elif current_user.role in ["admin", "hr"] and not document.employee_id:
        document.employee_id = current_user.id
    
    db_document = Document(**document.dict(), uploaded_by=current_user.id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: int,
    document: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Role-based access control
    if current_user.role == "employee" and db_document.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = document.dict(exclude_unset=True)
    
    # Handle status updates with approval tracking
    if "status" in update_data and update_data["status"] in ["approved", "rejected"]:
        if current_user.role not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Not authorized to change status")
        db_document.approved_by = current_user.id
        db_document.approved_at = datetime.now()
    
    for field, value in update_data.items():
        setattr(db_document, field, value)
    
    db.commit()
    db.refresh(db_document)
    return db_document

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if db_document.employee_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Delete file from filesystem if it exists
    if db_document.file_path and os.path.exists(db_document.file_path):
        try:
            os.remove(db_document.file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    db.delete(db_document)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    employee_id: Optional[int] = None,
    document_type: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Role-based employee_id assignment
    if current_user.role == "employee":
        employee_id = current_user.id
    elif not employee_id:
        employee_id = current_user.id
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/documents"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Create document record
    db_document = Document(
        employee_id=employee_id,
        document_type=document_type or "Other",
        category=category or "Personal",
        file_name=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
        description=description,
        uploaded_by=current_user.id,
        status="pending" if current_user.role == "employee" else "approved"
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return {
        "message": "Document uploaded successfully",
        "document_id": db_document.id,
        "document": db_document
    }

@router.put("/{document_id}/approve")
def approve_document(
    document_id: int,
    comments: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = "approved"
    document.approved_by = current_user.id
    document.approved_at = datetime.now()
    if comments:
        document.rejection_reason = comments  # Using this field for admin comments
    
    db.commit()
    return {"message": "Document approved successfully"}

@router.put("/{document_id}/reject")
def reject_document(
    document_id: int,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = "rejected"
    document.approved_by = current_user.id
    document.approved_at = datetime.now()
    if reason:
        document.rejection_reason = reason
    
    db.commit()
    return {"message": "Document rejected successfully"}

@router.get("/download/{document_id}")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Role-based access control
    if current_user.role == "employee":
        if document.employee_id != current_user.id:
            # Check if it's a shared document
            if not (document.status == "approved" and document.category in ["HR", "Training", "Company"]):
                raise HTTPException(status_code=403, detail="Not authorized")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_path": document.file_path,
        "file_name": document.file_name,
        "mime_type": document.mime_type
    }

# Document Types
@router.get("/types/", response_model=List[DocumentTypeResponse])
def get_document_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(DocumentType).filter(DocumentType.is_active == True).all()

@router.post("/types/", response_model=DocumentTypeResponse)
def create_document_type(
    doc_type: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_type = DocumentType(**doc_type)
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

# Document Versions
@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
def get_document_versions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if current_user.role == "employee" and document.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(DocumentVersion).filter(DocumentVersion.document_id == document_id).all()