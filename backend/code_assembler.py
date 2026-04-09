def build_validation_block(fields):
    lines = ['        errors = []']
    for field in fields:
        if field["required"]:
            lines.append(
                f'        if not form_data.get("{field["name"]}", "").strip():\n            errors.append("{field["label"]} is required.")'
            )
    return "\n".join(lines)


def build_storage_payload(fields):
    lines = []
    for field in fields:
        default = ".strip()" if field["type"] != "number" else ""
        lines.append(f'"{field["name"]}": request.form.get("{field["name"]}", ""){default}')
    return ",\n        ".join(lines)


def build_snippet_comment(snippets):
    if not snippets:
        return "# No relevant retrieval snippets were found for this module."
    names = ", ".join(snippet["name"] for snippet in snippets)
    return f"# Retrieval context used while assembling this module: {names}"


def build_explanation(context, snippets):
    reasons = [
        f"Selected `{context['module']}` as the target module based on the parsed prompt intent `{context['intent']}`.",
        f"Used `{context['framework']}` with `{len(context['field_schema'])}` inferred field(s): {', '.join(field['name'] for field in context['field_schema']) or 'none'}.",
    ]
    if context.get("roles"):
        reasons.append(f"Detected primary user roles: {', '.join(context['roles'])}.")
    if context.get("workflows"):
        reasons.append(f"Recognized workflow hints: {', '.join(context['workflows'])}.")
    if context.get("constraints"):
        reasons.append(f"Applied prompt constraints: {', '.join(context['constraints'])}.")
    if snippets:
        reasons.append(f"Ranked snippet support by module, framework, and intent; top matches were {', '.join(snippet['name'] for snippet in snippets)}.")
    else:
        reasons.append("No matching snippets were found, so the module was assembled from templates and default route logic.")
    return " ".join(reasons)


def build_login_backend(fields, snippets, context):
    snippet_comment = build_snippet_comment(snippets)
    field_payload = build_storage_payload(fields)
    return f'''from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from services.storage import append_record

bp = Blueprint("{context["module"]}", __name__)

{snippet_comment}

DEMO_USER = "admin"
DEMO_PASSWORD = "admin123"


@bp.route("/{context["module"]}", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        form_data = {{
        {field_payload}
        }}
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        if username == DEMO_USER and password == DEMO_PASSWORD:
            session["user"] = username
            append_record("logins", form_data)
            flash("Signed in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Use admin / admin123 to test the generated login flow.", "error")
    return render_template("{context["module"]}.html", page_title="{context["title"]}", description="{context["description"]}")
'''


def build_dashboard_backend(snippets, context):
    snippet_comment = build_snippet_comment(snippets)
    return f'''from flask import Blueprint, render_template
from services.storage import build_dashboard_stats

bp = Blueprint("{context["module"]}", __name__)

{snippet_comment}


@bp.route("/")
@bp.route("/dashboard")
def dashboard():
    stats = build_dashboard_stats()
    return render_template("dashboard.html", page_title="{context["title"]}", description="{context["description"]}", stats=stats)
'''


def build_form_backend(fields, snippets, context):
    validation_block = build_validation_block(fields)
    field_payload = build_storage_payload(fields)
    snippet_comment = build_snippet_comment(snippets)
    endpoint = context["module"]
    success_message = f'{context["module"].replace("_", " ").title()} submitted successfully.'
    return f'''from flask import Blueprint, flash, redirect, render_template, request, url_for
from services.storage import append_record, build_dashboard_stats

bp = Blueprint("{endpoint}", __name__)

{snippet_comment}


@bp.route("/{endpoint}", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        form_data = {{
        {field_payload}
        }}
{validation_block}
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("{endpoint}.html", page_title="{context["title"]}", description="{context["description"]}", form_data=form_data)
        append_record("{endpoint}", form_data)
        flash("{success_message}", "success")
        return redirect(url_for("{endpoint}.success"))
    return render_template("{endpoint}.html", page_title="{context["title"]}", description="{context["description"]}", form_data={{}})


@bp.route("/{endpoint}/success")
def success():
    stats = build_dashboard_stats()
    return render_template("success.html", page_title="{context["title"]}", description="{context["description"]}", module_name="{endpoint.replace("_", " ").title()}", stats=stats)
'''


def assemble_module(module, html_code, snippets, context):
    assembled_code = {"html": html_code}

    if module == "login":
        backend_code = build_login_backend(context["field_schema"], snippets, context)
    elif module == "dashboard":
        backend_code = build_dashboard_backend(snippets, context)
    else:
        backend_code = build_form_backend(context["field_schema"], snippets, context)

    assembled_code["backend"] = backend_code
    assembled_code["retrieved_snippets"] = [snippet["name"] for snippet in snippets]
    assembled_code["explanation"] = build_explanation(context, snippets)
    return assembled_code
