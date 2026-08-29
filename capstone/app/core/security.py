"""Security utilities for password hashing and JWT token management."""
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
settings = get_settings()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Previously hashed password
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: UUID,
    role: str,
    expires_delta: timedelta | None = None
) -> tuple[str, int]:
    """
    Create a JWT access token.
    
    Args:
        subject: User UUID (sub claim)
        role: User role (student or teacher)
        expires_delta: Optional token expiration delta
        
    Returns:
        Tuple of (token_string, expires_in_seconds)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Use timezone-aware UTC datetime to ensure correct timestamp
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "role": role,
    }
    
    # Use a secret key from settings - must be configured
    if not settings.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY must be set in environment")
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    expires_in = int(expires_delta.total_seconds())
    
    return encoded_jwt, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    if not settings.jwt_secret_key:
        raise ValueError("JWT_SECRET_KEY must be set in environment")
    
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    return payload
