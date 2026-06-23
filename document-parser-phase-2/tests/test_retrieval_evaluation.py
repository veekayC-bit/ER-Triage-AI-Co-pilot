

from rag.loader import load_documents
from rag.chunker import chunk_documents
from rag.retriever import BM25Retriever


def evaluate_query(retriever, query):
    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    results = retriever.search(query, top_k=3)

    for rank, (chunk, score) in enumerate(results, start=1):
        print(f"\nRank #{rank}")
        print(f"Score: {score:.2f}")
        print(f"Source: {chunk['source']}")
        print(f"Category: {chunk['category']}")
        print("Preview:")
        print(chunk['text'][:200])


if __name__ == "__main__":
    documents = load_documents("knowledge_base")
    chunks = chunk_documents(documents)

    retriever = BM25Retriever(chunks)

    queries = [
        "missing antibiotic duration",
        "manual review needed",
        "specialist information missing",
        "confidence assessment",
        "drug course length",
        "medicine schedule incomplete",
        "doctor referral missing specialty",
    ]

    for query in queries:
        evaluate_query(retriever, query)