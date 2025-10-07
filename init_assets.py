#!/usr/bin/env python3

import sys
import os
from datetime import date, datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Asset, AssetRequest, User
from sqlalchemy.orm import Session

def init_sample_assets():
    """Initialize sample asset data for testing"""
    db = SessionLocal()
    
    try:
        # Check if assets already exist
        existing_assets = db.query(Asset).count()
        if existing_assets > 0:
            print(f"Assets already exist ({existing_assets} found). Skipping initialization.")
            return
        
        # Sample assets data
        sample_assets = [
            {
                "name": "MacBook Pro 16\"",
                "asset_type": "Laptop",
                "serial_number": "SN-MBP-2023-001",
                "specifications": "M2 Pro, 32GB RAM, 1TB SSD",
                "purchase_date": date(2023, 4, 10),
                "purchase_cost": 2999.00,
                "warranty_expiry": date(2026, 4, 10),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Dell UltraSharp 27\"",
                "asset_type": "Monitor",
                "serial_number": "SN-DELL-2023-045",
                "specifications": "4K UHD, IPS Panel",
                "purchase_date": date(2023, 5, 15),
                "purchase_cost": 599.00,
                "warranty_expiry": date(2026, 5, 15),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "iPhone 14 Pro",
                "asset_type": "Phone",
                "serial_number": "SN-APPLE-2023-078",
                "specifications": "128GB, Deep Purple",
                "purchase_date": date(2023, 6, 1),
                "purchase_cost": 999.00,
                "warranty_expiry": date(2024, 6, 1),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Sony WH-1000XM5",
                "asset_type": "Headphones",
                "serial_number": "SN-SONY-2023-112",
                "specifications": "Noise Cancelling, Black",
                "purchase_date": date(2023, 6, 15),
                "purchase_cost": 399.00,
                "warranty_expiry": date(2025, 6, 15),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "HP LaserJet Pro MFP 4301fdw",
                "asset_type": "Printer",
                "serial_number": "SN-HP-2022-987",
                "specifications": "Multifunction Printer with WiFi",
                "purchase_date": date(2022, 12, 1),
                "purchase_cost": 299.00,
                "warranty_expiry": date(2024, 12, 1),
                "status": "maintenance",
                "condition": "good",
                "location": "Office Floor 2"
            },
            {
                "name": "Lenovo ThinkPad X1 Carbon",
                "asset_type": "Laptop",
                "serial_number": "SN-LENOVO-2023-203",
                "specifications": "i7-1260P, 16GB RAM, 512GB SSD",
                "purchase_date": date(2023, 7, 1),
                "purchase_cost": 1899.00,
                "warranty_expiry": date(2026, 7, 1),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Samsung 32\" Curved Monitor",
                "asset_type": "Monitor",
                "serial_number": "SN-SAMSUNG-2023-156",
                "specifications": "32\" WQHD Curved Display",
                "purchase_date": date(2023, 8, 1),
                "purchase_cost": 449.00,
                "warranty_expiry": date(2026, 8, 1),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "iPad Pro 12.9\"",
                "asset_type": "Tablet",
                "serial_number": "SN-IPAD-2023-089",
                "specifications": "M2 Chip, 256GB, Space Gray",
                "purchase_date": date(2023, 8, 15),
                "purchase_cost": 1099.00,
                "warranty_expiry": date(2024, 8, 15),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Logitech MX Master 3S",
                "asset_type": "Mouse",
                "serial_number": "SN-LOGI-2023-234",
                "specifications": "Wireless Mouse with USB-C",
                "purchase_date": date(2023, 9, 1),
                "purchase_cost": 99.00,
                "warranty_expiry": date(2025, 9, 1),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            },
            {
                "name": "Microsoft Surface Laptop 5",
                "asset_type": "Laptop",
                "serial_number": "SN-MS-2023-445",
                "specifications": "i5-1235U, 8GB RAM, 256GB SSD",
                "purchase_date": date(2023, 9, 15),
                "purchase_cost": 1299.00,
                "warranty_expiry": date(2025, 9, 15),
                "status": "available",
                "condition": "excellent",
                "location": "IT Storage"
            }
        ]
        
        # Create asset records
        created_assets = []
        for asset_data in sample_assets:
            asset = Asset(**asset_data)
            db.add(asset)
            created_assets.append(asset)
        
        db.commit()
        
        # Refresh to get IDs
        for asset in created_assets:
            db.refresh(asset)
        
        print(f"Successfully created {len(created_assets)} sample assets:")
        for asset in created_assets:
            print(f"  - {asset.name} ({asset.asset_type}) - {asset.status}")
        
        # Create some sample asset requests
        # First, get a sample employee user
        employee_user = db.query(User).filter(User.role == "employee").first()
        
        if employee_user:
            sample_requests = [
                {
                    "employee_id": employee_user.id,
                    "asset_type": "Laptop",
                    "request_type": "request",
                    "reason": "Need a laptop for development work",
                    "requested_date": date.today(),
                    "status": "pending"
                },
                {
                    "employee_id": employee_user.id,
                    "asset_type": "Monitor",
                    "request_type": "request",
                    "reason": "Need an additional monitor for productivity",
                    "requested_date": date.today(),
                    "status": "pending"
                }
            ]
            
            created_requests = []
            for request_data in sample_requests:
                request = AssetRequest(**request_data)
                db.add(request)
                created_requests.append(request)
            
            db.commit()
            
            print(f"\\nSuccessfully created {len(created_requests)} sample asset requests:")
            for request in created_requests:
                print(f"  - {request.asset_type} request by employee ID {request.employee_id}")
        
        print("\\nAsset initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing assets: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing sample asset data...")
    init_sample_assets()