from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import os

from app.models.user import UserRole
from app.routers.auth import get_current_active_user, require_role
from app.db import get_database
from app.core.config import settings
from app.core.logger import logger

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "general",
    current_user: dict = Depends(get_current_active_user)
):
    """Upload a document."""
    db = get_database()
    
    # Validate file size
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    filename = f"{datetime.utcnow().timestamp()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Create document record
    document_doc = {
        "user_id": str(current_user["_id"]),
        "filename": file.filename,
        "file_path": file_path,
        "file_size": file.size,
        "content_type": file.content_type,
        "document_type": document_type,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.documents.insert_one(document_doc)
    document_doc["_id"] = str(result.inserted_id)
    
    logger.info(f"Document uploaded: {file.filename}")
    
    return document_doc

@router.get("/my-documents")
async def get_my_documents(
    current_user: dict = Depends(get_current_active_user)
):
    """Get current user's documents."""
    db = get_database()
    
    cursor = db.documents.find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    documents = await cursor.to_list(length=None)
    
    return documents

@router.get("/all-documents")
async def get_all_documents(
    current_user: dict = Depends(require_role(UserRole.HR))
):
    """Get all documents (HR only)."""
    db = get_database()
    
    cursor = db.documents.find().sort("created_at", -1)
    documents = await cursor.to_list(length=None)
    
    return documents

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete a document."""
    db = get_database()
    
    document = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check permissions
    if (current_user["role"] == UserRole.EMPLOYEE and 
        document["user_id"] != str(current_user["_id"])):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete file from filesystem
    try:
        os.remove(document["file_path"])
    except FileNotFoundError:
        pass
    
    # Delete document record
    await db.documents.delete_one({"_id": ObjectId(document_id)})
    
    logger.info(f"Document deleted: {document_id}")
    
    return {"message": "Document deleted successfully"}
