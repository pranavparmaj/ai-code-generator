import re


CRUD_FEATURE_KEYWORDS = {
    "search": ["search"],
    "filters": ["filter", "filters"],
    "dashboard": ["dashboard", "metrics", "analytics"],
    "auth": ["login", "sign in", "authenticate", "role-based access", "role based access"],
    "create": ["create", "new"],
    "edit": ["edit", "update"],
    "delete": ["delete", "remove"],
    "detail": ["detail", "view"],
}

WORKFLOW_FEATURE_KEYWORDS = {
    "redirects": ["redirect", "followed by", "and then", "then", "next"],
    "auth": ["login", "sign in", "register", "registration"],
    "dashboard": ["dashboard"],
    "profile": ["profile"],
    "notifications": ["notify", "notification", "email alert"],
}

SEARCH_CANDIDATES = {"name", "title", "email", "username", "department", "role", "company", "category", "assignee", "owner"}
FILTER_CANDIDATES = {"status", "department", "role", "category", "priority", "assignee", "owner"}
STATUS_LIKE_VALUES = {"status", "state"}


def _has_keyword(source, keywords):
    lowered = (source or "").lower()
    return any(keyword in lowered for keyword in keywords)


def infer_features(prompt, notes, app_family, module):
    source = f"{prompt or ''} {notes or ''}".lower()
    feature_map = WORKFLOW_FEATURE_KEYWORDS if app_family == "workflow" else CRUD_FEATURE_KEYWORDS
    features = [name for name, keywords in feature_map.items() if _has_keyword(source, keywords)]

    if app_family == "crud":
        features.extend([name for name in ("create", "edit", "delete", "detail") if name not in features])
        if module != "crud" and "dashboard" not in features:
            features.append("dashboard")

    if app_family == "workflow" and "redirects" not in features:
        features.append("redirects")

    unique = []
    for feature in features:
        if feature not in unique:
            unique.append(feature)
    return unique


def infer_routes(context):
    app_family = context.get("app_family")
    module = context.get("module")
    routes = ["/"]

    if app_family == "workflow":
        for step in context.get("module_plan", []):
            routes.append(f"/{step['module']}")
        if "/dashboard" not in routes:
            routes.append("/dashboard")
        return routes

    if app_family == "crud":
        plural = f"/{context['resource_plural']}"
        routes.extend([
            "/login",
            "/logout",
            plural,
            f"{plural}/new",
            f"{plural}/<item_id>",
            f"{plural}/<item_id>/edit",
            f"{plural}/<item_id>/delete",
            "/dashboard",
        ])
        return routes

    routes.append(f"/{module}")
    if module != "dashboard":
        routes.append(f"/{module}/success")
        routes.append("/dashboard")
    return routes


def infer_forms(context):
    app_family = context.get("app_family")
    forms = []

    if app_family == "workflow":
        for step in context.get("module_plan", []):
            if step["module"] == "dashboard":
                continue
            forms.append({
                "route": f"/{step['module']}",
                "fields": list(step.get("fields", [])),
                "submit_method": "POST",
            })
        return forms

    if app_family == "crud":
        forms.append({
            "route": f"/{context['resource_plural']}/new",
            "fields": list(context.get("fields", [])),
            "submit_method": "POST",
        })
        forms.append({
            "route": "/login",
            "fields": ["username", "password"],
            "submit_method": "POST",
        })
        return forms

    forms.append({
        "route": f"/{context['module']}",
        "fields": list(context.get("fields", [])),
        "submit_method": "POST",
    })
    return forms


def infer_test_plan(context):
    app_family = context.get("app_family")
    plan = {
        "home_route": "/",
        "public_routes": [],
        "protected_routes": [],
        "auth_route": None,
    }

    if app_family == "workflow":
        plan["public_routes"] = [
            f"/{step['module']}"
            for step in context.get("module_plan", [])
            if step["module"] in {"registration", "login"}
        ]
        if any(step["module"] == "dashboard" for step in context.get("module_plan", [])):
            plan["protected_routes"].append("/dashboard")
        plan["auth_route"] = "/login"
        return plan

    if app_family == "crud":
        plan["public_routes"] = ["/login"]
        plan["protected_routes"] = [f"/{context['resource_plural']}", "/dashboard"]
        plan["auth_route"] = "/login"
        return plan

    plan["public_routes"] = [f"/{context['module']}"]
    return plan


def infer_search_fields(fields, features):
    if "search" not in features:
        return []
    ranked = [field for field in fields if field in SEARCH_CANDIDATES]
    if not ranked:
        ranked = [field for field in fields if field not in {"description", "notes", "message"}]
    return ranked[:3]


def infer_filter_fields(fields, features):
    if "filters" not in features:
        return []
    ranked = [field for field in fields if field in FILTER_CANDIDATES]
    if not ranked:
        ranked = [field for field in fields if field in STATUS_LIKE_VALUES]
    if not ranked and fields:
        ranked = [fields[0]]
    unique = []
    for field in ranked[:2]:
        if field not in unique:
            unique.append(field)
    return unique


def infer_dashboard_metrics(fields, features):
    metrics = [{"key": "total_items", "label": "Total records"}]
    if "dashboard" not in features:
        return metrics
    if any(field in fields for field in STATUS_LIKE_VALUES):
        metrics.append({"key": "active_items", "label": "Active items"})
        metrics.append({"key": "draft_items", "label": "Draft items"})
    if "department" in fields:
        metrics.append({"key": "department_count", "label": "Departments"})
    elif "category" in fields:
        metrics.append({"key": "category_count", "label": "Categories"})
    elif "priority" in fields:
        metrics.append({"key": "priority_count", "label": "Priority levels"})
    return metrics[:4]


def build_app_spec(context):
    app_family = context.get("app_family")
    spec = {
        "app_family": app_family,
        "module": context.get("module"),
        "project_name": context.get("project_name"),
        "resource_name": context.get("resource_name"),
        "resource_plural": context.get("resource_plural"),
        "fields": list(context.get("fields", [])),
        "features": infer_features(
            context.get("description") or "",
            context.get("notes") or "",
            context.get("app_family"),
            context.get("module"),
        ),
        "routes": infer_routes(context),
        "forms": infer_forms(context),
        "tests": infer_test_plan(context),
    }

    if app_family == "workflow":
        spec["module_routes"] = [route for route in spec["routes"] if route != "/"]
        spec["workflow"] = {
            "steps": [step["module"] for step in context.get("module_plan", [])],
            "edges": list(context.get("workflow_edges", [])),
        }
    elif app_family == "crud":
        plural = f"/{context['resource_plural']}"
        spec["search_fields"] = infer_search_fields(spec["fields"], spec["features"])
        spec["filter_fields"] = infer_filter_fields(spec["fields"], spec["features"])
        spec["dashboard_metrics"] = infer_dashboard_metrics(spec["fields"], spec["features"])
        spec["module_routes"] = [
            plural,
            f"{plural}/new",
            f"{plural}/<item_id>",
            f"{plural}/<item_id>/edit",
            f"{plural}/<item_id>/delete",
            "/dashboard",
        ]
    else:
        spec["module_routes"] = [route for route in spec["routes"] if route != "/"]

    return spec
