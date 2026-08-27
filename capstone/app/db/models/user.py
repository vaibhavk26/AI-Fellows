from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, SmallInteger, String, TIMESTAMP, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(320), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher')", name="ck_users_role"),
        CheckConstraint("length(btrim(full_name)) > 0", name="ck_users_full_name"),
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True
    )
    class_level = Column(SmallInteger, nullable=False, server_default=text("10"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (CheckConstraint("class_level = 10", name="ck_student_profiles_class_level"),)


class TeacherProfile(Base):
    __tablename__ = "teacher_profiles"

    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), primary_key=True
    )
    department = Column(String(150), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
