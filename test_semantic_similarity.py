

from rag.embedding import get_embedding
from rag.similarity import cosine_similarity


pairs = [
    (
        "antibiotic duration",
        "drug course length",
    ),
    (
        "antibiotic duration",
        "referral specialist",
    ),
    (
        "missing specialty information",
        "specialist details absent",
    ),
]


for text_a, text_b in pairs:
    embedding_a = get_embedding(text_a)
    embedding_b = get_embedding(text_b)

    similarity = cosine_similarity(
        embedding_a,
        embedding_b,
    )

    print("\n" + "=" * 80)
    print(f"Text A: {text_a}")
    print(f"Text B: {text_b}")
    print(f"Similarity: {similarity:.4f}")