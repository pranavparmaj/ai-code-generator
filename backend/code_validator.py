import ast
import importlib.util
import os
import sys


def validate_python_code(code):
    try:
        ast.parse(code)
        return True, "Valid Python code"
    except SyntaxError as e:
        return False, str(e)


def validate_html_code(html):
    if "<html>" in html and "</html>" in html:
        return True, "Valid HTML structure"
    return False, "Invalid HTML structure"


def collect_imports(code):
    imports = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports


def find_route_conflicts(code):
    conflicts = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return conflicts

    seen_routes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "route":
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        route_value = decorator.args[0].value
                        if route_value in seen_routes:
                            conflicts.append(route_value)
                        seen_routes[route_value] = node.name
    return conflicts


def collect_routes(code):
    routes = set()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return routes

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "route":
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        routes.add(decorator.args[0].value)
    return routes


def detect_security_findings(code):
    findings = []
    insecure_patterns = {
        "debug=True": "Debug mode is enabled in generated application code.",
        "SECRET_KEY = \"": "Hard-coded secret-like value detected.",
        "request.args.get(": "Review query parameter handling for validation and sanitization.",
        "password = request.form.get": "Password handling is plain-text in request processing.",
    }
    for pattern, message in insecure_patterns.items():
        if pattern in code:
            findings.append(message)
    return findings


def infer_missing_dependencies(imports):
    package_map = {
        "flask": "flask",
        "jinja2": "jinja2",
        "numpy": "numpy",
        "faiss": "faiss-cpu",
        "sentence_transformers": "sentence-transformers",
    }
    return sorted({package_map[name] for name in imports if name in package_map})


def run_quality_checks(generated_html, backend_code, app_spec=None):
    warnings = []
    quality_score = 100
    imports = collect_imports(backend_code)
    app_spec = app_spec or {}

    if "from flask import" not in backend_code:
        warnings.append("Missing expected Flask imports.")
        quality_score -= 15

    route_count = backend_code.count("@bp.route")
    if route_count == 0:
        warnings.append("No Flask routes were detected in the generated backend.")
        quality_score -= 20

    if "eval(" in backend_code or "exec(" in backend_code:
        warnings.append("Unsafe dynamic execution detected.")
        quality_score -= 40

    if "services.storage" not in backend_code:
        warnings.append("Generated backend is not using the shared storage service.")
        quality_score -= 10

    if "<form" in generated_html and "method=\"POST\"" not in generated_html:
        warnings.append("Form markup is missing an explicit POST method.")
        quality_score -= 10

    route_conflicts = find_route_conflicts(backend_code)
    if route_conflicts:
        warnings.append(f"Conflicting route declarations detected: {', '.join(route_conflicts)}")
        quality_score -= 20

    declared_routes = collect_routes(backend_code)
    expected_routes = [route for route in app_spec.get("module_routes", app_spec.get("routes", [])) if route != "/" and "<" not in route]
    missing_routes = [route for route in expected_routes if route not in declared_routes]
    if missing_routes:
        warnings.append(f"Expected routes missing from generated backend: {', '.join(missing_routes[:5])}")
        quality_score -= min(20, len(missing_routes) * 5)

    if "flask" not in imports:
        warnings.append("Flask import was not detected during AST inspection.")
        quality_score -= 15

    if "Blueprint(" in backend_code and "@bp.route" not in backend_code:
        warnings.append("Blueprint declared without route handlers.")
        quality_score -= 20

    security_findings = detect_security_findings(backend_code)
    if security_findings:
        warnings.extend(security_findings)
        quality_score -= min(20, len(security_findings) * 5)

    lint_warnings = []
    for index, line in enumerate(backend_code.splitlines(), start=1):
        if len(line) > 100:
            lint_warnings.append(f"Line {index} exceeds 100 characters.")
            if len(lint_warnings) >= 3:
                break

    if lint_warnings:
        warnings.extend(lint_warnings)
        quality_score -= 5

    return max(quality_score, 0), warnings, {
        "imports": sorted(imports),
        "route_conflicts": route_conflicts,
        "declared_routes": sorted(declared_routes),
        "missing_routes": missing_routes,
        "missing_dependencies": infer_missing_dependencies(imports),
        "security_findings": security_findings,
        "lint_warnings": lint_warnings,
    }


def validate_module(generated_html, backend_code, app_spec=None):
    validation_result = {
        "python_valid": False,
        "html_valid": False,
        "errors": []
    }

    py_valid, py_msg = validate_python_code(backend_code)

    html_valid, html_msg = validate_html_code(generated_html)

    validation_result["python_valid"] = py_valid
    validation_result["html_valid"] = html_valid

    if not py_valid:
        validation_result["errors"].append(py_msg)

    if not html_valid:
        validation_result["errors"].append(html_msg)

    quality_score, warnings, details = run_quality_checks(generated_html, backend_code, app_spec=app_spec)
    validation_result["quality_score"] = quality_score
    validation_result["warnings"] = warnings
    validation_result["route_count"] = backend_code.count("@bp.route")
    validation_result["imports"] = details["imports"]
    validation_result["route_conflicts"] = details["route_conflicts"]
    validation_result["declared_routes"] = details["declared_routes"]
    validation_result["missing_routes"] = details["missing_routes"]
    validation_result["missing_dependencies"] = details["missing_dependencies"]
    validation_result["security_findings"] = details["security_findings"]
    validation_result["lint_warnings"] = details["lint_warnings"]

    return validation_result


def run_project_smoke_checks(project_path, app_spec=None):
    app_spec = app_spec or {}
    result = {
        "project_smoke_ok": False,
        "project_smoke_errors": [],
        "checked_routes": [],
    }

    app_path = os.path.join(project_path, "app.py")
    if not os.path.isfile(app_path):
        result["project_smoke_errors"].append("Generated project is missing app.py.")
        return result

    module_dir = os.path.abspath(project_path)
    previous_path = list(sys.path)
    modules_to_restore = {}
    managed_prefixes = ("routes", "services", "config", "app", "generated_project_app")
    for name, module in list(sys.modules.items()):
        if name == "config" or name in {"app", "generated_project_app"} or any(name.startswith(prefix + ".") or name == prefix for prefix in ("routes", "services")):
            modules_to_restore[name] = module
            sys.modules.pop(name, None)
    sys.path.insert(0, module_dir)

    try:
        spec = importlib.util.spec_from_file_location("generated_project_app", app_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        app = getattr(module, "app", None)
        if app is None and hasattr(module, "create_app"):
            app = module.create_app()
        if app is None:
            result["project_smoke_errors"].append("Generated project does not expose app or create_app.")
            return result

        client = app.test_client()
        home = client.get("/")
        result["checked_routes"].append({"route": "/", "status": home.status_code})
        if home.status_code >= 500:
            result["project_smoke_errors"].append("Home route returned a server error.")

        for route in app_spec.get("tests", {}).get("public_routes", []):
            response = client.get(route)
            result["checked_routes"].append({"route": route, "status": response.status_code})
            if response.status_code >= 500:
                result["project_smoke_errors"].append(f"Public route {route} returned a server error.")

        if app_spec.get("tests", {}).get("auth_route") == "/login":
            login = client.post("/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
            result["checked_routes"].append({"route": "POST /login", "status": login.status_code})
            if login.status_code >= 500:
                result["project_smoke_errors"].append("Login flow returned a server error.")

        for route in app_spec.get("tests", {}).get("protected_routes", []):
            response = client.get(route)
            result["checked_routes"].append({"route": route, "status": response.status_code})
            if response.status_code >= 500:
                result["project_smoke_errors"].append(f"Protected route {route} returned a server error.")

        result["project_smoke_ok"] = not result["project_smoke_errors"]
        return result
    except Exception as exc:
        result["project_smoke_errors"].append(str(exc))
        return result
    finally:
        for name in list(sys.modules.keys()):
            if name == "config" or name in {"app", "generated_project_app"} or any(name.startswith(prefix + ".") or name == prefix for prefix in ("routes", "services")):
                sys.modules.pop(name, None)
        sys.modules.update(modules_to_restore)
        sys.path = previous_path


def run_generated_tests(project_path):
    result = {
        "generated_tests_ok": False,
        "generated_test_results": [],
        "generated_test_failures": [],
    }

    test_path = os.path.join(project_path, "tests", "test_app.py")
    if not os.path.isfile(test_path):
        result["generated_test_failures"].append("Generated project is missing tests/test_app.py.")
        return result

    module_dir = os.path.abspath(project_path)
    previous_path = list(sys.path)
    modules_to_restore = {}
    for name, module in list(sys.modules.items()):
        if name == "config" or name in {"app", "generated_project_app", "generated_project_tests"} or any(name.startswith(prefix + ".") or name == prefix for prefix in ("routes", "services", "tests")):
            modules_to_restore[name] = module
            sys.modules.pop(name, None)
    sys.path.insert(0, module_dir)

    try:
        spec = importlib.util.spec_from_file_location("generated_project_tests", test_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        test_functions = [
            (name, getattr(module, name))
            for name in dir(module)
            if name.startswith("test_") and callable(getattr(module, name))
        ]

        for name, fn in test_functions:
            try:
                fn()
                result["generated_test_results"].append({"name": name, "status": "passed"})
            except Exception as exc:
                result["generated_test_results"].append({"name": name, "status": "failed", "error": str(exc)})
                result["generated_test_failures"].append(f"{name}: {exc}")

        result["generated_tests_ok"] = not result["generated_test_failures"]
        return result
    except Exception as exc:
        result["generated_test_failures"].append(str(exc))
        return result
    finally:
        for name in list(sys.modules.keys()):
            if name == "config" or name in {"app", "generated_project_app", "generated_project_tests"} or any(name.startswith(prefix + ".") or name == prefix for prefix in ("routes", "services", "tests")):
                sys.modules.pop(name, None)
        sys.modules.update(modules_to_restore)
        sys.path = previous_path
