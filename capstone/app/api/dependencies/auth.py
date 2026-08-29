"""Auth dependency for protected endpoints."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.api.dependencies.database import get_db
from app.api.schemas.auth import UserResponse
from app.core.security import decode_access_token
from app.services.auth_service import AuthService
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        UserResponse with current user data
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Token missing 'sub' claim")
        user_id = UUID(user_id_str)
    except (JWTError, ValueError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_student(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get the current authenticated user if they are a student.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        UserResponse for student
        
    Raises:
        HTTPException: 403 if user is not a student
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available to students",
        )
    return current_user


def get_current_teacher(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get the current authenticated user if they are a teacher.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        UserResponse for teacher
        
    Raises:
        HTTPException: 403 if user is not a teacher
    """
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available to teachers",
        )
    return current_user
