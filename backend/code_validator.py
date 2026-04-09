import ast


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


def run_quality_checks(generated_html, backend_code):
    warnings = []
    quality_score = 100
    imports = collect_imports(backend_code)

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
        "missing_dependencies": infer_missing_dependencies(imports),
        "security_findings": security_findings,
        "lint_warnings": lint_warnings,
    }


def validate_module(generated_html, backend_code):
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

    quality_score, warnings, details = run_quality_checks(generated_html, backend_code)
    validation_result["quality_score"] = quality_score
    validation_result["warnings"] = warnings
    validation_result["route_count"] = backend_code.count("@bp.route")
    validation_result["imports"] = details["imports"]
    validation_result["route_conflicts"] = details["route_conflicts"]
    validation_result["missing_dependencies"] = details["missing_dependencies"]
    validation_result["security_findings"] = details["security_findings"]
    validation_result["lint_warnings"] = details["lint_warnings"]

    return validation_result
