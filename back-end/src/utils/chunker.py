from dataclasses import dataclass


@dataclass
class TextChunk:
    text: str
    index: int
    metadata: dict | None = None


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[TextChunk]:
    if not text.strip():
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(TextChunk(text=chunk, index=index))
            index += 1
        if end >= text_len:
            break
        start = end - chunk_overlap

    return chunks
