from dataclasses import dataclass


DEFAULT_CHUNK_MIN_CHARS = 500
DEFAULT_CHUNK_MAX_CHARS = 900
MAX_CHUNK_OVERLAP_CHARS = 100


@dataclass(frozen=True)
class RetrievalChunkPayload:
    document_id: str
    chunk_id: str
    source_path: str
    schema_version: str
    content: str


def build_document_chunks(
    *,
    document_id: str,
    source_path: str,
    schema_version: str,
    text: str,
) -> tuple[RetrievalChunkPayload, ...]:
    paragraphs = tuple(
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    )
    raw_chunks = _build_paragraph_chunks(paragraphs)

    return tuple(
        RetrievalChunkPayload(
            document_id=document_id,
            chunk_id=f"{document_id}:{index}",
            source_path=source_path,
            schema_version=schema_version,
            content=content,
        )
        for index, content in enumerate(raw_chunks, start=1)
    )


def _build_paragraph_chunks(paragraphs: tuple[str, ...]) -> tuple[str, ...]:
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > DEFAULT_CHUNK_MAX_CHARS:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_paragraph(paragraph))
            continue

        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= DEFAULT_CHUNK_MAX_CHARS:
            current = candidate
            continue

        if current:
            chunks.append(current)
        current = paragraph

    if current:
        chunks.append(current)

    return tuple(chunks)


def _split_long_paragraph(paragraph: str) -> tuple[str, ...]:
    chunks: list[str] = []
    start = 0

    while start < len(paragraph):
        end = min(start + DEFAULT_CHUNK_MAX_CHARS, len(paragraph))
        chunks.append(paragraph[start:end])
        start = end

    return tuple(chunks)
