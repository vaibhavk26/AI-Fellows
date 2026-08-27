from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    TIMESTAMP,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.db.models.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(String(100), nullable=False)
    class_level = Column(SmallInteger, nullable=False, server_default=text("10"))
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("name", "class_level", name="uq_subjects_name_class"),
        CheckConstraint("class_level = 10", name="ck_subjects_class_level"),
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("subjects.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    name = Column(String(150), nullable=False)
    display_order = Column(SmallInteger, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("subject_id", "name", name="uq_chapters_subject_name"),
        UniqueConstraint("subject_id", "display_order", name="uq_chapters_subject_order"),
        CheckConstraint("display_order > 0", name="ck_chapters_display_order"),
    )


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    chapter_id = Column(
        UUID(as_uuid=True), ForeignKey("chapters.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    name = Column(String(150), nullable=False)
    display_order = Column(SmallInteger, nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("chapter_id", "name", name="uq_topics_chapter_name"),
        UniqueConstraint("chapter_id", "display_order", name="uq_topics_chapter_order"),
        CheckConstraint("display_order > 0", name="ck_topics_display_order"),
    )


class CurriculumDocument(Base):
    __tablename__ = "curriculum_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    subject_id = Column(
        UUID(as_uuid=True), ForeignKey("subjects.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
    )
    chapter_id = Column(
        UUID(as_uuid=True), ForeignKey("chapters.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True
    )
    title = Column(String(300), nullable=False)
    source_uri = Column(String(2048), nullable=False)
    content_hash = Column(String(64), nullable=False)
    document_type = Column(String(30), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("source_uri", name="uq_curriculum_documents_source_uri"),
        UniqueConstraint("content_hash", name="uq_curriculum_documents_content_hash"),
        CheckConstraint(
            "document_type IN ('syllabus', 'reference', 'sample_paper')", name="ck_curriculum_documents_type"
        ),
        CheckConstraint("content_hash ~ '^[0-9a-fA-F]{64}$'", name="ck_curriculum_documents_hash"),
    )


class SourceReference(Base):
    __tablename__ = "source_references"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_documents.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    page_number = Column(Integer, nullable=True)
    chunk_id = Column(String(200), nullable=True)
    excerpt = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("document_id", "page_number", "chunk_id", name="uq_source_references_location"),
        CheckConstraint("page_number IS NULL OR page_number > 0", name="ck_source_references_page"),
        CheckConstraint("page_number IS NOT NULL OR chunk_id IS NOT NULL", name="ck_source_references_locator"),
    )
