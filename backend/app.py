from flask import Flask, render_template, request, jsonify
from prompt_parser import parse_prompt
from field_extractor import build_field_schema
from code_generator import generate_module
from rag_engine import retrieve_relevant_snippets
from code_assembler import assemble_module
from code_validator import validate_module
from project_generator import generate_project

import sys
import os

sys.path.append(os.path.abspath(".."))

from utils.zip_exporter import create_zip


app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.json
    prompt = data.get("prompt")

    # Step 1: Parse prompt
    parsed_prompt = parse_prompt(prompt)

    fields = parsed_prompt["fields"]

    # Step 2: Field intelligence
    field_schema = build_field_schema(fields)

    # Step 3: Generate HTML module
    module = parsed_prompt["module"]

    generated_html = generate_module(module, field_schema)

    # Step 4: Retrieve relevant snippets
    snippets = retrieve_relevant_snippets(prompt)

    # Step 5: Assemble module
    assembled = assemble_module(module, generated_html, snippets)

        # Step 6: Validate code
    validation = validate_module(
        assembled["html"],
        assembled["backend"]
    )

    # Step 7: Generate project files
    project_path = generate_project(
        module,
        assembled["html"],
        assembled["backend"]
    )

    # Step 8: Create downloadable ZIP
    zip_path = create_zip(project_path)

    response = {
        "module": module,
        "framework": parsed_prompt["framework"],
        "language": parsed_prompt["language"],
        "fields": field_schema,
        "generated_html": assembled["html"],
        "backend_code": assembled["backend"],
        "validation": validation,
        "project_path": project_path,
        "download_zip": zip_path
    }

    return jsonify(response)



if __name__ == "__main__":
    app.run(debug=True)