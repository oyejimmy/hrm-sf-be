#!/usr/bin/env python3

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import Asset, AssetRequest, User
from sqlalchemy.orm import Session

def show_asset_management_status():
    """Display comprehensive asset management status"""
    db = SessionLocal()
    
    try:
        print("="*70)
        print("ASSET MANAGEMENT SYSTEM - CURRENT STATUS")
        print("="*70)
        
        # Get all assets
        all_assets = db.query(Asset).all()
        
        # Group by status
        status_groups = {}
        type_groups = {}
        
        for asset in all_assets:
            # Group by status
            status = asset.status
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(asset)
            
            # Group by type
            asset_type = asset.asset_type
            if asset_type not in type_groups:
                type_groups[asset_type] = []
            type_groups[asset_type].append(asset)
        
        # Show assets by status
        print(f"\nASSETS BY STATUS:")
        print("-" * 50)
        for status, assets in status_groups.items():
            print(f"\n{status.upper()} ({len(assets)} assets):")
            for asset in assets:
                assignee_info = ""
                if asset.assigned_to:
                    assignee = db.query(User).filter(User.id == asset.assigned_to).first()
                    assignee_info = f" -> {assignee.email}" if assignee else " -> Unknown"
                
                print(f"  - {asset.name} ({asset.asset_type}){assignee_info}")
                print(f"    Serial: {asset.serial_number} | Condition: {asset.condition}")
                print(f"    Location: {asset.location} | Cost: ${asset.purchase_cost or 0:.2f}")
        
        # Show assets by type
        print(f"\n\nASSETS BY TYPE:")
        print("-" * 50)
        for asset_type, assets in type_groups.items():
            print(f"\n{asset_type.upper()} ({len(assets)} assets):")
            for asset in assets:
                status_color = asset.status
                print(f"  - {asset.name} [{status_color}] - {asset.condition}")
        
        # Show asset requests
        print(f"\n\nASSET REQUESTS:")
        print("-" * 50)
        
        all_requests = db.query(AssetRequest).all()
        if all_requests:
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
                    
                    request_info = f"{request.request_type.title()} {request.asset_type}"
                    if request.asset_id:
                        asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
                        if asset:
                            request_info += f" ({asset.name})"
                    
                    print(f"  - {request_info} by {employee_email}")
                    print(f"    Date: {request.requested_date} | Reason: {request.reason or 'N/A'}")
                    if request.admin_comments:
                        print(f"    Admin Comments: {request.admin_comments}")
        else:
            print("No asset requests found.")
        
        # Summary statistics
        print(f"\n\nSUMMARY STATISTICS:")
        print("-" * 50)
        print(f"Total Assets: {len(all_assets)}")
        print(f"Available Assets: {len(status_groups.get('available', []))}")
        print(f"Assigned Assets: {len(status_groups.get('assigned', []))}")
        print(f"Assets in Maintenance: {len(status_groups.get('maintenance', []))}")
        print(f"Retired Assets: {len(status_groups.get('retired', []))}")
        print(f"Total Asset Requests: {len(all_requests)}")
        
        # Calculate total asset value
        total_value = sum(asset.purchase_cost or 0 for asset in all_assets)
        print(f"Total Asset Value: ${total_value:,.2f}")
        
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"Error displaying asset status: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    show_asset_management_status()