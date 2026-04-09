MODULE_TEMPLATE_MAP = {
    "login": "login_form.html",
    "registration": "registration_form.html",
    "dashboard": "dashboard.html",
    "profile": "generic_form.html",
    "contact": "generic_form.html",
    "feedback": "generic_form.html",
}


def select_template(module):
    return MODULE_TEMPLATE_MAP.get(module, "generic_form.html")
