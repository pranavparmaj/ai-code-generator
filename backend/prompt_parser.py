import re
from datetime import datetime


MODULE_ALIASES = {
    "login": "login",
    "sign in": "login",
    "signin": "login",
    "registration": "registration",
    "register": "registration",
    "signup": "registration",
    "sign up": "registration",
    "dashboard": "dashboard",
    "profile": "profile",
    "contact": "contact",
    "feedback": "feedback",
}

FRAMEWORKS = {
    "flask": "python",
}

LANGUAGES = ["python"]

DEFAULT_FIELDS = {
    "login": ["username", "password"],
    "registration": ["first_name", "last_name", "email", "password", "confirm_password"],
    "dashboard": [],
    "profile": ["full_name", "email", "phone", "address"],
    "contact": ["name", "email", "subject", "message"],
    "feedback": ["name", "email", "rating", "message"],
}

ROLE_PATTERNS = [
    "admin",
    "administrator",
    "manager",
    "employee",
    "customer",
    "client",
    "user",
    "operator",
    "support",
    "student",
]

WORKFLOW_KEYWORDS = {
    "redirect": ["redirect", "send to", "take to", "go to"],
    "approve": ["approve", "approval"],
    "notify": ["notify", "notification", "email alert"],
    "review": ["review", "moderation"],
    "search": ["search", "filter"],
    "export": ["export", "download"],
    "login": ["sign in", "login", "authenticate"],
    "register": ["register", "signup", "onboard"],
}

CONSTRAINT_PATTERNS = {
    "required": r"\b(required|must have|mandatory)\b",
    "optional": r"\b(optional|can be empty|not required)\b",
    "secure": r"\b(secure|security|hash|encrypted)\b",
    "validation": r"\b(validate|validation|sanitiz)\b",
    "dashboard_redirect": r"\bredirect\b.*\bdashboard\b",
    "email_notification": r"\b(email|notify)\b",
}


def slugify(value):
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "generated_project"


def normalize_prompt(prompt):
    return (prompt or "").strip()


def detect_module(prompt, option_module=None):
    if option_module and option_module in DEFAULT_FIELDS:
        return option_module

    prompt = normalize_prompt(prompt).lower()
    for alias, module in MODULE_ALIASES.items():
        if alias in prompt:
            return module

    return "registration"


def detect_framework(prompt, option_framework=None):
    if option_framework in FRAMEWORKS:
        return option_framework

    prompt = normalize_prompt(prompt).lower()
    for framework in FRAMEWORKS:
        if framework in prompt:
            return framework

    return "flask"


def detect_language(prompt, framework, option_language=None):
    if option_language in LANGUAGES:
        return option_language

    prompt = normalize_prompt(prompt).lower()
    for lang in LANGUAGES:
        if lang in prompt:
            return lang

    return FRAMEWORKS.get(framework, "python")


def normalize_field_name(name):
    field = re.sub(r"[^a-zA-Z0-9_ ]+", "", name or "").strip().lower().replace(" ", "_")
    return re.sub(r"_+", "_", field).strip("_")


def sentence_case(text):
    text = (text or "").strip()
    return text[:1].upper() + text[1:] if text else ""


def parse_field_list(raw_fields):
    values = []
    for field in raw_fields:
        normalized = normalize_field_name(field)
        if normalized and normalized not in values:
            values.append(normalized)
    return values


def extract_fields(prompt):
    prompt = normalize_prompt(prompt).lower()
    prompt = prompt.replace("fields as", "")
    prompt = prompt.replace("fields", "")

    match = re.search(r"with (.*)", prompt)
    if not match:
        return []

    field_text = match.group(1)
    field_text = field_text.replace(" and ", ",")
    field_text = field_text.replace(";", ",")

    return parse_field_list(field_text.split(","))


def extract_roles(prompt):
    prompt_lower = normalize_prompt(prompt).lower()
    roles = []
    for role in ROLE_PATTERNS:
        if re.search(rf"\b{re.escape(role)}s?\b", prompt_lower):
            normalized = "admin" if role == "administrator" else role
            if normalized not in roles:
                roles.append(normalized)
    return roles


def extract_constraints(prompt, notes=""):
    source = f"{normalize_prompt(prompt)} {notes}".lower()
    constraints = []
    for name, pattern in CONSTRAINT_PATTERNS.items():
        if re.search(pattern, source):
            constraints.append(name)
    return constraints


def extract_entities(prompt, fields):
    prompt_lower = normalize_prompt(prompt).lower()
    known_entities = [
        "user", "account", "profile", "session", "customer", "client",
        "feedback", "message", "dashboard", "registration", "login",
        "contact", "report", "notification"
    ]
    entities = []
    for entity in known_entities:
        if entity in prompt_lower and entity not in entities:
            entities.append(entity)
    for field in fields:
        if field not in entities:
            entities.append(field)
    return entities[:12]


def extract_workflows(prompt, notes=""):
    source = f"{normalize_prompt(prompt)} {notes}".lower()
    workflows = []
    for workflow, keywords in WORKFLOW_KEYWORDS.items():
        if any(keyword in source for keyword in keywords):
            workflows.append(workflow)
    return workflows


def detect_intent(module, workflows, constraints):
    if module == "dashboard":
        return "monitoring"
    if module == "login":
        return "authentication"
    if module == "registration":
        return "onboarding"
    if "notify" in workflows or "email_notification" in constraints:
        return "notification"
    if module in {"contact", "feedback"}:
        return "submission"
    return "data_collection"


def build_summary(module, roles, workflows, constraints, fields):
    parts = [f"Module: {module}"]
    if roles:
        parts.append(f"Roles: {', '.join(roles)}")
    if workflows:
        parts.append(f"Workflow: {', '.join(workflows)}")
    if constraints:
        parts.append(f"Constraints: {', '.join(constraints)}")
    parts.append(f"Fields: {', '.join(fields) if fields else 'none'}")
    return " | ".join(parts)


def build_project_name(module, options):
    project_name = slugify(options.get("project_name", ""))
    if project_name != "generated_project":
        return project_name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{options.get('framework', 'flask')}_{module}_{timestamp}"


def parse_prompt(prompt, options=None):
    options = options or {}

    module = detect_module(prompt, options.get("module"))
    framework = detect_framework(prompt, options.get("framework"))
    language = detect_language(prompt, framework, options.get("language"))

    explicit_fields = parse_field_list((options.get("fields") or "").split(","))
    prompt_fields = extract_fields(prompt)
    fields = explicit_fields or prompt_fields or DEFAULT_FIELDS.get(module, [])
    roles = extract_roles(prompt)
    constraints = extract_constraints(prompt, options.get("notes", ""))
    workflows = extract_workflows(prompt, options.get("notes", ""))
    intent = detect_intent(module, workflows, constraints)
    entities = extract_entities(prompt, fields)

    project_name = build_project_name(module, {"project_name": options.get("project_name"), "framework": framework})

    result = {
        "module": module,
        "framework": framework,
        "language": language,
        "fields": fields,
        "title": options.get("title") or f"{module.replace('_', ' ').title()} Workspace",
        "project_name": project_name,
        "description": options.get("description") or normalize_prompt(prompt) or f"Generated {module} application",
        "styling": options.get("styling") or "modern",
        "database": options.get("database") or "json",
        "include_tests": bool(options.get("include_tests", True)),
        "include_readme": bool(options.get("include_readme", True)),
        "include_sample_data": bool(options.get("include_sample_data", True)),
        "notes": options.get("notes", ""),
        "roles": roles,
        "constraints": constraints,
        "entities": entities,
        "workflows": workflows,
        "intent": intent,
        "prompt_summary": build_summary(module, roles, workflows, constraints, fields),
        "goal": sentence_case(options.get("description") or normalize_prompt(prompt) or f"Generated {module} application"),
    }

    return result
