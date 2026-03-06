import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.abspath("../templates/flask")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_module(module, field_schema):

    if module == "registration":
        template_name = "registration_form.html"

    elif module == "login":
        template_name = "login_form.html"

    elif module == "dashboard":
        template_name = "dashboard.html"

    else:
        return "Unsupported module"

    template = env.get_template(template_name)

    rendered = template.render(fields=field_schema)

    return rendered