

from rag.loader import load_documents
from rag.chunker import chunk_documents
from rag.semantic_retriever import SemanticRetriever


documents = load_documents("knowledge_base")
chunks = chunk_documents(documents)

retriever = SemanticRetriever(chunks)

query = "drug course length"

results = retriever.search(query, top_k=3)

print("\n" + "=" * 80)
print(f"QUERY: {query}")
print("=" * 80)

for rank, (chunk, similarity) in enumerate(results, start=1):
    print(f"\nRank #{rank}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Source: {chunk['source']}")
    print(f"Category: {chunk['category']}")
    print("Preview:")
    print(chunk['text'][:250])