from rag.embedding import get_embedding

text = "Antibiotic prescriptions require explicit duration"

embedding = get_embedding(text)

print("Embedding generated successfully")
print(f"Dimensions: {len(embedding)}")
print("First 10 values:")
print(embedding[:10])