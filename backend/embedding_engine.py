import hashlib
import math


MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIMENSION = 32
model = None
model_load_attempted = False


def get_model():
    global model, model_load_attempted
    if model_load_attempted:
        return model

    model_load_attempted = True
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME, local_files_only=True)
    except Exception:
        model = None
    return model


def generate_embedding(text):
    loaded_model = get_model()
    if loaded_model is not None:
        return loaded_model.encode(text)

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
