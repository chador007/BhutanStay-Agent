from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 384 dimensions


def get_embedding(text: str) -> list[float]:
    """Generate embedding vector for a text string."""
    embedding = model.encode(text)
    return embedding.tolist()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts."""
    embeddings = model.encode(texts)
    return [e.tolist() for e in embeddings]