import json
import os
import numpy as np
from embedding_engine import generate_embedding
from vector_store import load_faiss_index


def load_snippet_metadata():

    metadata_path = os.path.abspath("../data/snippet_metadata.json")

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    return metadata


def load_snippet_code(file_path):

    full_path = os.path.abspath(f"../{file_path}")

    with open(full_path, "r") as f:
        code = f.read()

    return code


def get_snippets():

    metadata = load_snippet_metadata()

    snippets = []

    for item in metadata:

        code = load_snippet_code(item["file"])

        snippets.append({
            "name": item["name"],
            "module": item["module"],
            "framework": item["framework"],
            "description": item["description"],
            "code": code
        })

    return snippets

def retrieve_relevant_snippets(query, top_k=2):

    index = load_faiss_index()

    snippets = get_snippets()

    query_vector = generate_embedding(query)

    query_vector = np.array([query_vector]).astype("float32")

    distances, indices = index.search(query_vector, top_k)

    retrieved = []

    for i in indices[0]:
        retrieved.append(snippets[i])

    return retrieved