from sentence_transformers import SentenceTransformer


# Load pretrained embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text):

    embedding = model.encode(text)

    return embedding


def generate_embeddings_for_snippets(snippets):

    embedded_snippets = []

    for snippet in snippets:

        description = snippet["description"]

        vector = generate_embedding(description)

        snippet["embedding"] = vector

        embedded_snippets.append(snippet)

    return embedded_snippets