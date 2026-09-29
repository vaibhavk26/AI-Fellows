from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.api.schemas.auth import RegisterRequest
from app.core.config import Settings
from app.services import auth_service

FRONTEND_ROOT = Path(__file__).resolve().parents[2] / "frontend"
if str(FRONTEND_ROOT) not in sys.path:
    sys.path.insert(0, str(FRONTEND_ROOT))

from components.api import teacher_signup_enabled


@pytest.mark.parametrize(
    ("environment", "override", "expected"),
    [
        ("production", None, False),
        ("production", True, True),
        ("production", False, False),
        ("development", None, True),
    ],
)
def test_settings_teacher_signup_policy(environment, override, expected):
    settings = Settings(environment=environment, allow_teacher_signup=override)

    assert settings.teacher_signup_enabled is expected


@pytest.mark.parametrize(
    ("environment", "override", "expected"),
    [
        ("production", None, False),
        ("production", "true", True),
        ("production", "false", False),
        ("development", None, True),
    ],
)
def test_signup_ui_policy_matches_environment(monkeypatch, environment, override, expected):
    monkeypatch.setenv("ENVIRONMENT", environment)
    if override is None:
        monkeypatch.delenv("ALLOW_TEACHER_SIGNUP", raising=False)
    else:
        monkeypatch.setenv("ALLOW_TEACHER_SIGNUP", override)

    assert teacher_signup_enabled() is expected


def test_backend_rejects_teacher_registration_when_switch_is_off(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_settings",
        lambda: SimpleNamespace(teacher_signup_enabled=False),
    )
    database = MagicMock()
    request = RegisterRequest(
        email="teacher@example.com",
        password="StrongPassword123!",
        full_name="Test Teacher",
        role="teacher",
    )

    with pytest.raises(ValueError, match="Teacher registration is currently disabled"):
        auth_service.AuthService.register_user(database, request)

    database.query.assert_not_called()


def test_backend_keeps_student_registration_outside_teacher_switch(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_settings",
        lambda: SimpleNamespace(teacher_signup_enabled=False),
    )
    database = MagicMock()
    database.query.return_value.filter.return_value.first.return_value = None

    def assign_user_fields(user):
        user.id = uuid4()
        user.created_at = datetime.now(timezone.utc)

    database.add.side_effect = assign_user_fields
    request = RegisterRequest(
        email="student@example.com",
        password="StrongPassword123!",
        full_name="Test Student",
        role="student",
        class_level=10,
    )

    auth_service.AuthService.register_user(database, request)

    database.commit.assert_called_once()
