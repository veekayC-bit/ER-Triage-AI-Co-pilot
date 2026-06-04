

from pathlib import Path
from typing import List, Dict


SUPPORTED_EXTENSIONS = {".md"}


def load_documents(knowledge_base_path: str) -> List[Dict]:
    """
    Load all markdown documents from the knowledge base.

    Returns:
    [
        {
            "text": "...",
            "source": "antibiotic_guidelines.md",
            "category": "prescriptions"
        }
    ]
    """

    documents = []

    root = Path(knowledge_base_path)

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        documents.append(
            {
                "text": content,
                "source": file_path.name,
                "category": file_path.parent.name,
            }
        )

    return documents


if __name__ == "__main__":
    docs = load_documents("knowledge_base")

    print(f"Loaded {len(docs)} documents")

    for doc in docs:
        print(f"- {doc['source']} ({doc['category']})")