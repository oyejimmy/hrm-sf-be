from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db.sqlite import SQLiteService
from app.models.pydantic_models import UserCreate, UserResponse, UserLogin, Token
from app.models.sql_models import UserRole, UserStatus
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_token,
    get_user_id_from_token,
    sanitize_log_input
)
from app.core.logger import logger

router = APIRouter()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = await SQLiteService.get_user_by_id(db, int(user_id))
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {sanitize_log_input(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def require_role(required_role: UserRole):
    """Decorator to require specific role."""
    def role_checker(current_user = Depends(get_current_active_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing_user = await SQLiteService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user data
    user_dict = {
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "role": user_data.role,
        "status": user_data.status or UserStatus.ACTIVE,
        "team_id": user_data.team_id,
        "phone": user_data.phone,
        "profile_picture": user_data.profile_picture,
        "password_hash": get_password_hash(user_data.password)
    }
    
    user = await SQLiteService.create_user(db, user_dict)
    
    logger.info(f"New user registered: {sanitize_log_input(user_data.email)}")
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        status=user.status,
        team_id=user.team_id,
        phone=user.phone,
        profile_picture=user.profile_picture,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=user.last_login
    )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    try:
        # Find user by email
        user = await SQLiteService.get_user_by_email(db, user_credentials.email)
        
        if not user or not verify_password(user_credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Update last login
        await SQLiteService.update_user_last_login(db, user.id)
        
        logger.info(f"User logged in: {sanitize_log_input(user_credentials.email)}")
        
        redirect_url = "/dashboard"
        if user.role == UserRole.ADMIN:
            redirect_url = "/admin/dashboard"
        elif user.role == UserRole.EMPLOYEE:
            redirect_url = "/employee/dashboard"
        elif user.role == UserRole.TEAM_LEAD:
            redirect_url = "/team-lead/dashboard"

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            redirect_url=redirect_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {sanitize_log_input(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(request: dict, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    refresh_token_value = request.get("refresh_token")
    
    try:
        payload = verify_token(refresh_token_value, "refresh")
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user = await SQLiteService.get_user_by_id(db, int(user_id))
        
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        }
        
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {sanitize_log_input(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        status=current_user.status,
        team_id=current_user.team_id,
        phone=current_user.phone,
        profile_picture=current_user.profile_picture,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login
    )

@router.post("/logout")
async def logout(current_user = Depends(get_current_active_user)):
    """Logout user (client should discard tokens)."""
    logger.info(f"User logged out: {sanitize_log_input(current_user.email)}")
    return {"message": "Successfully logged out"}
