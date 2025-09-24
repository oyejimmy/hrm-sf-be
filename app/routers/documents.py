from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Document, DocumentVersion, DocumentType, User
from ..schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse, DocumentVersionResponse, DocumentTypeResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    employee_id: Optional[int] = None,
    document_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document)
    if current_user.role == "employee":
        query = query.filter(Document.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(Document.employee_id == employee_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if status:
        query = query.filter(Document.status == status)
    if category:
        query = query.filter(Document.category == category)
    return query.offset(skip).limit(limit).all()

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if current_user.role == "employee" and document.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return document

@router.post("/", response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
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
    
    if current_user.role == "employee" and db_document.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    for field, value in document.dict(exclude_unset=True).items():
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
    
    if current_user.role == "employee" and db_document.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_document)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    employee_id: int = None,
    document_type: str = None,
    category: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "employee":
        employee_id = current_user.id
    
    # Here you would implement file upload logic
    # For now, we'll just create a document record
    db_document = Document(
        employee_id=employee_id,
        document_type=document_type,
        file_name=file.filename,
        file_size=str(file.size) if file.size else "0",
        category=category,
        description=description,
        uploaded_by=current_user.id,
        status="pending"
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return {"message": "Document uploaded successfully", "document_id": db_document.id}

@router.put("/{document_id}/approve")
def approve_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = "approved"
    db.commit()
    return {"message": "Document approved successfully"}

@router.put("/{document_id}/reject")
def reject_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = "rejected"
    db.commit()
    return {"message": "Document rejected successfully"}

# Document Types
@router.get("/types/", response_model=List[DocumentTypeResponse])
def get_document_types(db: Session = Depends(get_db)):
    return db.query(DocumentType).all()

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