"""Idempotent sample curriculum data for local development and tests.

These rows are not authoritative and must not be used to classify production
curriculum. Section 10.3 ingestion discovers the operational hierarchy from
the supplied subject PDFs (see docs/capstone-development-runbook.md section 9.2).
"""

from app.db.models.curriculum import Chapter, Subject
from app.db.session import SessionLocal

SUBJECTS = ["Physics", "Mathematics"]

CHAPTERS = {
    "Physics": [
        "Electricity",
        "Light",
        "Magnetic Effects of Electric Current",
    ],
    "Mathematics": [
        "Real Numbers",
        "Quadratic Equations",
        "Trigonometry",
        "Statistics",
    ],
}

CLASS_LEVEL = 10


def seed_reference_data() -> None:
    session = SessionLocal()
    try:
        for subject_name in SUBJECTS:
            subject = (
                session.query(Subject)
                .filter_by(name=subject_name, class_level=CLASS_LEVEL)
                .one_or_none()
            )
            if subject is None:
                subject = Subject(name=subject_name, class_level=CLASS_LEVEL)
                session.add(subject)
                session.flush()
                print(f"Created subject: {subject_name}")
            else:
                print(f"Subject already exists, skipping: {subject_name}")

            for order, chapter_name in enumerate(CHAPTERS[subject_name], start=1):
                chapter = (
                    session.query(Chapter)
                    .filter_by(subject_id=subject.id, name=chapter_name)
                    .one_or_none()
                )
                if chapter is None:
                    session.add(
                        Chapter(subject_id=subject.id, name=chapter_name, display_order=order)
                    )
                    print(f"Created chapter: {subject_name} / {chapter_name}")
                else:
                    print(f"Chapter already exists, skipping: {subject_name} / {chapter_name}")

        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    seed_reference_data()
