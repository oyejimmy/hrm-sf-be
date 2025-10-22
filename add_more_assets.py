#!/usr/bin/env python3

import sys
import os
from datetime import date, timedelta

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Asset, AssetRequest, User
from sqlalchemy.orm import Session

def add_comprehensive_asset_data():
    """Add comprehensive asset data with various statuses and types"""
    db = SessionLocal()
    
    try:
        # Additional assets with different statuses
        additional_assets = [
            # Office Equipment
            {
                "name": "Herman Miller Aeron Chair",
                "asset_type": "Furniture",
                "serial_number": "SN-HM-2023-001",
                "specifications": "Size B, Graphite Frame, Mineral Finish",
                "purchase_date": date(2023, 3, 15),
                "purchase_cost": 1395.00,
                "warranty_expiry": date(2035, 3, 15),
                "status": "assigned",
                "condition": "excellent",
                "location": "Office Desk 12"
            },
            {
                "name": "Standing Desk Converter",
                "asset_type": "Furniture",
                "serial_number": "SN-DESK-2023-002",
                "specifications": "Height Adjustable, 32\" Width",
                "purchase_date": date(2023, 4, 1),
                "purchase_cost": 299.00,
                "warranty_expiry": date(2025, 4, 1),
                "status": "available",
                "condition": "excellent",
                "location": "Storage Room A"
            },
            
            # Network Equipment
            {
                "name": "Cisco Catalyst 2960-X Switch",
                "asset_type": "Network Equipment",
                "serial_number": "SN-CISCO-2022-789",
                "specifications": "24-Port Gigabit Switch",
                "purchase_date": date(2022, 11, 10),
                "purchase_cost": 899.00,
                "warranty_expiry": date(2025, 11, 10),
                "status": "assigned",
                "condition": "good",
                "location": "Server Room"
            },
            {
                "name": "Ubiquiti UniFi Access Point",
                "asset_type": "Network Equipment", 
                "serial_number": "SN-UBNT-2023-456",
                "specifications": "WiFi 6, Indoor Access Point",
                "purchase_date": date(2023, 2, 20),
                "purchase_cost": 179.00,
                "warranty_expiry": date(2025, 2, 20),
                "status": "assigned",
                "condition": "excellent",
                "location": "Office Ceiling Zone 2"
            },
            
            # Software Licenses
            {
                "name": "Microsoft Office 365 Business Premium",
                "asset_type": "Software License",
                "serial_number": "LIC-MS365-2023-001",
                "specifications": "Annual Subscription, 5 Users",
                "purchase_date": date(2023, 1, 1),
                "purchase_cost": 1320.00,
                "warranty_expiry": date(2024, 1, 1),
                "status": "assigned",
                "condition": "excellent",
                "location": "Digital License"
            },
            {
                "name": "Adobe Creative Cloud Team",
                "asset_type": "Software License",
                "serial_number": "LIC-ADOBE-2023-002",
                "specifications": "Annual Subscription, 3 Users",
                "purchase_date": date(2023, 3, 1),
                "purchase_cost": 1797.00,
                "warranty_expiry": date(2024, 3, 1),
                "status": "assigned",
                "condition": "excellent",
                "location": "Digital License"
            },
            
            # Retired/Damaged Assets
            {
                "name": "Old Dell OptiPlex 7010",
                "asset_type": "Desktop",
                "serial_number": "SN-DELL-2019-999",
                "specifications": "i5-3470, 8GB RAM, 500GB HDD",
                "purchase_date": date(2019, 6, 15),
                "purchase_cost": 699.00,
                "warranty_expiry": date(2022, 6, 15),
                "status": "retired",
                "condition": "poor",
                "location": "Storage - Disposal"
            },
            {
                "name": "Damaged MacBook Air",
                "asset_type": "Laptop",
                "serial_number": "SN-MBA-2021-555",
                "specifications": "M1, 8GB RAM, 256GB SSD - Screen Cracked",
                "purchase_date": date(2021, 8, 10),
                "purchase_cost": 999.00,
                "warranty_expiry": date(2022, 8, 10),
                "status": "maintenance",
                "condition": "poor",
                "location": "IT Repair Queue"
            },
            
            # Mobile Devices
            {
                "name": "Samsung Galaxy Tab S8",
                "asset_type": "Tablet",
                "serial_number": "SN-SAMSUNG-2023-777",
                "specifications": "11\", 128GB, WiFi + 5G",
                "purchase_date": date(2023, 5, 20),
                "purchase_cost": 729.00,
                "warranty_expiry": date(2024, 5, 20),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Google Pixel 7 Pro",
                "asset_type": "Phone",
                "serial_number": "SN-GOOGLE-2023-888",
                "specifications": "256GB, Obsidian",
                "purchase_date": date(2023, 7, 1),
                "purchase_cost": 899.00,
                "warranty_expiry": date(2024, 7, 1),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            }
        ]
        
        # Check for existing assets and create only new ones
        created_assets = []
        for asset_data in additional_assets:
            existing_asset = db.query(Asset).filter(Asset.serial_number == asset_data["serial_number"]).first()
            if not existing_asset:
                asset = Asset(**asset_data)
                db.add(asset)
                created_assets.append(asset)
            else:
                print(f"Asset with serial number {asset_data['serial_number']} already exists, skipping...")
        
        db.commit()
        
        # Refresh to get IDs
        for asset in created_assets:
            db.refresh(asset)
        
        if created_assets:
            print(f"Successfully created {len(created_assets)} additional assets:")
        else:
            print("No new assets were created (all already exist).")
            for asset in created_assets:
                print(f"  - {asset.name} ({asset.asset_type}) - {asset.status}")
        
        # Create additional asset requests with different statuses
        employees = db.query(User).filter(User.role.in_(["employee", "hr", "team_lead"])).all()
        admin_user = db.query(User).filter(User.role == "admin").first()
        
        if employees and admin_user:
            additional_requests = [
                {
                    "employee_id": employees[0].id,
                    "asset_type": "Desktop",
                    "request_type": "request",
                    "reason": "Need a desktop computer for CAD work",
                    "requested_date": date.today() - timedelta(days=5),
                    "status": "approved",
                    "approved_by": admin_user.id,
                    "approved_at": date.today() - timedelta(days=3)
                },
                {
                    "employee_id": employees[1].id,
                    "asset_type": "Software License",
                    "request_type": "request", 
                    "reason": "Need Photoshop license for marketing materials",
                    "requested_date": date.today() - timedelta(days=2),
                    "status": "rejected",
                    "approved_by": admin_user.id,
                    "approved_at": date.today() - timedelta(days=1),
                    "admin_comments": "Budget constraints - please use free alternatives"
                },
                {
                    "employee_id": employees[2].id,
                    "asset_id": created_assets[8].id,  # Samsung Galaxy Tab
                    "asset_type": "Tablet",
                    "request_type": "return",
                    "reason": "Project completed, returning tablet",
                    "requested_date": date.today(),
                    "status": "pending"
                }
            ]
            
            created_requests = []
            for request_data in additional_requests:
                request = AssetRequest(**request_data)
                db.add(request)
                created_requests.append(request)
            
            db.commit()
            
            print(f"\nSuccessfully created {len(created_requests)} additional asset requests:")
            for request in created_requests:
                print(f"  - {request.request_type.title()} {request.asset_type} - {request.status}")
        
        # Show comprehensive asset summary
        print("\n" + "="*60)
        print("COMPREHENSIVE ASSET SUMMARY")
        print("="*60)
        
        all_assets = db.query(Asset).all()
        
        # Group by status
        status_groups = {}
        for asset in all_assets:
            status = asset.status
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(asset)
        
        for status, assets in status_groups.items():
            print(f"\n{status.upper()} ASSETS ({len(assets)}):")
            for asset in assets:
                assignee_info = ""
                if asset.assigned_to:
                    assignee = db.query(User).filter(User.id == asset.assigned_to).first()
                    assignee_info = f" -> {assignee.email}" if assignee else " -> Unknown"
                
                print(f"  - {asset.name} ({asset.asset_type}){assignee_info}")
                print(f"    Serial: {asset.serial_number} | Condition: {asset.condition} | Location: {asset.location}")
        
        # Show asset requests summary
        print(f"\n" + "="*60)
        print("ASSET REQUESTS SUMMARY")
        print("="*60)
        
        all_requests = db.query(AssetRequest).all()
        request_status_groups = {}
        
        for request in all_requests:
            status = request.status
            if status not in request_status_groups:
                request_status_groups[status] = []
            request_status_groups[status].append(request)
        
        for status, requests in request_status_groups.items():
            print(f"\n{status.upper()} REQUESTS ({len(requests)}):")
            for request in requests:
                employee = db.query(User).filter(User.id == request.employee_id).first()
                employee_email = employee.email if employee else "Unknown"
                print(f"  - {request.request_type.title()} {request.asset_type} by {employee_email}")
                if request.reason:
                    print(f"    Reason: {request.reason}")
                if request.admin_comments:
                    print(f"    Admin Comments: {request.admin_comments}")
        
        print(f"\n" + "="*60)
        print("Asset Management System populated successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"Error adding comprehensive asset data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Adding comprehensive asset management data...")
    add_comprehensive_asset_data()