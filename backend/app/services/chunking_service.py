def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Split long invoice text into smaller overlapping chunks.

    Example:
    Full invoice text
    → Chunk 0
    → Chunk 1
    → Chunk 2

    The overlap helps avoid losing context when important information
    is split between two chunks.
    """

    if not text:
        return []

    cleaned_text = " ".join(text.split())

    chunks = []
    start = 0
    text_length = len(cleaned_text)

    while start < text_length:
        end = start + chunk_size
        chunk = cleaned_text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - overlap

        if start >= text_length:
            break

    return chunks