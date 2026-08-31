This directory is reserved for curriculum source material, PDFs, and extracted content used by the RAG pipeline.

Place one text-readable PDF per supported subject here, for example `physics.pdf` and `mathematics.pdf`. Do not split files by chapter or create a manual chapter/topic mapping. Section 10.3 ingestion discovers the hierarchy from each PDF, persists the resulting Subjects, Chapters, and Topics, and uses those records to classify source chunks and vectors.

Do not commit material that cannot be redistributed. Scanned or image-only PDFs need OCR and are outside the current `pypdf` ingestion scope.
