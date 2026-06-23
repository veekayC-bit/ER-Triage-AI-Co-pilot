from rag.loader import load_documents
from rag.chunker import chunk_documents
from rag.retriever import BM25Retriever


documents = load_documents("knowledge_base")

chunks = chunk_documents(documents)

retriever = BM25Retriever(chunks)

results = retriever.search(
    "pain management"
)

for chunk, score in results:
    print("\n====================")
    print("Score:", score)
    print("Source:", chunk["source"])
    print("Category:", chunk["category"])
    print(chunk["text"][:300])