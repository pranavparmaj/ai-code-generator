import re

MODULE_TYPES = ["login", "registration", "signup", "dashboard"]

FRAMEWORKS = {
    "flask": "python",
    "django": "python",
    "node": "javascript",
    "express": "javascript",
    "php": "php"
}

LANGUAGES = ["python", "javascript", "php"]


def detect_module(prompt):

    prompt = prompt.lower()

    for module in MODULE_TYPES:
        if module in prompt:
            return module

    return "unknown"


def detect_framework(prompt):

    prompt = prompt.lower()

    for framework in FRAMEWORKS:
        if framework in prompt:
            return framework

    return None


def detect_language(prompt, framework):

    prompt = prompt.lower()

    # language directly mentioned
    for lang in LANGUAGES:
        if lang in prompt:
            return lang

    # fallback from framework
    if framework:
        return FRAMEWORKS.get(framework)

    return "python"


def extract_fields(prompt):

    prompt = prompt.lower()

    # remove phrases
    prompt = prompt.replace("fields as", "")
    prompt = prompt.replace("fields", "")

    match = re.search(r"with (.*)", prompt)

    if not match:
        return []

    field_text = match.group(1)

    # replace connectors
    field_text = field_text.replace("and", ",")
    field_text = field_text.replace("  ", " ")

    raw_fields = field_text.split(",")

    fields = []

    for f in raw_fields:

        f = f.strip()

        # split accidental combinations
        parts = f.split()

        if len(parts) > 1 and parts[0] != "phone":
            fields.extend(parts)
        else:
            fields.append(f)

    return fields


def parse_prompt(prompt):

    module = detect_module(prompt)

    framework = detect_framework(prompt)

    language = detect_language(prompt, framework)

    fields = extract_fields(prompt)

    result = {
        "module": module,
        "framework": framework if framework else "custom",
        "language": language,
        "fields": fields
    }

    return result