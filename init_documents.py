#!/usr/bin/env python3

import sys
import os
from datetime import date, datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Document, DocumentType, User
from sqlalchemy.orm import Session

def init_sample_documents():
    """Initialize sample document data for testing"""
    db = SessionLocal()
    
    try:
        # Check if documents already exist
        existing_docs = db.query(Document).count()
        if existing_docs > 0:
            print(f"Documents already exist ({existing_docs} found). Skipping initialization.")
            return
        
        # Get sample users
        admin_user = db.query(User).filter(User.role == "admin").first()
        hr_user = db.query(User).filter(User.role == "hr").first()
        employee_user = db.query(User).filter(User.role == "employee").first()
        
        if not admin_user or not hr_user or not employee_user:
            print("Required users not found. Please run init_db.py first.")
            return
        
        # Create document types first
        document_types = [
            {
                "name": "Employment Contract",
                "category": "Employment",
                "is_required": True,
                "description": "Employee employment contract",
                "allowed_formats": ["pdf", "doc", "docx"],
                "max_file_size": 10
            },
            {
                "name": "ID Document",
                "category": "Personal",
                "is_required": True,
                "description": "Government issued ID document",
                "allowed_formats": ["pdf", "jpg", "png"],
                "max_file_size": 5
            },
            {
                "name": "Training Certificate",
                "category": "Training",
                "is_required": False,
                "description": "Professional training certificates",
                "allowed_formats": ["pdf", "jpg", "png"],
                "max_file_size": 5
            },
            {
                "name": "Expense Report",
                "category": "Finance",
                "is_required": False,
                "description": "Monthly expense reports",
                "allowed_formats": ["pdf", "xlsx", "csv"],
                "max_file_size": 10
            },
            {
                "name": "Company Policy",
                "category": "HR",
                "is_required": False,
                "description": "Company policies and procedures",
                "allowed_formats": ["pdf", "doc", "docx"],
                "max_file_size": 20
            }
        ]
        
        created_types = []
        for doc_type_data in document_types:
            doc_type = DocumentType(**doc_type_data)
            db.add(doc_type)
            created_types.append(doc_type)
        
        db.commit()
        print(f"Created {len(created_types)} document types")
        
        # Sample documents data
        sample_documents = [
            {
                "employee_id": employee_user.id,
                "document_type": "Employment Contract",
                "category": "Employment",
                "file_name": "employment_contract.pdf",
                "file_path": "uploads/documents/employment_contract.pdf",
                "file_size": 2457600,  # 2.4 MB
                "mime_type": "application/pdf",
                "status": "approved",
                "description": "Employee employment contract",
                "is_required": True,
                "uploaded_by": hr_user.id,
                "approved_by": admin_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "ID Document",
                "category": "Personal",
                "file_name": "id_document.jpg",
                "file_path": "uploads/documents/id_document.jpg",
                "file_size": 1258291,  # 1.2 MB
                "mime_type": "image/jpeg",
                "status": "approved",
                "description": "Government issued ID document",
                "is_required": True,
                "uploaded_by": employee_user.id,
                "approved_by": hr_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Training Certificate",
                "category": "Training",
                "file_name": "training_certificate.pdf",
                "file_path": "uploads/documents/training_certificate.pdf",
                "file_size": 838860,  # 0.8 MB
                "mime_type": "application/pdf",
                "status": "approved",
                "description": "Professional development certificate",
                "is_required": False,
                "uploaded_by": employee_user.id,
                "approved_by": hr_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Expense Report",
                "category": "Finance",
                "file_name": "expense_report_nov.xlsx",
                "file_path": "uploads/documents/expense_report_nov.xlsx",
                "file_size": 524288,  # 0.5 MB
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "status": "pending",
                "description": "November expense report",
                "is_required": False,
                "uploaded_by": employee_user.id
            },
            {
                "employee_id": hr_user.id,
                "document_type": "Company Policy",
                "category": "HR",
                "file_name": "company_policy_2024.pdf",
                "file_path": "uploads/documents/company_policy_2024.pdf",
                "file_size": 5971968,  # 5.7 MB
                "mime_type": "application/pdf",
                "status": "approved",
                "description": "Updated company policies for 2024",
                "is_required": False,
                "uploaded_by": hr_user.id,
                "approved_by": admin_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Performance Review",
                "category": "HR",
                "file_name": "performance_review_q3.docx",
                "file_path": "uploads/documents/performance_review_q3.docx",
                "file_size": 314572,  # 0.3 MB
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "status": "rejected",
                "description": "Q3 performance review",
                "is_required": False,
                "uploaded_by": employee_user.id,
                "approved_by": hr_user.id,
                "approved_at": datetime.now(),
                "rejection_reason": "Please use the updated performance review template"
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Tax Documents",
                "category": "Finance",
                "file_name": "tax_documents_2023.pdf",
                "file_path": "uploads/documents/tax_documents_2023.pdf",
                "file_size": 1887436,  # 1.8 MB
                "mime_type": "application/pdf",
                "status": "approved",
                "description": "2023 tax documentation",
                "is_required": True,
                "uploaded_by": employee_user.id,
                "approved_by": admin_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Safety Training",
                "category": "Training",
                "file_name": "safety_training_cert.pdf",
                "file_path": "uploads/documents/safety_training_cert.pdf",
                "file_size": 2202009,  # 2.1 MB
                "mime_type": "application/pdf",
                "status": "approved",
                "description": "Workplace safety training certificate",
                "is_required": True,
                "uploaded_by": employee_user.id,
                "approved_by": hr_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Passport Copy",
                "category": "Personal",
                "file_name": "passport_copy.jpg",
                "file_path": "uploads/documents/passport_copy.jpg",
                "file_size": 943718,  # 0.9 MB
                "mime_type": "image/jpeg",
                "status": "approved",
                "description": "Passport identification copy",
                "is_required": True,
                "uploaded_by": employee_user.id,
                "approved_by": hr_user.id,
                "approved_at": datetime.now()
            },
            {
                "employee_id": employee_user.id,
                "document_type": "Project Report",
                "category": "Employment",
                "file_name": "project_report_q4.docx",
                "file_path": "uploads/documents/project_report_q4.docx",
                "file_size": 1572864,  # 1.5 MB
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "status": "pending",
                "description": "Q4 project completion report",
                "is_required": False,
                "uploaded_by": employee_user.id
            }
        ]
        
        # Create document records
        created_documents = []
        for doc_data in sample_documents:
            document = Document(**doc_data)
            db.add(document)
            created_documents.append(document)
        
        db.commit()
        
        # Refresh to get IDs
        for document in created_documents:
            db.refresh(document)
        
        print(f"Successfully created {len(created_documents)} sample documents:")
        for document in created_documents:
            print(f"  - {document.file_name} ({document.category}) - {document.status}")
        
        print("\\nDocument initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing documents: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing sample document data...")
    init_sample_documents()