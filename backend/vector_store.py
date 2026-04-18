import faiss
import numpy as np
import os


INDEX_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vector_db", "snippet_index.faiss"))


def create_faiss_index(embedded_snippets):

    dimension = len(embedded_snippets[0]["embedding"])

    index = faiss.IndexFlatL2(dimension)

    vectors = []

    for snippet in embedded_snippets:
        vectors.append(snippet["embedding"])

    vectors = np.array(vectors).astype("float32")

    index.add(vectors)

    faiss.write_index(index, INDEX_PATH)

    return index


def load_faiss_index():

    if os.path.exists(INDEX_PATH):

        index = faiss.read_index(INDEX_PATH)

        return index

    return None
