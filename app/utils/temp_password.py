import secrets
import string
import bcrypt
from typing import Dict, Optional

def generate_temp_password(
    length: int = 10,
    include_symbols: bool = False,
    hash_rounds: int = 10
) -> Dict[str, str]:
    """
    Generate a secure temporary password and its bcrypt hash.
    
    Args:
        length: Password length (default: 10)
        include_symbols: Include symbols in password (default: False)
        hash_rounds: Bcrypt hash rounds (default: 10)
    
    Returns:
        Dict containing 'temp_password' and 'hashed_password'
    
    Example:
        result = generate_temp_password(length=12, include_symbols=False)
        # Store result['hashed_password'] in database
        # Email result['temp_password'] to user
    """
    if length < 4:
        raise ValueError("Password length must be at least 4 characters")
    
    # Character sets
    alpha = string.ascii_letters + string.digits
    symbols = "!@#$%&*?"
    charset = alpha + symbols if include_symbols else alpha
    
    # Generate secure random password
    temp_password = ''.join(secrets.choice(charset) for _ in range(length))
    
    # Ensure password has at least one digit and one letter (when not using symbols)
    if not include_symbols and length >= 2:
        has_digit = any(c.isdigit() for c in temp_password)
        has_letter = any(c.isalpha() for c in temp_password)
        
        if not has_digit or not has_letter:
            # Regenerate if requirements not met (very unlikely)
            return generate_temp_password(length, include_symbols, hash_rounds)
    
    # Hash the password
    hashed_password = bcrypt.hashpw(
        temp_password.encode('utf-8'), 
        bcrypt.gensalt(rounds=hash_rounds)
    ).decode('utf-8')
    
    return {
        'temp_password': temp_password,
        'hashed_password': hashed_password
    }