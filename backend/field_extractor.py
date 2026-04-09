TEXTAREA_FIELDS = {"address", "message", "notes", "description"}
NUMBER_FIELDS = {"age", "income", "salary", "rating", "score", "quantity"}
REQUIRED_OPTIONAL_FIELDS = {"company", "website", "bio", "address_line_2"}


def detect_field_type(field):
    field = field.lower()

    if "password" in field:
        return "password"
    if "email" in field or "mail" in field:
        return "email"
    if "phone" in field or "mobile" in field:
        return "tel"
    if "date" in field or "dob" in field:
        return "date"
    if field in NUMBER_FIELDS:
        return "number"
    if field in TEXTAREA_FIELDS:
        return "textarea"
    return "text"


def build_placeholder(label, field_type):
    if field_type == "textarea":
        return f"Enter {label.lower()}"
    if field_type == "password":
        return f"Create {label.lower()}" if "confirm" not in label.lower() else f"Re-enter {label.lower().replace('confirm ', '')}"
    if field_type == "email":
        return "name@example.com"
    if field_type == "tel":
        return "+1 555 010 1234"
    if field_type == "date":
        return ""
    if field_type == "number":
        return "0"
    return f"Enter {label.lower()}"


def humanize(field):
    return field.replace("_", " ").strip().title()


def build_field_schema(fields):
    schema = []

    for field in fields:
        name = field.lower().strip()
        field_type = detect_field_type(name)
        label = humanize(name)
        schema.append(
            {
                "name": name,
                "label": label,
                "type": field_type,
                "required": name not in REQUIRED_OPTIONAL_FIELDS,
                "placeholder": build_placeholder(label, field_type),
                "help_text": f"Provide your {label.lower()}." if field_type != "password" else f"Use a secure {label.lower()}.",
            }
        )

    return schema
