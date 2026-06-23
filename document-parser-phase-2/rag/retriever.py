from rank_bm25 import BM25Okapi


class BM25Retriever:
    def __init__(self, chunks):
        self.chunks = chunks

        tokenized_chunks = [
            chunk["text"].lower().split()
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(tokenized_chunks)

    def search(self, query, top_k=3):
        tokenized_query = query.lower().split()

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked[:top_k]