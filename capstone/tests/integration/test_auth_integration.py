"""Integration tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.database import get_db
from app.core.config import get_settings
from app.db.models.base import Base
from app.main import app

# Use test database
settings = get_settings()
engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Set up test database tables."""
    # Create all tables before tests
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)


class TestAuthEndpoints:
    """Test suite for authentication endpoints."""

    def test_register_student(self):
        """Test student registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "student@example.com",
                "password": "StrongPassword123!",
                "full_name": "Asha Sharma",
                "role": "student",
                "class_level": 10,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "student@example.com"
        assert data["full_name"] == "Asha Sharma"
        assert data["role"] == "student"
        assert data["class_level"] == 10
        assert "id" in data
        assert "created_at" in data
        assert "password_hash" not in data

    def test_register_teacher(self):
        """Test teacher registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "teacher@example.com",
                "password": "TeacherPassword123!",
                "full_name": "John Doe",
                "role": "teacher",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "teacher@example.com"
        assert data["role"] == "teacher"
        assert data["class_level"] is None

    def test_register_duplicate_email(self):
        """Test that duplicate email registration fails."""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "unique@example.com",
                "password": "Password123!",
                "full_name": "First User",
                "role": "student",
            },
        )
        
        # Try to register with same email
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "unique@example.com",
                "password": "Password456!",
                "full_name": "Second User",
                "role": "student",
            },
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_class_level(self):
        """Test that invalid class level for student fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid_class@example.com",
                "password": "Password123!",
                "full_name": "Student",
                "role": "student",
                "class_level": 11,  # Invalid class level
            },
        )
        
        assert response.status_code == 400
        assert "class level 10" in response.json()["detail"]

    def test_login_success(self):
        """Test successful login."""
        # Register a user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "Password123!",
                "full_name": "Login User",
                "role": "student",
            },
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "Password123!",
            },
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert data["user"]["email"] == "login@example.com"
        assert data["user"]["role"] == "student"

    def test_login_invalid_email(self):
        """Test login with non-existent email."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123!",
            },
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_invalid_password(self):
        """Test login with incorrect password."""
        # Register a user
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login2@example.com",
                "password": "CorrectPassword123!",
                "full_name": "Login User",
                "role": "student",
            },
        )
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login2@example.com",
                "password": "WrongPassword123!",
            },
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_get_current_user(self):
        """Test getting current user information."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "Password123!",
                "full_name": "Test User",
                "role": "student",
            },
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "Password123!",
            },
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == "user@example.com"
        assert data["full_name"] == "Test User"
        assert data["role"] == "student"

    def test_get_current_user_invalid_token(self):
        """Test that invalid token returns 401."""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_logout(self):
        """Test logout endpoint."""
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "Password123!",
                "full_name": "Logout User",
                "role": "student",
            },
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "logout@example.com",
                "password": "Password123!",
            },
        )
        
        token = login_response.json()["data"]["access_token"]
        
        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 204
