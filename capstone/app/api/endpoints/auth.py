"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.api.dependencies.database import get_db
from app.api.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    """
    Register a new user.
    
    - **email**: User email (must be unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name
    - **role**: User role (student or teacher)
    - **class_level**: Class level (10 for students, optional for others)
    
    Returns: Created user data (201 Created)
    """
    try:
        return AuthService.register_user(db, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=dict)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """
    Authenticate a user and return access token.
    
    - **email**: User email
    - **password**: User password
    
    Returns: Access token, token type, expiration, and user data (200 OK)
    """
    auth_response = AuthService.authenticate_user(db, request.email, request.password)
    
    if not auth_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "data": auth_response,
        "meta": None,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(current_user: UserResponse = Depends(get_current_user)) -> None:
    """
    Logout the current user.
    
    The MVP does not maintain a token blacklist; logout is client-side.
    
    Returns: 204 No Content
    """
    return None


@router.get("/me", response_model=dict)
def get_current_user_endpoint(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """
    Get the authenticated user's information.
    
    Returns: Current user data (200 OK)
    """
    return {
        "data": current_user,
        "meta": None,
    }
