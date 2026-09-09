"""Curriculum PDF ingestion and local FAISS retrieval for Section 10.3."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

import faiss
import numpy as np
from pypdf import PdfReader
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.curriculum import Chapter, CurriculumDocument, SourceReference, Subject, Topic

CHUNK_TOKEN_COUNT = 512
CHUNK_OVERLAP_TOKENS = 100
# A subsection heading like "13.2 Mean of Grouped Data" or "12.6.2 Resistors in Parallel": number
# (2 or 3 levels), single space, then a title starting with a capital letter (no digits), which
# rules out numeric tables/ranges.
TOPIC_PATTERN = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){1,2})\s+([A-Z][A-Za-z ,'&-]{2,100})$")
# Some PDFs render a heading by drawing it several times on top of itself (a kerning/bolding
# artifact), which extraction turns into the same text repeated back-to-back on one line, e.g.
# "12.1 ELECTRIC CURRENT12.1 ELECTRIC CURRENT12.1 ELECTRIC CURRENT". Collapsing this back to a
# single occurrence lets it match TOPIC_PATTERN/CHAPTER_HEADER_PATTERN normally.
_REPEATED_LINE_PATTERN = re.compile(r"^(.{4,150}?)\1{1,9}$")
# Explicit "Chapter <title>" markers, e.g. injected from PDF bookmarks. The title must look like
# a title (starts with a capital letter, no digits/periods) to avoid matching body sentences that
# happen to contain the word "chapter" mid-sentence after line-wrapping.
NAMED_CHAPTER_PATTERN = re.compile(r"^(?i:chapter)\s+([A-Z][A-Za-z ,'&-]{2,150})$")
# A chapter title-page marker where extraction glues the title, chapter number, and the word
# "CHAPTER" onto one line with no separating whitespace, e.g. "Electricity12 CHAPTER". Rare and
# specific enough to trust on a single occurrence.
TITLE_PAGE_CHAPTER_PATTERN = re.compile(r"^(.{3,100}?)(\d{1,2})\s*chapter$", re.IGNORECASE)
# A running-header/footer style chapter title: ALL CAPS words, optionally followed by a page
# number (e.g. "REAL NUMBERS 1", "STATISTICS 171"). Loose on its own, so it is only trusted once
# it recurs across several pages (see _detect_chapter_titles) rather than a single occurrence, and
# generic recurring labels (subject name, "Questions", etc.) are denylisted below.
CHAPTER_HEADER_PATTERN = re.compile(r"^([A-Z][A-Z '&-]{2,78}[A-Z])(?:\s+\d{1,4})?$")
MIN_CHAPTER_HEADER_OCCURRENCES = 3
# Recurring running-header text that is never a chapter title: the subject name itself (printed on
# alternating pages), and generic section labels (exercises, summaries, notes).
CHAPTER_HEADER_DENYLIST = {
    "PHYSICS", "MATHEMATICS", "SCIENCE",
    "QUESTIONS", "QUESTION", "EXERCISES", "EXERCISE", "SUMMARY", "NOTE", "NOTES", "CONTENTS",
    "ACTIVITY", "ACTIVITIES",
}
# Known chapter titles that PDF text extraction mangles via inconsistent letter-spacing (kerning),
# keyed by the heading collapsed to its bare uppercase letters for lookup.
CHAPTER_TITLE_ALIASES = {
    "REALNUMBERS": "Real Numbers",
    "QUADRATICEQUATIONS": "Quadratic Equations",
    "STATISTICS": "Statistics",
    "TRIGONOMETRY": "Introduction To Trigonometry",
    "INTRODUCTIONTOTRIGONOMETRY": "Introduction To Trigonometry",
    "ELECTRICITY": "Electricity",
    "REFRACTION": "Light",
    "ELECTRICCURRENT": "Magnetic Effects of Electric Current",
}


def _collapse_letters(text: str) -> str:
    return re.sub(r"[^A-Z]", "", text.upper())


def _collapse_repeated_line(line: str) -> str:
    match = _REPEATED_LINE_PATTERN.fullmatch(line)
    return match.group(1) if match else line


def _canonical_chapter_title(raw_title: str) -> str:
    alias = CHAPTER_TITLE_ALIASES.get(_collapse_letters(raw_title))
    return alias if alias else raw_title.title()


def _extract_chapter_candidate(line: str) -> tuple[str, bool] | None:
    """Return (raw title substring, is_trusted_on_first_sight) if the line looks like a chapter
    marker, or None. Named/title-page markers are trusted immediately; ALL-CAPS running headers
    need to recur across pages (checked by the caller) before being trusted."""
    named_match = NAMED_CHAPTER_PATTERN.fullmatch(line)
    if named_match:
        return named_match.group(1).strip(), True
    title_page_match = TITLE_PAGE_CHAPTER_PATTERN.fullmatch(line)
    if title_page_match:
        return title_page_match.group(1).strip(), True
    header_match = CHAPTER_HEADER_PATTERN.fullmatch(line)
    if header_match:
        title = header_match.group(1).strip()
        if _collapse_letters(title) not in CHAPTER_HEADER_DENYLIST:
            return title, False
    return None


def _detect_chapter_titles(pages: list[str]) -> dict[str, str]:
    """Find recurring ALL-CAPS running headers and named chapter markers, keyed by collapsed letters."""
    occurrences: dict[str, list[str]] = {}
    trusted: dict[str, str] = {}
    for page_text in pages:
        for raw_line in page_text.splitlines():
            line = _collapse_repeated_line(_normalize(raw_line))
            if not line:
                continue
            candidate = _extract_chapter_candidate(line)
            if not candidate:
                continue
            title, is_trusted = candidate
            key = _collapse_letters(title)
            if is_trusted:
                trusted[key] = _canonical_chapter_title(title)
            else:
                occurrences.setdefault(key, []).append(title)
    for key, seen_titles in occurrences.items():
        if key not in trusted and len(seen_titles) >= MIN_CHAPTER_HEADER_OCCURRENCES:
            trusted[key] = _canonical_chapter_title(seen_titles[0])
    return trusted


class EmbeddingModel(Protocol):
    def encode(self, texts: list[str], **kwargs) -> object: ...


@dataclass(frozen=True)
class ExtractedChunk:
    text: str
    page_number: int
    chunk_id: str
    chapter_name: str | None
    topic_name: str | None


@dataclass(frozen=True)
class RetrievalResult:
    source_reference_id: UUID
    document_id: UUID
    text: str
    page_number: int
    score: float
    subject_id: UUID
    chapter_id: UUID | None
    topic_id: UUID | None


def _normalize(text: str) -> str:
    return " ".join(text.split())


def chunk_pages(pages: list[str], chunk_size: int = CHUNK_TOKEN_COUNT, overlap: int = CHUNK_OVERLAP_TOKENS) -> list[ExtractedChunk]:
    """Split extracted page text while retaining the latest confidently detected headings."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chapter_titles = _detect_chapter_titles(pages)
    chunks: list[ExtractedChunk] = []
    current_chapter: str | None = None
    current_topic: str | None = None
    for page_number, page_text in enumerate(pages, start=1):
        lines = page_text.splitlines()
        body: list[str] = []
        for raw_line in lines:
            line = _collapse_repeated_line(_normalize(raw_line))
            if not line:
                continue
            topic_match = TOPIC_PATTERN.fullmatch(line)
            candidate = _extract_chapter_candidate(line)
            chapter_title = chapter_titles.get(_collapse_letters(candidate[0])) if candidate else None
            if topic_match:
                title = topic_match.group(2).strip()
                current_topic = title.title() if title.isupper() else title
            elif chapter_title:
                current_chapter = chapter_title
                current_topic = None
            else:
                body.append(line)

        tokens = _normalize(" ".join(body)).split()
        start = 0
        sequence = 1
        while start < len(tokens):
            chunk_tokens = tokens[start : start + chunk_size]
            chunks.append(ExtractedChunk(
                text=" ".join(chunk_tokens), page_number=page_number,
                chunk_id=f"page-{page_number}-chunk-{sequence}",
                chapter_name=current_chapter, topic_name=current_topic,
            ))
            if start + chunk_size >= len(tokens):
                break
            start += chunk_size - overlap
            sequence += 1
    return chunks


def extract_pdf_pages(pdf_path: Path) -> list[str]:
    reader = PdfReader(str(pdf_path))
    bookmark_titles: dict[int, list[str]] = {}

    def collect_bookmarks(entries: list[object]) -> None:
        for entry in entries:
            if isinstance(entry, list):
                collect_bookmarks(entry)
                continue
            try:
                page_number = reader.get_destination_page_number(entry) + 1
                title = _normalize(str(entry.title))
            except (AttributeError, KeyError, TypeError):
                continue
            if title:
                bookmark_titles.setdefault(page_number, []).append(f"Chapter {title}")

    collect_bookmarks(reader.outline)
    pages = ["\n".join(bookmark_titles.get(page_number, []) + [page.extract_text() or ""]) for page_number, page in enumerate(reader.pages, start=1)]
    if not any(_normalize(page) for page in pages):
        raise ValueError(f"{pdf_path} contains no extractable text; OCR is not supported")
    return pages


def _embedding_model() -> EmbeddingModel:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


class FaissStore:
    def __init__(self, directory: Path, embedding_model: EmbeddingModel | None = None):
        self.directory = directory
        self.index_path = directory / "curriculum.faiss"
        self.metadata_path = directory / "curriculum.metadata.json"
        self.embedding_model = embedding_model or _embedding_model()

    def add(self, chunks: list[ExtractedChunk], references: list[SourceReference], subject_id: UUID, chapter_ids: list[UUID | None], topic_ids: list[UUID | None]) -> None:
        if not chunks:
            return
        vectors = np.asarray(self.embedding_model.encode([chunk.text for chunk in chunks]), dtype="float32")
        if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
            raise ValueError("embedding model returned invalid vector dimensions")
        faiss.normalize_L2(vectors)
        self.directory.mkdir(parents=True, exist_ok=True)
        index = faiss.read_index(str(self.index_path)) if self.index_path.exists() else faiss.IndexFlatIP(vectors.shape[1])
        if index.d != vectors.shape[1]:
            raise ValueError("existing FAISS index uses a different embedding dimension")
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8")) if self.metadata_path.exists() else []
        index.add(vectors)
        metadata.extend({
            "source_reference_id": str(reference.id), "document_id": str(reference.document_id),
            "text": chunk.text, "page_number": chunk.page_number, "subject_id": str(subject_id),
            "chapter_id": str(chapter_id) if chapter_id else None, "topic_id": str(topic_id) if topic_id else None,
        } for chunk, reference, chapter_id, topic_id in zip(chunks, references, chapter_ids, topic_ids, strict=True))
        faiss.write_index(index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    def search(self, query: str, limit: int = 5, subject_id: UUID | None = None, chapter_id: UUID | None = None, topic_id: UUID | None = None) -> list[RetrievalResult]:
        if limit < 1 or not self.index_path.exists() or not self.metadata_path.exists():
            return []
        metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        if not metadata:
            return []
        vector = np.asarray(self.embedding_model.encode([query]), dtype="float32")
        faiss.normalize_L2(vector)
        index = faiss.read_index(str(self.index_path))
        scores, positions = index.search(vector, min(index.ntotal, max(limit * 4, limit)))
        results: list[RetrievalResult] = []
        for score, position in zip(scores[0], positions[0], strict=True):
            if position < 0:
                continue
            item = metadata[position]
            if subject_id and item["subject_id"] != str(subject_id):
                continue
            if chapter_id and item["chapter_id"] != str(chapter_id):
                continue
            if topic_id and item["topic_id"] != str(topic_id):
                continue
            results.append(RetrievalResult(UUID(item["source_reference_id"]), UUID(item["document_id"]), item["text"], item["page_number"], float(score), UUID(item["subject_id"]), UUID(item["chapter_id"]) if item["chapter_id"] else None, UUID(item["topic_id"]) if item["topic_id"] else None))
            if len(results) == limit:
                break
        return results


class CurriculumIngestor:
    def __init__(self, database: Session, vector_directory: Path, embedding_model: EmbeddingModel | None = None):
        self.database = database
        self.store = FaissStore(vector_directory, embedding_model)

    def ingest(self, pdf_path: Path, subject_name: str, pages: list[str] | None = None) -> CurriculumDocument:
        pdf_path = pdf_path.resolve()
        content = pdf_path.read_bytes() if pages is None else "\n".join(pages).encode()
        content_hash = hashlib.sha256(content).hexdigest()
        existing = self.database.query(CurriculumDocument).filter_by(content_hash=content_hash).one_or_none()
        if existing:
            return existing
        if self.database.query(CurriculumDocument).filter_by(source_uri=str(pdf_path)).first():
            raise ValueError("the PDF path already refers to a different document; use a new path")

        subject = self._subject(subject_name)
        chunks = chunk_pages(pages if pages is not None else extract_pdf_pages(pdf_path))
        if not chunks:
            raise ValueError(f"{pdf_path} contains no text to index")
        document = CurriculumDocument(subject_id=subject.id, title=pdf_path.stem, source_uri=str(pdf_path), content_hash=content_hash, document_type="reference")
        self.database.add(document)
        self.database.flush()
        references: list[SourceReference] = []
        chapter_ids: list[UUID | None] = []
        topic_ids: list[UUID | None] = []
        for chunk in chunks:
            chapter = self._chapter(subject, chunk.chapter_name) if chunk.chapter_name else None
            topic = self._topic(chapter, chunk.topic_name) if chapter and chunk.topic_name else None
            reference = SourceReference(document_id=document.id, page_number=chunk.page_number, chunk_id=chunk.chunk_id, excerpt=chunk.text)
            self.database.add(reference)
            references.append(reference)
            chapter_ids.append(chapter.id if chapter else None)
            topic_ids.append(topic.id if topic else None)
        self.database.flush()
        self.store.add(chunks, references, subject.id, chapter_ids, topic_ids)
        self.database.commit()
        return document

    def _subject(self, name: str) -> Subject:
        subject = self.database.query(Subject).filter_by(name=name, class_level=10).one_or_none()
        if not subject:
            subject = Subject(name=name, class_level=10)
            self.database.add(subject)
            self.database.flush()
        return subject

    def _chapter(self, subject: Subject, name: str) -> Chapter:
        chapter = self.database.query(Chapter).filter_by(subject_id=subject.id, name=name).one_or_none()
        if not chapter:
            order = (self.database.query(func.coalesce(func.max(Chapter.display_order), 0)).filter_by(subject_id=subject.id).scalar() or 0) + 1
            chapter = Chapter(subject_id=subject.id, name=name, display_order=order)
            self.database.add(chapter)
            self.database.flush()
        return chapter

    def _topic(self, chapter: Chapter, name: str) -> Topic:
        topic = self.database.query(Topic).filter_by(chapter_id=chapter.id, name=name).one_or_none()
        if not topic:
            order = (self.database.query(func.coalesce(func.max(Topic.display_order), 0)).filter_by(chapter_id=chapter.id).scalar() or 0) + 1
            topic = Topic(chapter_id=chapter.id, name=name, display_order=order)
            self.database.add(topic)
            self.database.flush()
        return topic