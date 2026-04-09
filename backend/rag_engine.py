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


def build_snippet_intent(snippet):
    description = snippet["description"].lower()
    module = snippet["module"].lower()
    if "login" in description or module == "login":
        return "authentication"
    if "register" in description or module == "registration":
        return "onboarding"
    if "dashboard" in description or module == "dashboard":
        return "monitoring"
    return "data_collection"


def score_snippet(snippet, query, module=None, framework=None, intent=None, entities=None, workflows=None):
    query_lower = (query or "").lower()
    entities = entities or []
    workflows = workflows or []
    haystack = " ".join([snippet["name"], snippet["module"], snippet["framework"], snippet["description"]]).lower()

    score = 0
    if framework and snippet["framework"] == framework:
        score += 25
    if module and snippet["module"] == module:
        score += 35
    if module and snippet["module"] == "authentication" and module in {"login", "registration"}:
        score += 18
    if intent and build_snippet_intent(snippet) == intent:
        score += 22

    for entity in entities:
        if entity in haystack:
            score += 6
    for workflow in workflows:
        if workflow in haystack:
            score += 5

    query_terms = [term for term in query_lower.split() if len(term) > 3]
    score += sum(2 for term in query_terms if term in haystack)
    return score

def retrieve_relevant_snippets(query, module=None, framework=None, intent=None, entities=None, workflows=None, top_k=3):
    index = load_faiss_index()
    snippets = get_snippets()
    filtered_snippets = snippets

    if framework:
        framework_matches = [snippet for snippet in filtered_snippets if snippet["framework"] == framework]
        if framework_matches:
            filtered_snippets = framework_matches

    if not index or not snippets:
        ranked = sorted(
            filtered_snippets,
            key=lambda snippet: score_snippet(
                snippet,
                query,
                module=module,
                framework=framework,
                intent=intent,
                entities=entities,
                workflows=workflows,
            ),
            reverse=True
        )
        return ranked[:top_k]

    try:
        query_vector = generate_embedding(query)
        query_vector = np.array([query_vector]).astype("float32")
        distances, indices = index.search(query_vector, min(top_k, len(snippets)))
    except Exception:
        ranked = sorted(
            filtered_snippets,
            key=lambda snippet: score_snippet(
                snippet,
                query,
                module=module,
                framework=framework,
                intent=intent,
                entities=entities,
                workflows=workflows,
            ),
            reverse=True
        )
        return ranked[:top_k]

    vector_candidates = []
    for rank, i in enumerate(indices[0]):
        if i < len(snippets):
            snippet = snippets[i]
            vector_candidates.append((snippet, rank))

    unique_candidates = []
    seen = set()
    for snippet, rank in vector_candidates:
        key = snippet["name"]
        if key not in seen:
            seen.add(key)
            unique_candidates.append((snippet, rank))

    ranked = sorted(
        unique_candidates,
        key=lambda item: (
            score_snippet(
                item[0],
                query,
                module=module,
                framework=framework,
                intent=intent,
                entities=entities,
                workflows=workflows,
            ),
            -item[1]
        ),
        reverse=True
    )
    return [snippet for snippet, _ in ranked[:top_k]]
