

from typing import List, Dict
import uuid


DEFAULT_CHUNK_SIZE = 400
DEFAULT_OVERLAP = 50


def chunk_documents(
    documents: List[Dict],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Dict]:
    """
    Split loaded documents into overlapping chunks.

    Expected document format:
    {
        "text": "...",
        "source": "file.md",
        "category": "prescriptions"
    }
    """

    chunks = []

    for document in documents:
        text = document.get("text", "")
        source = document.get("source", "unknown")
        category = document.get("category", "unknown")

        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_text,
                    "source": source,
                    "category": category,
                }
            )

            start += chunk_size - overlap

    return chunks