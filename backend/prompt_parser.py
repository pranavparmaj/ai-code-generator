import re
from datetime import datetime

from app_spec import build_app_spec


MODULE_ALIASES = {
    "crud": "crud",
    "create read update delete": "crud",
    "management system": "crud",
    "inventory": "inventory_management",
    "inventory management": "inventory_management",
    "employee management": "employee_management",
    "employee manager": "employee_management",
    "customer management": "customer_management",
    "customer portal": "customer_management",
    "ticket system": "ticket_system",
    "ticket tracker": "ticket_system",
    "support ticket": "ticket_system",
    "task manager": "task_manager",
    "task management": "task_manager",
    "product catalog": "product_catalog",
    "product management": "product_catalog",
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
    "crud": ["name", "status", "description"],
    "inventory_management": ["name", "sku", "status", "quantity", "description"],
    "employee_management": ["name", "department", "role", "status", "email"],
    "customer_management": ["name", "company", "status", "email", "phone"],
    "ticket_system": ["title", "priority", "status", "assignee", "description"],
    "task_manager": ["title", "status", "owner", "due_date", "description"],
    "product_catalog": ["name", "status", "price", "category", "description"],
    "login": ["username", "password"],
    "registration": ["first_name", "last_name", "email", "password", "confirm_password"],
    "dashboard": [],
    "profile": ["full_name", "email", "phone", "address"],
    "contact": ["name", "email", "subject", "message"],
    "feedback": ["name", "email", "rating", "message"],
}

RESOURCE_HINTS = [
    "product", "products", "customer", "customers", "employee", "employees",
    "ticket", "tickets", "task", "tasks", "order", "orders", "invoice", "invoices",
    "student", "students", "asset", "assets", "project", "projects", "inventory",
]

CRUD_FAMILY_MODULES = {
    "crud": "record",
    "inventory_management": "item",
    "employee_management": "employee",
    "customer_management": "customer",
    "ticket_system": "ticket",
    "task_manager": "task",
    "product_catalog": "product",
}

WORKFLOW_MODULES = {"registration", "login", "dashboard", "profile", "contact", "feedback"}
WORKFLOW_CONNECTOR_PATTERN = re.compile(r"\b(?:followed by|and then|then|after that|next|plus)\b", re.IGNORECASE)
FIELD_SECTION_END_PATTERN = re.compile(
    r"(?=\b(?:include|add|followed by|and then|then|after that|next|plus)\b|[.?!]|$)",
    re.IGNORECASE,
)

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
    value = (value or "").strip().lower()
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_")
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
    if any(keyword in prompt for keyword in ["crud", "create read update delete"]):
        return "crud"
    crud_signals = ["list", "create", "edit", "update", "delete"]
    if sum(1 for signal in crud_signals if re.search(rf"\b{signal}\b", prompt)) >= 3:
        return "crud"

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
    match = re.search(r"\bwith\s+(.+?)" + FIELD_SECTION_END_PATTERN.pattern, prompt, flags=re.IGNORECASE)
    if not match:
        return []

    field_text = match.group(1)
    field_text = re.sub(r"\bfields?\b", "", field_text)
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


def extract_resource_name(prompt, module, option_project_name=""):
    prompt_lower = normalize_prompt(prompt).lower()
    singular_map = {
        "products": "product",
        "customers": "customer",
        "employees": "employee",
        "tickets": "ticket",
        "tasks": "task",
        "orders": "order",
        "invoices": "invoice",
        "students": "student",
        "assets": "asset",
        "projects": "project",
    }
    for resource in RESOURCE_HINTS:
        if re.search(rf"\b{re.escape(resource)}\b", prompt_lower):
            return singular_map.get(resource, resource.rstrip("s"))

    if module in CRUD_FAMILY_MODULES:
        project_bits = slugify(option_project_name or "").split("_")
        for bit in project_bits:
            if bit and bit not in {"flask", "crud", "app", "system", "manager"}:
                return singular_map.get(bit, bit.rstrip("s"))
        return CRUD_FAMILY_MODULES.get(module, "record")

    return module


def extract_workflows(prompt, notes=""):
    source = f"{normalize_prompt(prompt)} {notes}".lower()
    workflows = []
    for workflow, keywords in WORKFLOW_KEYWORDS.items():
        if any(keyword in source for keyword in keywords):
            workflows.append(workflow)
    return workflows


def detect_intent(module, workflows, constraints):
    if module in CRUD_FAMILY_MODULES:
        return "resource_management"
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


def detect_modules_in_order(prompt):
    prompt_text = normalize_prompt(prompt)
    matches = []
    for alias, module in MODULE_ALIASES.items():
        for match in re.finditer(rf"\b{re.escape(alias)}\b", prompt_text, flags=re.IGNORECASE):
            matches.append((match.start(), module))
    matches.sort(key=lambda item: item[0])

    ordered = []
    for _, module in matches:
        if module not in ordered:
            ordered.append(module)
    return ordered


def split_workflow_segments(prompt):
    parts = [segment.strip(" ,.;") for segment in WORKFLOW_CONNECTOR_PATTERN.split(normalize_prompt(prompt)) if segment.strip(" ,.;")]
    return parts


def build_workflow_plan(prompt, options):
    ordered_modules = [module for module in detect_modules_in_order(prompt) if module in WORKFLOW_MODULES]
    connectors_present = bool(WORKFLOW_CONNECTOR_PATTERN.search(normalize_prompt(prompt)))
    if len(ordered_modules) < 2 or not connectors_present:
        return None

    segments = split_workflow_segments(prompt)
    plan = []
    seen_modules = set()
    for segment in segments:
        segment_module = detect_module(segment, None)
        if segment_module not in WORKFLOW_MODULES or segment_module in seen_modules:
            continue
        segment_fields = extract_fields(segment) or DEFAULT_FIELDS.get(segment_module, [])
        plan.append({
            "module": segment_module,
            "fields": segment_fields,
            "title": f"{segment_module.replace('_', ' ').title()} Step",
            "description": sentence_case(segment),
        })
        seen_modules.add(segment_module)

    if len(plan) < 2:
        return None

    workflow_edges = []
    for current_step, next_step in zip(plan, plan[1:]):
        workflow_edges.append({"from": current_step["module"], "to": next_step["module"]})

    return {"module_plan": plan, "workflow_edges": workflow_edges}


def build_project_name(module, options):
    project_name = slugify(options.get("project_name", ""))
    if project_name != "generated_project":
        return project_name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{options.get('framework', 'flask')}_{module}_{timestamp}"


def detect_app_family(module):
    if module in CRUD_FAMILY_MODULES:
        return "crud"
    return "standard"


def parse_prompt(prompt, options=None):
    options = options or {}

    workflow_plan = build_workflow_plan(prompt, options)
    module = detect_module(prompt, options.get("module"))
    framework = detect_framework(prompt, options.get("framework"))
    language = detect_language(prompt, framework, options.get("language"))

    explicit_fields = parse_field_list((options.get("fields") or "").split(","))
    prompt_fields = extract_fields(prompt)
    if workflow_plan:
        primary_step = workflow_plan["module_plan"][0]
        fields = primary_step["fields"]
        module = primary_step["module"]
    else:
        fields = explicit_fields or prompt_fields or DEFAULT_FIELDS.get(module, [])
    roles = extract_roles(prompt)
    constraints = extract_constraints(prompt, options.get("notes", ""))
    workflows = extract_workflows(prompt, options.get("notes", ""))
    intent = detect_intent(module, workflows, constraints)
    entities = extract_entities(prompt, fields)
    resource_name = extract_resource_name(prompt, module, options.get("project_name", ""))

    project_name = build_project_name(module, {"project_name": options.get("project_name"), "framework": framework})

    result = {
        "module": module,
        "app_family": "workflow" if workflow_plan else detect_app_family(module),
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
        "resource_name": resource_name,
        "resource_plural": f"{resource_name}s" if not resource_name.endswith("s") else resource_name,
    }

    if workflow_plan:
        result["module_plan"] = workflow_plan["module_plan"]
        result["workflow_edges"] = workflow_plan["workflow_edges"]
        result["workflow_modules"] = [step["module"] for step in workflow_plan["module_plan"]]
        result["title"] = options.get("title") or "Workflow Workspace"
        result["prompt_summary"] = (
            f"Workflow: {' -> '.join(step['module'] for step in workflow_plan['module_plan'])} | "
            f"Roles: {', '.join(roles) if roles else 'none'} | "
            f"Fields: {', '.join(fields) if fields else 'none'}"
        )

    result["app_spec"] = build_app_spec(result)
    return result
