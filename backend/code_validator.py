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

    return validation_result