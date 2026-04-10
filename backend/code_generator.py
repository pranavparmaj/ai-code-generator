import os
from jinja2 import Environment, FileSystemLoader
from template_selector import select_template

TEMPLATE_DIR = os.path.abspath("../templates/flask")

env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_module(module, field_schema, generation_context):
    template_key = "workflow" if generation_context.get("app_family") == "workflow" else module
    template_name = select_template(template_key)
    template = env.get_template(template_name)
    rendered = template.render(
        fields=field_schema,
        module=module,
        page_title=generation_context["title"],
        description=generation_context["description"],
        project_name=generation_context["project_name"],
        include_sample_data=generation_context["include_sample_data"],
        resource_name=generation_context.get("resource_name", module),
        resource_plural=generation_context.get("resource_plural", f"{module}s"),
        module_plan=generation_context.get("module_plan", []),
        workflow_edges=generation_context.get("workflow_edges", []),
    )
    return rendered
