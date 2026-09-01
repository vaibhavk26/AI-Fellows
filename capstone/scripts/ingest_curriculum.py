"""Ingest the configured Physics and Mathematics curriculum PDFs."""

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.rag.pipeline import CurriculumIngestor


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest curriculum PDFs into PostgreSQL and FAISS")
    parser.add_argument("--all", action="store_true", help="ingest data/curriculum/physics.pdf and mathematics.pdf")
    parser.add_argument("--pdf", type=Path, help="path to a single curriculum PDF")
    parser.add_argument("--subject", help="subject name for --pdf")
    arguments = parser.parse_args()
    if arguments.all:
        inputs = [(Path("data/curriculum/physics.pdf"), "Physics"), (Path("data/curriculum/mathematics.pdf"), "Mathematics")]
    elif arguments.pdf and arguments.subject:
        inputs = [(arguments.pdf, arguments.subject)]
    else:
        parser.error("provide --all or both --pdf and --subject")

    database = SessionLocal()
    try:
        ingestor = CurriculumIngestor(database, Path(get_settings().vector_db_path))
        for pdf_path, subject_name in inputs:
            document = ingestor.ingest(pdf_path, subject_name)
            print(f"Ingested {subject_name}: {document.id}")
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()


if __name__ == "__main__":
    main()
