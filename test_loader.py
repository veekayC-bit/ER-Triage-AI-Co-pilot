from rag.loader import load_documents
from rag.chunker import chunk_documents


documents = load_documents("knowledge_base")

print(f"\nLoaded Documents: {len(documents)}")

chunks = chunk_documents(documents)

print(f"Generated Chunks: {len(chunks)}")

print("\nFirst Chunk Metadata:")
print(f"Source: {chunks[0]['source']}")
print(f"Category: {chunks[0]['category']}")
print(f"Chunk ID: {chunks[0]['chunk_id']}")

print("\nFirst Chunk Text:")
print(chunks[0]["text"])