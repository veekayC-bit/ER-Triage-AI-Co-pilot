

from rag.embedding import get_embedding
from rag.similarity import cosine_similarity


class SemanticRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.chunk_embeddings = []

        print("Generating embeddings for chunks...")

        for chunk in chunks:
            embedding = get_embedding(chunk["text"])

            self.chunk_embeddings.append(
                {
                    "chunk": chunk,
                    "embedding": embedding,
                }
            )

    def search(self, query, top_k=3):
        query_embedding = get_embedding(query)

        results = []

        for item in self.chunk_embeddings:
            similarity = cosine_similarity(
                query_embedding,
                item["embedding"],
            )

            results.append(
                (
                    item["chunk"],
                    similarity,
                )
            )

        results.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        return results[:top_k]