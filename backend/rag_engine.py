import json
import os


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