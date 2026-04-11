from flask import Flask, render_template, request, jsonify, send_file
from prompt_parser import parse_prompt
from field_extractor import build_field_schema
from code_generator import generate_module
from rag_engine import retrieve_relevant_snippets
from code_assembler import assemble_module
from code_validator import validate_module
from project_generator import generate_project
from generation_history import append_history, build_analytics, load_history

import logging
import sys
import os

sys.path.append(os.path.abspath(".."))

from utils.zip_exporter import create_zip

LOG_PATH = os.path.abspath("../data/app.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

SAMPLE_PROMPTS = [
    {
        "title": "Product CRUD",
        "prompt": "Create a CRUD app for products with name, status, price and description fields. Add search, filters, dashboard metrics and role-based access.",
        "module": "crud",
    },
    {
        "title": "Employee Management",
        "prompt": "Build an employee management system with name, department, role, status and email fields. Include login, dashboard, search, filters and edit/delete actions.",
        "module": "employee_management",
    },
    {
        "title": "Ticket System",
        "prompt": "Create a support ticket system with title, priority, status, assignee and description fields. Add table view, filters, dashboard and role-based access.",
        "module": "ticket_system",
    },
    {
        "title": "Customer Registration",
        "prompt": "Create a registration module with first name, last name, email, password, company and address fields.",
        "module": "registration",
    },
    {
        "title": "Operations Login",
        "prompt": "Build a login form with username and password for a Flask operations workspace.",
        "module": "login",
    },
    {
        "title": "Contact Desk",
        "prompt": "Create a contact form with name, email, subject and message fields.",
        "module": "contact",
    },
    {
        "title": "Auth Workflow",
        "prompt": "Generate a registration system with username, password, first name, last name and DOB followed by a login system with username and password and then a dashboard.",
        "module": "registration",
    },
]

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)


@app.route("/")
def home():
    return render_template("workspace.html")


@app.route("/samples")
def samples():
    return jsonify({"samples": SAMPLE_PROMPTS})


@app.route("/history")
def history():
    return jsonify({
        "items": load_history(),
        "analytics": build_analytics()
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/download")
def download():
    zip_path = request.args.get("path", "")
    resolved = os.path.abspath(zip_path)
    generated_root = os.path.abspath("../generated_projects")
    if not resolved.startswith(generated_root) or not os.path.exists(resolved):
        return jsonify({"error": "File not found"}), 404
    return send_file(resolved, as_attachment=True)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    prompt = data.get("prompt", "")
    options = data.get("options", {})

    try:
        parsed_prompt = parse_prompt(prompt, options)
        if parsed_prompt.get("app_family") == "workflow":
            field_schema_map = {}
            for step in parsed_prompt["module_plan"]:
                step_schema = build_field_schema(step["fields"])
                step["field_schema"] = step_schema
                field_schema_map[step["module"]] = step_schema
            field_schema = parsed_prompt["module_plan"][0]["field_schema"]
            parsed_prompt["field_schema_map"] = field_schema_map
            parsed_prompt["field_schema"] = field_schema
            parsed_prompt["fields"] = parsed_prompt["module_plan"][0]["fields"]
        else:
            field_schema = build_field_schema(parsed_prompt["fields"])
            parsed_prompt["field_schema"] = field_schema

        module = parsed_prompt["module"]
        generated_html = generate_module(module, field_schema, parsed_prompt)
        snippets = retrieve_relevant_snippets(
            prompt,
            module=module,
            framework=parsed_prompt["framework"],
            intent=parsed_prompt["intent"],
            entities=parsed_prompt["entities"],
            workflows=parsed_prompt["workflows"],
        )
        assembled = assemble_module(module, generated_html, snippets, parsed_prompt)
        validation = validate_module(assembled["html"], assembled["backend"])
        project_path = generate_project(parsed_prompt, assembled["html"], assembled["backend"])
        zip_path = create_zip(project_path)
        download_url = f"/download?path={zip_path}"

        history_entry = append_history({
            "status": "success",
            "project_name": parsed_prompt["project_name"],
            "module": module,
            "framework": parsed_prompt["framework"],
            "prompt": prompt,
            "zip_path": zip_path,
            "download_url": download_url,
            "project_path": project_path,
            "quality_score": validation.get("quality_score", 0),
        })

        response = {
            "module": module,
            "framework": parsed_prompt["framework"],
            "language": parsed_prompt["language"],
            "project_name": parsed_prompt["project_name"],
            "fields": field_schema,
            "generated_html": assembled["html"],
            "preview_html": assembled["html"],
            "backend_code": assembled["backend"],
            "validation": validation,
            "project_path": project_path,
            "download_zip": zip_path,
            "download_url": download_url,
            "explanation": assembled["explanation"],
            "retrieved_snippets": assembled["retrieved_snippets"],
            "steps": [
                "Prompt parsed",
                "Field schema built",
                "Template rendered",
                "Snippet retrieval completed",
                "Backend assembled",
                "Validation completed",
                "Project exported",
            ],
            "history_entry": history_entry,
            "analytics": build_analytics(),
            "prompt_analysis": {
                "intent": parsed_prompt["intent"],
                "roles": parsed_prompt["roles"],
                "entities": parsed_prompt["entities"],
                "constraints": parsed_prompt["constraints"],
                "workflows": parsed_prompt["workflows"],
                "summary": parsed_prompt["prompt_summary"],
            },
        }

        logging.info("Generation succeeded for project=%s module=%s", parsed_prompt["project_name"], module)
        return jsonify(response)
    except Exception as exc:
        logging.exception("Generation failed")
        history_entry = append_history({
            "status": "failed",
            "project_name": options.get("project_name") or "failed_generation",
            "module": options.get("module") or "unknown",
            "framework": options.get("framework") or "flask",
            "prompt": prompt,
            "error": str(exc),
        })
        return jsonify({
            "error": "Generation failed. Review the message and try adjusting the prompt or selected options.",
            "details": str(exc),
            "history_entry": history_entry,
            "analytics": build_analytics(),
        }), 500



if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    print(f"Open the app at: http://{host}:{port}")
    app.run(host=host, port=port, debug=True)
