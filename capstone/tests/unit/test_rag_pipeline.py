from pathlib import Path
from uuid import uuid4

import numpy as np

from app.rag.pipeline import ExtractedChunk, FaissStore, chunk_pages


class FixedEmbeddingModel:
    def encode(self, texts, **kwargs):
        return np.array([[1.0, 0.0] if "light" in text.lower() else [0.0, 1.0] for text in texts])


def test_chunk_pages_tracks_detected_hierarchy_and_overlap():
    pages = ["Chapter Light\n1.1 Reflection\n" + "light " * 8]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert len(chunks) == 2
    assert chunks[0].chapter_name == "Light"
    assert chunks[0].topic_name == "Reflection"
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]


def test_chunk_pages_accepts_named_chapter_headings_from_bookmarks():
    chunks = chunk_pages(["Chapter Light\n" + "light " * 5], chunk_size=5, overlap=2)

    assert chunks[0].chapter_name == "Light"


def test_chunk_pages_supports_three_level_topic_numbering():
    pages = ["Chapter Electricity\n12.6.2 Resistors in Parallel\n" + "current " * 5]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert chunks[0].chapter_name == "Electricity"
    assert chunks[0].topic_name == "Resistors in Parallel"


def test_chunk_pages_collapses_repeated_heading_artifact():
    heading = "12.1 ELECTRIC CURRENT" * 5
    pages = ["Chapter Electricity\n" + heading + "\n" + "current " * 5]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert chunks[0].topic_name == "Electric Current"


def test_chunk_pages_ignores_body_sentences_that_start_with_the_word_chapter():
    pages = ["chapter (see Section 12.7). A fuse prevents damage.\n" + "current " * 5]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert chunks[0].chapter_name is None


def test_chunk_pages_ignores_numeric_tables_and_exercise_items():
    pages = ["10 - 25 2 17.5 35.0\n1. Collect the marks obtained by students.\n" + "data " * 5]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert chunks[0].chapter_name is None
    assert chunks[0].topic_name is None


def test_chunk_pages_requires_all_caps_running_header_to_recur_across_pages():
    one_off_page = "SOLUTION\n" + "answer " * 5
    recurring_pages = ["STATISTICS 1\n" + "data " * 5] * 3
    chunks = chunk_pages([one_off_page, *recurring_pages], chunk_size=5, overlap=2)

    assert all(c.chapter_name is None for c in chunks if c.page_number == 1)
    assert all(c.chapter_name == "Statistics" for c in chunks if c.page_number != 1)


def test_faiss_store_returns_filtered_relevant_chunks(tmp_path: Path):
    document_id, light_reference, algebra_reference = uuid4(), uuid4(), uuid4()
    physics_id, mathematics_id = uuid4(), uuid4()
    references = [type("Reference", (), {"id": light_reference, "document_id": document_id})(), type("Reference", (), {"id": algebra_reference, "document_id": document_id})()]
    chunks = [
        ExtractedChunk("Light reflects from a mirror.", 1, "page-1-chunk-1", "Light", "Reflection"),
        ExtractedChunk("Algebra uses equations.", 2, "page-2-chunk-1", "Algebra", None),
    ]
    store = FaissStore(tmp_path, FixedEmbeddingModel())
    store.add(chunks, references, physics_id, [None, None], [None, None])
    store.add([chunks[1]], [references[1]], mathematics_id, [None], [None])

    results = store.search("How does light reflect?", subject_id=physics_id)

    assert len(results) == 2
    assert results[0].source_reference_id == light_reference
    assert all(result.subject_id == physics_id for result in results)


def test_faiss_store_supports_five_queries_per_subject(tmp_path: Path):
    document_id = uuid4()
    physics_id, mathematics_id = uuid4(), uuid4()
    physics_reference, mathematics_reference = uuid4(), uuid4()
    physics_chunk = ExtractedChunk("Light reflection from a mirror.", 1, "physics-1", "Light", "Reflection")
    mathematics_chunk = ExtractedChunk("Algebra uses equations.", 1, "mathematics-1", "Algebra", None)
    store = FaissStore(tmp_path, FixedEmbeddingModel())
    store.add([physics_chunk], [type("Reference", (), {"id": physics_reference, "document_id": document_id})()], physics_id, [None], [None])
    store.add([mathematics_chunk], [type("Reference", (), {"id": mathematics_reference, "document_id": document_id})()], mathematics_id, [None], [None])

    for query in ("light", "reflection", "mirror", "light ray", "reflected light"):
        results = store.search(query, subject_id=physics_id)
        assert [result.source_reference_id for result in results] == [physics_reference]
    for query in ("algebra", "equation", "equations", "solve equation", "math algebra"):
        results = store.search(query, subject_id=mathematics_id)
        assert [result.source_reference_id for result in results] == [mathematics_reference]