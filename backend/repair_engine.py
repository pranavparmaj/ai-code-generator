import os


def _read_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _write_file(path, content):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def repair_generated_project(project_path, smoke_result=None):
    smoke_result = smoke_result or {}
    applied_fixes = []
    errors = " ".join(smoke_result.get("project_smoke_errors", []))

    app_path = os.path.join(project_path, "app.py")
    if os.path.isfile(app_path):
        app_code = _read_file(app_path)
        if "TemplateNotFound" in errors and 'template_folder=os.path.join(BASE_DIR, "templates")' not in app_code:
            if "BASE_DIR = os.path.dirname(__file__)" not in app_code:
                app_code = app_code.replace("from flask import Flask, render_template\n", "import os\n\nfrom flask import Flask, render_template\n", 1)
                app_code = app_code.replace("def create_app():\n", 'BASE_DIR = os.path.dirname(__file__)\n\n\ndef create_app():\n', 1)
            app_code = app_code.replace(
                "app = Flask(__name__)",
                'app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))',
            )
            _write_file(app_path, app_code)
            applied_fixes.append("Configured generated Flask app with explicit template/static folders.")

    return {
        "applied_fixes": applied_fixes,
        "repair_attempted": bool(applied_fixes),
    }
