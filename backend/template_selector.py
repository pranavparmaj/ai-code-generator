MODULE_TEMPLATE_MAP = {
    "workflow": "workflow_overview.html",
    "crud": "crud_overview.html",
    "inventory_management": "crud_overview.html",
    "employee_management": "crud_overview.html",
    "customer_management": "crud_overview.html",
    "ticket_system": "crud_overview.html",
    "task_manager": "crud_overview.html",
    "product_catalog": "crud_overview.html",
    "login": "login_form.html",
    "registration": "registration_form.html",
    "dashboard": "dashboard.html",
    "profile": "generic_form.html",
    "contact": "generic_form.html",
    "feedback": "generic_form.html",
}


def select_template(module):
    return MODULE_TEMPLATE_MAP.get(module, "generic_form.html")
