from pathlib import Path
from uuid import uuid4

import numpy as np

from app.rag.pipeline import ExtractedChunk, FaissStore, chunk_pages


class FixedEmbeddingModel:
    def encode(self, texts, **kwargs):
        return np.array([[1.0, 0.0] if "light" in text.lower() else [0.0, 1.0] for text in texts])


def test_chunk_pages_tracks_detected_hierarchy_and_overlap():
    pages = ["Chapter 1: Light\n1.1: Reflection\n" + "light " * 8]
    chunks = chunk_pages(pages, chunk_size=5, overlap=2)

    assert len(chunks) == 2
    assert chunks[0].chapter_name == "Light"
    assert chunks[0].topic_name == "Reflection"
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]


def test_chunk_pages_accepts_named_chapter_headings_from_bookmarks():
    chunks = chunk_pages(["Chapter Light\n" + "light " * 5], chunk_size=5, overlap=2)

    assert chunks[0].chapter_name == "Light"


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