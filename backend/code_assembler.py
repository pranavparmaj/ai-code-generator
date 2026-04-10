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
    if context.get("app_family") == "workflow" and context.get("module_plan"):
        reasons.append(
            "Built an ordered workflow plan of "
            + " -> ".join(step["module"] for step in context["module_plan"])
            + " so the exported app can share redirects, auth, and storage."
        )
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


def build_workflow_backend(context, snippets):
    snippet_comment = build_snippet_comment(snippets)
    modules = {step["module"]: step for step in context.get("module_plan", [])}
    next_map = {edge["from"]: edge["to"] for edge in context.get("workflow_edges", [])}
    registration_next = next_map.get("registration", "login")
    login_next = next_map.get("login", "dashboard")
    sections = [
        """from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from services.storage import append_record, build_dashboard_stats, create_user, get_user_by_username, update_user_profile, list_records

bp = Blueprint("workflow", __name__)
""",
        snippet_comment,
        """

def require_login():
    if "user" not in session:
        flash("Sign in to continue.", "error")
        return redirect(url_for("workflow.login"))
    return None
""",
    ]

    if "registration" in modules:
        sections.append(
            """

@bp.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        form_data = {key: request.form.get(key, "").strip() for key in ["username", "password", "first_name", "last_name", "dob"]}
        errors = []
        for key, label in [("username", "Username"), ("password", "Password"), ("first_name", "First name"), ("last_name", "Last name")]:
            if not form_data.get(key):
                errors.append(f"{label} is required.")
        if get_user_by_username(form_data.get("username", "")):
            errors.append("That username already exists.")
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("registration.html", page_title="Registration", description="Create an account to continue to sign in.")
        create_user(form_data)
        flash("Registration completed. Sign in with your new account.", "success")
        return redirect(url_for("workflow.%s"))
    return render_template("registration.html", page_title="Registration", description="Create an account to continue to sign in.")
""" % registration_next
        )

    if "login" in modules:
        sections.append(
            """

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = get_user_by_username(username)
        if user and user.get("password") == password:
            session["user"] = username
            session["role"] = user.get("role", "member")
            flash("Signed in successfully.", "success")
            return redirect(url_for("workflow.%s"))
        flash("Invalid credentials.", "error")
    return render_template("login.html", page_title="Login", description="Sign in to access your generated workflow app.")
""" % login_next
        )

    if "dashboard" in modules:
        sections.append(
            """

@bp.route("/dashboard")
def dashboard():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    stats = build_dashboard_stats()
    recent_entries = list_records()[:5]
    return render_template("dashboard.html", page_title="Workflow Dashboard", description="A shared dashboard across the generated modules.", stats=stats, recent_entries=recent_entries)
"""
        )

    if "profile" in modules:
        sections.append(
            """

@bp.route("/profile", methods=["GET", "POST"])
def profile():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    user = get_user_by_username(session["user"]) or {}
    if request.method == "POST":
        profile_data = {key: request.form.get(key, "").strip() for key in ["full_name", "email", "phone", "address"]}
        update_user_profile(session["user"], profile_data)
        flash("Profile updated.", "success")
        return redirect(url_for("workflow.%s"))
    return render_template("profile.html", page_title="Profile", description="Manage your generated account profile.", form_data=user)
""" % next_map.get("profile", "profile")
        )

    for simple_module in ("contact", "feedback"):
        if simple_module in modules:
            sections.append(
                f"""

@bp.route("/{simple_module}", methods=["GET", "POST"])
def {simple_module}():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    if request.method == "POST":
        form_data = {{key: request.form.get(key, "").strip() for key in {[field["name"] for field in modules[simple_module].get("field_schema", [])]}}}
        append_record("{simple_module}", form_data)
        flash("{simple_module.title()} submitted successfully.", "success")
        return redirect(url_for("workflow.{next_map.get(simple_module, 'dashboard')}"))
    return render_template("{simple_module}.html", page_title="{simple_module.title()}", description="Generated {simple_module} step in the workflow.", form_data={{}})
"""
            )

    sections.append(
        """

@bp.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("workflow.login"))
"""
    )
    return "".join(sections)


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


def build_crud_backend(fields, snippets, context):
    snippet_comment = build_snippet_comment(snippets)
    resource = context["resource_name"]
    plural = context["resource_plural"]
    list_template = f"{resource}_list.html"
    form_template = f"{resource}_form.html"
    detail_template = f"{resource}_detail.html"
    field_names = [field["name"] for field in fields]
    search_fields = [field for field in field_names if field not in {"description", "notes"}][:3] or field_names[:2]
    filter_field = "status" if "status" in field_names else field_names[0]
    create_payload = ",\n            ".join([f'"{field["name"]}": request.form.get("{field["name"]}", "").strip()' for field in fields])
    form_defaults = ", ".join([f'"{field["name"]}": ""' for field in fields])
    return f'''from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from services.storage import (
    build_dashboard_stats,
    create_item,
    delete_item,
    get_item,
    list_items,
    update_item,
)

bp = Blueprint("{context["module"]}", __name__)

{snippet_comment}

RESOURCE = "{resource}"
RESOURCE_LABEL = "{resource.title()}"


def require_login():
    if "user" not in session:
        flash("Sign in to continue.", "error")
        return redirect(url_for("auth.login"))
    return None


def require_admin():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    if session.get("role") != "admin":
        flash("Admin role required for that action.", "error")
        return redirect(url_for("{context["module"]}.list_view"))
    return None


@bp.route("/{plural}")
def list_view():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    query = request.args.get("q", "").strip().lower()
    status = request.args.get("status", "").strip().lower()
    items = list_items(RESOURCE)
    if query:
        items = [item for item in items if any(query in str(item.get(field, "")).lower() for field in {search_fields})]
    if status:
        items = [item for item in items if str(item.get("{filter_field}", "")).lower() == status]
    return render_template(
        "{list_template}",
        page_title="{context["title"]}",
        description="{context["description"]}",
        resource_name=RESOURCE,
        resource_plural="{plural}",
        resource_label=RESOURCE_LABEL,
        items=items,
        query=query,
        status=status,
        role=session.get("role", "member"),
    )


@bp.route("/{plural}/new", methods=["GET", "POST"])
def create_view():
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    form_data = {{{form_defaults}}}
    if request.method == "POST":
        form_data = {{
            {create_payload}
        }}
{build_validation_block(fields)}
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("{form_template}", page_title="Create {resource.title()}", description="{context["description"]}", fields={context["field_schema"]}, form_data=form_data, resource_label=RESOURCE_LABEL, action_url=url_for("{context["module"]}.create_view"), submit_label="Create")
        create_item(RESOURCE, form_data)
        flash(f"{{RESOURCE_LABEL}} created successfully.", "success")
        return redirect(url_for("{context["module"]}.list_view"))
    return render_template("{form_template}", page_title="Create {resource.title()}", description="{context["description"]}", fields={context["field_schema"]}, form_data=form_data, resource_label=RESOURCE_LABEL, action_url=url_for("{context["module"]}.create_view"), submit_label="Create")


@bp.route("/{plural}/<item_id>")
def detail_view(item_id):
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    item = get_item(RESOURCE, item_id)
    if not item:
        flash(f"{{RESOURCE_LABEL}} not found.", "error")
        return redirect(url_for("{context["module"]}.list_view"))
    return render_template("{detail_template}", page_title=f"{{RESOURCE_LABEL}} detail", description="{context["description"]}", resource_label=RESOURCE_LABEL, item=item)


@bp.route("/{plural}/<item_id>/edit", methods=["GET", "POST"])
def edit_view(item_id):
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    item = get_item(RESOURCE, item_id)
    if not item:
        flash(f"{{RESOURCE_LABEL}} not found.", "error")
        return redirect(url_for("{context["module"]}.list_view"))
    form_data = dict(item)
    if request.method == "POST":
        form_data = {{
            {create_payload}
        }}
{build_validation_block(fields)}
        if errors:
            for error in errors:
                flash(error, "error")
            form_data["id"] = item_id
            return render_template("{form_template}", page_title="Edit {resource.title()}", description="{context["description"]}", fields={context["field_schema"]}, form_data=form_data, resource_label=RESOURCE_LABEL, action_url=url_for("{context["module"]}.edit_view", item_id=item_id), submit_label="Save changes")
        update_item(RESOURCE, item_id, form_data)
        flash(f"{{RESOURCE_LABEL}} updated successfully.", "success")
        return redirect(url_for("{context["module"]}.detail_view", item_id=item_id))
    return render_template("{form_template}", page_title="Edit {resource.title()}", description="{context["description"]}", fields={context["field_schema"]}, form_data=form_data, resource_label=RESOURCE_LABEL, action_url=url_for("{context["module"]}.edit_view", item_id=item_id), submit_label="Save changes")


@bp.route("/{plural}/<item_id>/delete", methods=["POST"])
def delete_view(item_id):
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    delete_item(RESOURCE, item_id)
    flash(f"{{RESOURCE_LABEL}} deleted.", "success")
    return redirect(url_for("{context["module"]}.list_view"))


@bp.route("/dashboard")
def dashboard():
    redirect_response = require_login()
    if redirect_response:
        return redirect_response
    stats = build_dashboard_stats(RESOURCE)
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

    if context.get("app_family") == "workflow":
        backend_code = build_workflow_backend(context, snippets)
    elif module == "login":
        backend_code = build_login_backend(context["field_schema"], snippets, context)
    elif context.get("app_family") == "crud":
        backend_code = build_crud_backend(context["field_schema"], snippets, context)
    elif module == "dashboard":
        backend_code = build_dashboard_backend(snippets, context)
    else:
        backend_code = build_form_backend(context["field_schema"], snippets, context)

    assembled_code["backend"] = backend_code
    assembled_code["retrieved_snippets"] = [snippet["name"] for snippet in snippets]
    assembled_code["explanation"] = build_explanation(context, snippets)
    return assembled_code
