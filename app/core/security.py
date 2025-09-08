from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import re
import html

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
    """Verify and decode token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token."""
    try:
        payload = verify_token(token)
        return payload.get("sub")
    except:
        return None

def sanitize_input(input_string: str) -> str:
    """Sanitize input to prevent injection attacks."""
    if not isinstance(input_string, str):
        return str(input_string)
    
    # HTML escape
    sanitized = html.escape(input_string)
    
    # Remove potential script tags and other dangerous content
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()

def sanitize_log_input(input_string: str) -> str:
    """Sanitize input for logging to prevent log injection."""
    if not isinstance(input_string, str):
        input_string = str(input_string)
    
    # Remove newlines and carriage returns to prevent log injection
    sanitized = input_string.replace('\n', '\\n').replace('\r', '\\r')
    sanitized = sanitized.replace('\t', '\\t')
    
    # Limit length to prevent log flooding
    if len(sanitized) > 200:
        sanitized = sanitized[:200] + "..."
    
    return sanitized

def validate_object_id(object_id: str) -> bool:
    """Validate MongoDB ObjectId format."""
    if not isinstance(object_id, str):
        return False
    
    # ObjectId should be 24 characters long and contain only hexadecimal characters
    return bool(re.match(r'^[0-9a-fA-F]{24}$', object_id))