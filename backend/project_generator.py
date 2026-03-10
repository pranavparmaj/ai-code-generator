import os


BASE_DIR = os.path.abspath("../generated_projects")


def create_project_structure(module):

    project_name = f"flask_{module}_system"

    project_path = os.path.join(BASE_DIR, project_name)

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, "templates"), exist_ok=True)
    os.makedirs(os.path.join(project_path, "routes"), exist_ok=True)

    return project_path


def write_files(project_path, module, html_code, backend_code):

    # HTML template
    html_path = os.path.join(project_path, "templates", f"{module}.html")

    with open(html_path, "w") as f:
        f.write(html_code)

    # backend route
    route_path = os.path.join(project_path, "routes", f"{module}.py")

    with open(route_path, "w") as f:
        f.write(backend_code)

    # main flask app
    app_code = f"""
from flask import Flask, render_template
from routes.{module} import *

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("{module}.html")

if __name__ == "__main__":
    app.run(debug=True)
"""

    app_path = os.path.join(project_path, "app.py")

    with open(app_path, "w") as f:
        f.write(app_code)

    # requirements file
    requirements_path = os.path.join(project_path, "requirements.txt")

    with open(requirements_path, "w") as f:
        f.write("flask\n")

    return project_path


def generate_project(module, html_code, backend_code):

    project_path = create_project_structure(module)

    write_files(project_path, module, html_code, backend_code)

    return project_path