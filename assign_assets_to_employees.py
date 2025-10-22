#!/usr/bin/env python3

import sys
import os
from datetime import date

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Asset, User
from sqlalchemy.orm import Session

def assign_assets_to_employees():
    """Assign some assets to employees for demonstration"""
    db = SessionLocal()
    
    try:
        # Get available assets
        available_assets = db.query(Asset).filter(Asset.status == "available").all()
        
        # Get employees (non-admin users)
        employees = db.query(User).filter(User.role.in_(["employee", "hr", "team_lead"])).all()
        
        if not available_assets:
            print("No available assets found.")
            return
            
        if not employees:
            print("No employees found.")
            return
        
        print(f"Found {len(available_assets)} available assets and {len(employees)} employees")
        
        # Assignment logic: assign different types of assets to different employees
        assignments = [
            # Employee 1 gets laptop and monitor
            {"employee_idx": 0, "asset_types": ["Laptop", "Monitor"]},
            # Employee 2 gets phone and headphones  
            {"employee_idx": 1, "asset_types": ["Phone", "Headphones"]},
            # Employee 3 gets tablet and mouse
            {"employee_idx": 2, "asset_types": ["Tablet", "Mouse"]},
        ]
        
        assigned_count = 0
        
        for assignment in assignments:
            if assignment["employee_idx"] >= len(employees):
                continue
                
            employee = employees[assignment["employee_idx"]]
            
            for asset_type in assignment["asset_types"]:
                # Find an available asset of this type
                asset = next((a for a in available_assets if a.asset_type == asset_type and a.status == "available"), None)
                
                if asset:
                    # Assign the asset
                    asset.assigned_to = employee.id
                    asset.assigned_date = date.today()
                    asset.status = "assigned"
                    
                    assigned_count += 1
                    print(f"Assigned {asset.name} ({asset.asset_type}) to {employee.email}")
        
        # Commit all assignments
        db.commit()
        
        print(f"\nSuccessfully assigned {assigned_count} assets to employees!")
        
        # Show current asset status
        print("\nCurrent Asset Status:")
        all_assets = db.query(Asset).all()
        for asset in all_assets:
            if asset.assigned_to:
                assignee = db.query(User).filter(User.id == asset.assigned_to).first()
                assignee_email = assignee.email if assignee else "Unknown"
                print(f"  - {asset.name} ({asset.asset_type}) - {asset.status} to {assignee_email}")
            else:
                print(f"  - {asset.name} ({asset.asset_type}) - {asset.status}")
        
    except Exception as e:
        print(f"Error assigning assets: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Assigning assets to employees...")
    assign_assets_to_employees()