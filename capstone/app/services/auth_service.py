"""Authentication service layer."""
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.auth import AuthTokenResponse, RegisterRequest, UserResponse
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models.user import StudentProfile, TeacherProfile, User


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def register_user(db: Session, request: RegisterRequest) -> UserResponse:
        """
        Register a new user with appropriate profile.
        
        Args:
            db: Database session
            request: Registration request data
            
        Returns:
            UserResponse with created user data
            
        Raises:
            ValueError: If email already exists or registration fails
        """
        # Normalize email to lowercase
        email = request.email.lower()
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError("Email already registered")
        
        # Validate class_level for students
        if request.role == "student" and request.class_level != 10:
            raise ValueError("Only class level 10 is supported in MVP")
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        try:
            user = User(
                email=email,
                password_hash=password_hash,
                full_name=request.full_name,
                role=request.role,
                is_active=True,
            )
            db.add(user)
            db.flush()  # Flush to get the user ID
            
            # Create appropriate profile
            if request.role == "student":
                student_profile = StudentProfile(
                    user_id=user.id,
                    class_level=request.class_level or 10,
                )
                db.add(student_profile)
            elif request.role == "teacher":
                teacher_profile = TeacherProfile(
                    user_id=user.id,
                    department=None,
                )
                db.add(teacher_profile)
            
            db.commit()
            db.refresh(user)
            
            return UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                class_level=request.class_level if request.role == "student" else None,
                created_at=user.created_at,
            )
        except IntegrityError:
            db.rollback()
            raise ValueError("Failed to create user. Email may already be registered.")

    @staticmethod
    def authenticate_user(
        db: Session, email: str, password: str
    ) -> Optional[AuthTokenResponse]:
        """
        Authenticate a user by email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            
        Returns:
            AuthTokenResponse with token and user data, or None if auth fails
        """
        # Normalize email
        email = email.lower()
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        # Generate token
        access_token, expires_in = create_access_token(
            subject=user.id,
            role=user.role,
        )
        
        # Build response
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            class_level=None,
            created_at=user.created_at,
        )
        
        # Add class_level if student
        if user.role == "student":
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == user.id
            ).first()
            if student_profile:
                user_response.class_level = student_profile.class_level
        
        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_response,
        )

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[UserResponse]:
        """
        Get user by ID.
        
        Args:
            db: Database session
            user_id: User UUID
            
        Returns:
            UserResponse or None if user not found
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        class_level = None
        if user.role == "student":
            student_profile = db.query(StudentProfile).filter(
                StudentProfile.user_id == user.id
            ).first()
            if student_profile:
                class_level = student_profile.class_level
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            class_level=class_level,
            created_at=user.created_at,
        )
