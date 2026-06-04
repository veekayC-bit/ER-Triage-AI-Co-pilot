from openai import OpenAI
import os

EMBEDDING_MODEL = "text-embedding-3-small"


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    return OpenAI(api_key=api_key)


def get_embedding(text: str):
    """
    Convert text into an embedding vector.
    """

    client = get_client()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )

    return response.data[0].embedding