"""Integration test: ingest the real curriculum PDFs and validate that subjects, chapters,
topics, and chunks are correctly identified in PostgreSQL and stay consistent with FAISS."""
import json
from pathlib import Path

import faiss
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.db.models.base import Base
from app.rag.pipeline import CurriculumIngestor

settings = get_settings()
engine = create_engine(settings.test_database_url, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

CURRICULUM_DIR = Path(__file__).resolve().parents[2] / "data" / "curriculum"

EXPECTED_CHAPTERS = {
    "Mathematics": {"Real Numbers", "Quadratic Equations", "Introduction To Trigonometry", "Statistics"},
    "Physics": {"Electricity", "Light", "Magnetic Effects of Electric Current"},
}


@pytest.fixture(scope="module", autouse=True)
def database_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def ingested(tmp_path_factory):
    database = TestingSessionLocal()
    database.execute(text("TRUNCATE TABLE subjects CASCADE"))
    database.commit()
    vector_dir = tmp_path_factory.mktemp("vectors")
    ingestor = CurriculumIngestor(database, vector_dir)
    ingestor.ingest(CURRICULUM_DIR / "physics.pdf", "Physics")
    ingestor.ingest(CURRICULUM_DIR / "mathematics.pdf", "Mathematics")
    yield database, vector_dir
    database.execute(text("TRUNCATE TABLE subjects CASCADE"))
    database.commit()
    database.close()


def test_subjects_are_class_10_physics_and_mathematics(ingested):
    database, _ = ingested
    rows = database.execute(text("SELECT name, class_level FROM subjects"))
    assert {(name, level) for name, level in rows} == {("Physics", 10), ("Mathematics", 10)}


def test_chapters_match_expected_curriculum(ingested):
    database, _ = ingested
    for subject_name, expected in EXPECTED_CHAPTERS.items():
        rows = database.execute(
            text("SELECT c.name FROM chapters c JOIN subjects s ON s.id = c.subject_id WHERE s.name = :name"),
            {"name": subject_name},
        )
        assert {row[0] for row in rows} == expected


def test_every_chapter_has_at_least_one_topic(ingested):
    database, _ = ingested
    rows = database.execute(text(
        "SELECT c.name, count(t.id) FROM chapters c LEFT JOIN topics t ON t.chapter_id = c.id GROUP BY c.name"
    ))
    topic_counts = dict(rows.all())
    assert all(count > 0 for count in topic_counts.values()), topic_counts


def test_faiss_and_postgres_chunk_counts_match(ingested):
    database, vector_dir = ingested
    metadata = json.loads((vector_dir / "curriculum.metadata.json").read_text(encoding="utf-8"))
    index = faiss.read_index(str(vector_dir / "curriculum.faiss"))
    source_reference_count = database.execute(text("SELECT count(*) FROM source_references")).scalar()

    assert index.ntotal == len(metadata) == source_reference_count > 0


def test_faiss_metadata_has_no_orphan_references(ingested):
    database, vector_dir = ingested
    metadata = json.loads((vector_dir / "curriculum.metadata.json").read_text(encoding="utf-8"))
    source_reference_ids = {str(row[0]) for row in database.execute(text("SELECT id FROM source_references"))}
    subject_ids = {str(row[0]) for row in database.execute(text("SELECT id FROM subjects"))}
    chapter_ids = {str(row[0]) for row in database.execute(text("SELECT id FROM chapters"))}
    topic_ids = {str(row[0]) for row in database.execute(text("SELECT id FROM topics"))}

    assert all(entry["source_reference_id"] in source_reference_ids for entry in metadata)
    assert all(entry["subject_id"] in subject_ids for entry in metadata)
    assert all(entry["chapter_id"] in chapter_ids for entry in metadata if entry["chapter_id"])
    assert all(entry["topic_id"] in topic_ids for entry in metadata if entry["topic_id"])
    # a topic can never be set without its parent chapter also being set on the same chunk
    assert all(entry["chapter_id"] for entry in metadata if entry["topic_id"])


def test_faiss_search_returns_relevant_subject_content(ingested):
    from app.rag.pipeline import FaissStore

    database, vector_dir = ingested
    store = FaissStore(vector_dir)
    physics_id = database.execute(text("SELECT id FROM subjects WHERE name = 'Physics'")).scalar()

    results = store.search("resistors connected in parallel", limit=3, subject_id=physics_id)

    assert results
    assert all(result.subject_id == physics_id for result in results)
