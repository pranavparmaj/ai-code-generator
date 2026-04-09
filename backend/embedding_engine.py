import hashlib
import math

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIMENSION = 32

try:
    model = SentenceTransformer(MODEL_NAME, local_files_only=True)
except Exception:
    model = None


def generate_embedding(text):
    if model is not None:
        return model.encode(text)

    vector = [0.0] * EMBED_DIMENSION
    for token in (text or "").lower().split():
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % EMBED_DIMENSION
        vector[bucket] += 1.0

    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def generate_embeddings_for_snippets(snippets):
    embedded_snippets = []

    for snippet in snippets:
        description = snippet["description"]
        vector = generate_embedding(description)
        snippet["embedding"] = vector
        embedded_snippets.append(snippet)

    return embedded_snippets
